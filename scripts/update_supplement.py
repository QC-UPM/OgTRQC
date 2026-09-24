"""Refresh evidence blocks in the single-file, Overleaf-ready supplement.

Only named GENERATED blocks are replaced. Narrative text remains editable in
main.tex. All plot coordinates, numerical tables, bibliography and provenance
needed to compile the document live inside that one file.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / 'supplementary/main.tex'


def read_csv(relative: str) -> list[dict[str, str]]:
    """Read a repository-relative evidence table without refitting a model."""
    with (ROOT / relative).open(newline='') as handle:
        return list(csv.DictReader(handle))


def latex_table(alignment: str, headers: list[str], rows: list[list[str]]) -> str:
    """Render a booktabs table using already escaped LaTeX cell contents.

    Args:
        alignment: Tabular column specification.
        headers: Column labels.
        rows: Formatted data rows.

    Returns:
        Complete inline LaTeX tabular environment.
    """
    lines = [r'\begin{tabular}{' + alignment + '}', r'\toprule',
             ' & '.join(headers) + r' \\', r'\midrule']
    lines.extend(' & '.join(row) + r' \\' for row in rows)
    lines.extend([r'\bottomrule', r'\end{tabular}'])
    return '\n'.join(lines)


def replace_block(text: str, name: str, content: str) -> str:
    """Replace exactly one named generated block, preserving all other text."""
    pattern = re.compile(r'(% BEGIN GENERATED: ' + re.escape(name) + r'\n).*?(% END GENERATED: ' + re.escape(name) + r')', re.S)
    if len(pattern.findall(text)) != 1:
        raise ValueError(f'Expected exactly one GENERATED block named {name}.')
    return pattern.sub(lambda m: m.group(1) + content.rstrip() + '\n' + m.group(2), text)


def generate(paper: Path | None = None) -> dict:
    """Verify recorded results and embed evidence directly in main.tex.

    Args:
        paper: Optional supplied manuscript PDF, recorded by basename and hash.
            The PDF itself is not required by the resulting LaTeX document.

    Returns:
        Source/evidence snapshot embedded as comments in the document.

    Raises:
        ValueError: If source hashes, artifact hashes, or migration checks fail.
    """
    text = DOCUMENT.read_text()
    archive = ROOT / 'notebooks/reference'
    manifest = json.loads((archive / 'manifest.json').read_text())
    for name, record in manifest.items():
        if hashlib.sha256((archive / name).read_bytes()).hexdigest() != record['sha256']:
            raise ValueError(f'Notebook checksum mismatch: {name}')
    for path in (ROOT / 'validation/native').glob('*/manifest.json'):
        for name, digest in json.loads(path.read_text()).items():
            if hashlib.sha256((path.parent / name).read_bytes()).hexdigest() != digest:
                raise ValueError(f'Evidence checksum mismatch: {path.parent / name}')
    migration = json.loads((ROOT / 'validation/migration.json').read_text())
    if not migration['all_passed'] or not all(c['passed'] for c in migration['checks']):
        raise ValueError('Migration verification contains a failed comparison.')
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']
    ident = json.loads((ROOT / 'validation/native/identifiability/metadata.json').read_text())
    uncertainty = json.loads((ROOT / 'validation/native/uncertainty/metadata.json').read_text())
    original = json.loads((ROOT / 'validation/reference/summary.json').read_text())
    labels = {'single': 'Single exponential', 'stretched': 'Stretched exponential',
              'distributed': 'Distributed spectrum', 'biexponential': 'Biexponential'}
    scores = read_csv('validation/native/calibration/scores.csv')
    blocks = {}
    blocks['holdout_table'] = latex_table('lrrrr', ['Model', 'Parameters', 'RMSE', '$R^2$', 'Lag-1 corr.'],
        [[labels[r['model']], r['parameters'], f"{float(r['RMSE']):.8f}",
          f"{float(r['R2']):.8f}", f"{float(r['lag1']):.5f}"] for r in scores])
    profiles = read_csv('validation/native/identifiability/additional_profile_intervals.csv')
    symbols = {'log_tau0': r'$\ell_0$', 'b0': '$b_0$', 'b1': '$b_1$', 'b2': '$b_2$', 'cF': '$c_F$'}
    rows = [[r'$\alpha_A$', f"{ident['alpha_A']:.6f}", *[f'{v:.6f}' for v in ident['alpha_accepted_grid_interval']], 'Original grid']]
    rows.extend([[symbols[r['parameter']], f"{float(r['estimate']):.6f}", f"{float(r['lower']):.6f}",
                  f"{float(r['upper']):.6f}", 'Refined crossing'] for r in profiles])
    blocks['profiles_table'] = latex_table('lrrrl', ['Parameter', 'Estimate', 'Lower', 'Upper', 'Endpoint rule'], rows)
    orders = read_csv('validation/native/refinement/orders.csv')
    continuum = json.loads((ROOT / 'validation/native/continuum/metadata.json').read_text())
    blocks['orders_table'] = latex_table('lrr', ['Benchmark', 'All-grid order', 'Fine-grid order'],
        [['Constant $D$, field benchmark', f"{continuum['observed_order']:.6f}" + r'$^{a}$', '--']]
        + [[r['case'].capitalize(), f"{float(r['all_grid_order']):.6f}", f"{float(r['fine_grid_order']):.6f}"] for r in orders])
    criteria = read_csv('validation/native/review/information_criteria.csv')
    blocks['criteria_table'] = latex_table('lrrrr', ['Model', '$k_{lik}$', 'AIC', 'AICc', 'BIC'],
        [[labels[r['model']], r['likelihood_parameters'], *[f"{float(r[k]):.3f}" for k in ('AIC', 'AICc', 'BIC')]] for r in criteria])
    names = {'holdout_rmse': 'Primary holdout RMSE', 'five_profile_endpoints': 'Five profile endpoints',
             'all_16_retrospective_RMSEs': 'Sixteen retrospective RMSEs', 'constant_D_convergence_order': 'Constant-$D$ order',
             'R3_full_generator_errors': 'R3 relative $L^2$ errors', 'R3_full_generator_gaps': 'R3 spectral gaps',
             'original_alpha_profile_sse': 'Original alpha-profile SSE'}
    rows = [[names[c['name']], f"{c['max_absolute_error']:.3e}", f"{c['atol']:.1e}", f"{c['rtol']:.1e}"]
            for c in migration['checks'] if c['name'] in names]
    blocks['migration_table'] = latex_table('lrrr', ['Quantity', 'Max. abs. difference', 'Abs. tol.', 'Rel. tol.'], rows)
    blocks['notebook_hashes'] = '\n'.join(r'\noindent\textbf{\path{' + name + r'}}\\' + '\n'
        + r'{\small\path{' + record['sha256'] + r'}}\par\medskip' for name, record in manifest.items())

    predictions = read_csv('validation/native/calibration/predictions.csv')
    lines = []
    for kind, style in [('observed', 'only marks,mark=*,mark size=1.0pt,black'),
                        ('single', 'dotted,thick,orange!90!black'), ('stretched', 'dashed,thick,blue!70!black'),
                        ('distributed', 'thick,teal!80!black')]:
        rows = [r for r in predictions if r['model'] == ('distributed' if kind == 'observed' else kind)]
        points = ' '.join(f"({r['time_s']},{r['observed' if kind == 'observed' else 'predicted']})" for r in rows)
        lines.extend([r'\addplot[' + style + '] coordinates {', points, '};',
                      r'\addlegendentry{' + ('Published 533 kV/cm' if kind == 'observed' else labels[kind]) + '}'])
    blocks['holdout_plot'] = '\n'.join(lines)
    refinement = read_csv('validation/native/refinement/full_generator.csv')
    lines = []
    for case, style in [('symmetric', 'blue!70!black,mark=o,thick'), ('ramp', 'orange!90!black,mark=square*,thick')]:
        points = ' '.join(f"({r['N']},{r['relative_L2_error']})" for r in refinement if r['case'] == case)
        lines.extend([r'\addplot[' + style + '] coordinates {' + points + '};',
                      r'\addlegendentry{' + case.capitalize() + ' background}'])
    blocks['refinement_plot'] = '\n'.join(lines)
    profile = read_csv('validation/native/identifiability/original_alpha_profile_31_points.csv')
    points = ' '.join(f"({r['alpha_A']},{r['stat']})" for r in profile)
    blocks['profile_plot'] = (r'\addplot[blue!70!black,mark=*,mark size=1.5pt,thick] coordinates {' + points + '};\n'
                              + r'\addplot[black,dashed,domain=5:8.2] {3.841458820694124};')

    paths = set()
    for pattern in ['octa_gtrqc_sim/proton/**/*.py', 'octa_gtrqc_sim/proton/data/*.json', 'tests/*.py',
                    'scripts/*.py', 'notebooks/reference/*', 'validation/native/**/*', 'validation/reference/**/*.json']:
        paths.update(p for p in ROOT.glob(pattern) if p.is_file())
    paths.update(ROOT / p for p in ['pyproject.toml', 'poetry.lock', 'VARIANTS.md', 'validation/migration.json'])
    source_files = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    git_head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=False)
    old_hash = re.search(r'\\newcommand\{\\PaperHash\}\{([^}]+)\}', text)
    paper_hash = hashlib.sha256(paper.read_bytes()).hexdigest() if paper else (old_hash.group(1) if old_hash else 'Not supplied')
    snapshot = dict(package_version=project['version'], base_git_commit=git_head.stdout.strip() if git_head.returncode == 0 else None,
                    identity='Source/evidence working-tree snapshot; the base commit is not a release identifier for uncommitted changes.',
                    source_files=source_files, supplied_manuscript_sha256=paper_hash)
    snapshot_json = json.dumps(snapshot, indent=2) + '\n'
    digest = hashlib.sha256(snapshot_json.encode()).hexdigest()
    blocks['source_snapshot'] = '\n'.join('% ' + line for line in snapshot_json.splitlines())
    commands = dict(PackageVersion=project['version'], SnapshotHash=digest, PaperHash=paper_hash,
                    MigrationChecks=str(len(migration['checks'])), OriginalAuditPassed=str(original['audit']['passed']),
                    BootstrapCount=str(uncertainty['successful_replicates']), BootstrapCoverage=f"{uncertainty['coverage']:.3f}",
                    BootstrapWidth=f"{uncertainty['mean_width']:.6f}", RecordedPython=ident['environment']['python'],
                    RecordedNumpy=ident['environment']['numpy'], RecordedScipy=ident['environment']['scipy'])
    blocks['metadata'] = '\n'.join(chr(92) + 'newcommand{' + chr(92) + key + '}{' + value + '}' for key, value in commands.items())
    for name, content in blocks.items():
        text = replace_block(text, name, content)
    DOCUMENT.write_text(text)
    return snapshot


def main() -> None:
    """Refresh only the inline evidence blocks in the standalone document."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paper', type=Path)
    args = parser.parse_args()
    snapshot = generate(args.paper)
    print(f"Updated standalone document from {len(snapshot['source_files'])} source/evidence files.")


if __name__ == '__main__':
    main()
