"""Replay hash-verified source notebooks in isolated output directories.

The native models never execute notebook source. This separate, explicit command
retains the complete historical computational record, including the 80-gate
v3.1 audit and synthetic risk ensembles not duplicated by the native core.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


class ReferenceNotebookRunner:
    """Execute only archived notebooks listed in their provenance manifest.

    Args:
        source_directory: Directory containing original notebooks and manifest.
        output_directory: Root for isolated execution directories.
        timeout_s: Per-cell execution timeout in seconds.

    Attributes:
        source_directory: Read-only source archive.
        output_directory: Destination for executed copies and generated files.
        timeout_s: Maximum time per cell.
    """

    def __init__(self, source_directory: str | Path, output_directory: str | Path,
                 timeout_s: int = 3600) -> None:
        """Configure archived-source verification and isolated execution.

        Args:
            source_directory: Folder of original notebooks and manifest.
            output_directory: Destination outside the source archive.
            timeout_s: Maximum execution time per code cell, in seconds.
        """
        self.source_directory = Path(source_directory).resolve()
        self.output_directory = Path(output_directory).resolve()
        self.timeout_s = timeout_s
        if self.output_directory == self.source_directory or self.source_directory in self.output_directory.parents:
            raise ValueError('Execution output must be outside the original notebook archive.')

    def run(self, name: str) -> Path:
        """Verify and execute an archived notebook using the Poetry interpreter.

        Args:
            name: Exact notebook filename appearing in the source manifest.

        Returns:
            Executed notebook path. Original source cells remain unchanged; a
            final export cell is appended only to the executed v3.1 copy.

        Raises:
            ValueError: If the notebook is unknown or its source hash changed.
            ImportError: If the Poetry development dependencies are missing.
            Exception: Notebook execution failures propagate after saving the
                failed executed copy and a failure-status record.
        """
        import nbformat
        from nbclient import NotebookClient
        from jupyter_client import KernelManager
        from jupyter_client.kernelspec import KernelSpec

        manifest = json.loads((self.source_directory / 'manifest.json').read_text())
        if name not in manifest or Path(name).name != name:
            raise ValueError('Notebook must be listed in the archived source manifest.')
        source = self.source_directory / name
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != manifest[name]['sha256']:
            raise ValueError(f'Source hash mismatch: {name}')
        work = self.output_directory / source.stem
        work.mkdir(parents=True, exist_ok=True)
        notebook = nbformat.read(source, as_version=4)
        for cell in notebook.cells:
            if cell.cell_type == 'code':
                cell.outputs = []
                cell.execution_count = None
        if name.startswith('Hx_NdNiO3'):
            notebook.cells.append(nbformat.v4.new_code_cell('''# Added by the reference runner: export completed results only.
from pathlib import Path as _ExportPath
_export_root = _ExportPath.cwd() / "machine_readable"
_export_root.mkdir(exist_ok=True)
(_export_root / "summary.json").write_text(json.dumps(summary, indent=2))
for _name, _value in list(globals().items()):
    if isinstance(_value, pd.DataFrame):
        _value.to_csv(_export_root / (_name + ".csv"), index=False)
'''))
        manager = KernelManager(kernel_name='python3')
        # Explicit kernelspec avoids accidentally using a system Jupyter kernel.
        manager._kernel_spec = KernelSpec(argv=[sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
                                          display_name='Poetry Python', language='python')
        client = NotebookClient(notebook, km=manager, timeout=self.timeout_s,
                                resources={'metadata': {'path': str(work)}},
                                allow_errors=False)
        destination = work / name
        started = time.monotonic()
        status = dict(source_sha256=digest, python_executable=sys.executable, success=False)
        try:
            client.execute(cwd=str(work), cleanup_kc=True)
            status['success'] = True
        finally:
            nbformat.write(notebook, destination)
            status['elapsed_seconds'] = time.monotonic() - started
            (work / 'execution.json').write_text(json.dumps(status, indent=2) + '\n')
        return destination


def main() -> None:
    """Replay one archived notebook or all four using the current Poetry env."""
    parser = argparse.ArgumentParser(description='Reproduce the complete archived notebook record.')
    parser.add_argument('--source', default='notebooks/reference')
    parser.add_argument('--output', default='reference_results')
    parser.add_argument('--notebook', default='all', help='Exact archived filename, or all.')
    parser.add_argument('--timeout', type=int, default=3600, help='Timeout per notebook cell in seconds.')
    args = parser.parse_args()
    runner = ReferenceNotebookRunner(args.source, args.output, args.timeout)
    manifest = json.loads((Path(args.source) / 'manifest.json').read_text())
    names = list(manifest) if args.notebook == 'all' else [args.notebook]
    for name in names:
        print(f'Replaying {name} ...', flush=True)
        print(runner.run(name), flush=True)


if __name__ == '__main__':
    main()
