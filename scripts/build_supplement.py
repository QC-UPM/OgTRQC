"""Compile the standalone Overleaf-ready supplement using pdfLaTeX only."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

from update_supplement import generate, ROOT


def main() -> None:
    """Refresh inline evidence and compile in an otherwise empty directory.

    Three pdfLaTeX passes resolve the bibliography and cross-references. No
    external figures, BibTeX input, shell escape, or repository files are
    available to the TeX compiler. Intermediate files are temporary.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paper', type=Path, help='Optional supplied manuscript PDF to identify by hash.')
    parser.add_argument('--no-refresh', action='store_true', help='Compile the current editable document without refreshing evidence blocks.')
    args = parser.parse_args()
    if shutil.which('pdflatex') is None:
        raise SystemExit('pdfLaTeX is required locally; alternatively upload supplementary/main.tex to Overleaf.')
    if not args.no_refresh:
        generate(args.paper)
    with tempfile.TemporaryDirectory(prefix='proton-supplement-') as name:
        work = Path(name)
        shutil.copyfile(ROOT / 'supplementary/main.tex', work / 'main.tex')
        command = ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', '-file-line-error', '-no-shell-escape', 'main.tex']
        for _ in range(3):
            result = subprocess.run(command, cwd=work, capture_output=True, text=True, check=False)
            if result.returncode:
                log = Path(tempfile.gettempdir()) / 'proton-supplement-build.log'
                log.write_text(result.stdout + result.stderr)
                print(result.stdout[-10000:])
                raise SystemExit(f'Document build failed. Full log: {log}')
        log = (work / 'main.log').read_text(errors='replace')
        if 'There were undefined references' in log or 'There were undefined citations' in log:
            raise SystemExit('Unresolved cross-references in supplementary/main.tex.')
        destination = ROOT / 'supplementary/supplementary_material.pdf'
        shutil.copyfile(work / 'main.pdf', destination)
        # Keep the final log in /tmp for layout inspection, not in the repository.
        (Path(tempfile.gettempdir()) / 'proton-supplement-build.log').write_text(log)
        print(f'Built standalone PDF: {destination}')
        problems = [line for line in log.splitlines() if 'Overfull' in line]
        if problems:
            print('\n'.join(problems))


if __name__ == '__main__':
    main()
