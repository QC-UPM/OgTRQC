"""Refresh evidence blocks in the Overleaf-ready supplement.

Only named GENERATED blocks are replaced. Narrative text remains editable in
supplementary.tex. Tables and profile coordinates are embedded; recorded publication figures
are delivered separately in supplementary/figures/.
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
from evidence import verify_inputs

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / 'supplementary/supplementary.tex'


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


def generate() -> dict:
    """Verify retained numeric inputs and refresh the scientific supplement."""
    text = DOCUMENT.read_text()
    verify_inputs()
    figure_root = ROOT / 'supplementary/figures'
    figure_manifest = json.loads((figure_root / 'manifest.json').read_text())
    for name, digest in figure_manifest['files'].items():
        if hashlib.sha256((figure_root / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Figure checksum mismatch: {name}')
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']
    ident = json.loads((ROOT / 'validation/native/identifiability/metadata.json').read_text())
    uncertainty = json.loads((ROOT / 'validation/native/uncertainty/metadata.json').read_text())
    labels = {'single': 'Single exponential', 'stretched': 'Stretched exponential',
              'distributed': 'Distributed spectrum', 'biexponential': 'Biexponential'}
    scores = [r for r in read_csv('validation/native/review/scores.csv') if float(r['field_kv_cm']) == 533]
    blocks = {}
    blocks['holdout_table'] = latex_table('lrrrr', ['Model', 'Parameters', 'RMSE', '$R^2$', 'Lag-1 corr.'],
        [[labels[r['model']], r['parameters'], f"{float(r['RMSE']):.8f}",
          f"{float(r['R2']):.8f}", f"{float(r['lag1']):.5f}"] for r in scores])
    folds = read_csv('validation/native/review/scores.csv')
    models = ['single', 'stretched', 'distributed', 'biexponential']
    fold_rows = []
    for field in (133, 267, 400, 533):
        fold_rows.append([str(field)] + [f"{float(next(r['RMSE'] for r in folds if float(r['field_kv_cm']) == field and r['model'] == model)):.6f}" for model in models])
    pooled = [(sum(float(r['RMSE'])**2 for r in folds if r['model'] == model) / 4)**0.5 for model in models]
    fold_rows.append(['Pooled'] + [f'{v:.6f}' for v in pooled])
    blocks['allfields_table'] = latex_table('lrrrr', ['Field (kV/cm)', 'Single', 'Stretched', 'Distributed', 'Biexponential'], fold_rows)
    plots = []
    for parameter, symbol in [('log_tau0', r'$\ell_0$'), ('b0', '$b_0$'), ('b1', '$b_1$'), ('b2', '$b_2$'), ('cF', '$c_F$')]:
        data = read_csv(f'validation/native/identifiability/profile_{parameter}.csv')
        points = ' '.join(f"({r['value']},{r['stat']})" for r in data)
        lo, hi = min(float(r['value']) for r in data), max(float(r['value']) for r in data)
        plots.append(r'\begin{tikzpicture}\begin{axis}[width=.45\linewidth,height=43mm,grid=major,xlabel={' + symbol + r'},ylabel={$\Lambda$},ymin=0]' + '\n'
                     + r'\addplot[blue!70!black,thick] coordinates {' + points + '};\n'
                     + r'\addplot[black,dashed,domain=' + str(lo) + ':' + str(hi) + r'] {3.841458820694124};' + '\n'
                     + r'\end{axis}\end{tikzpicture}')
    blocks['additional_profiles'] = '\n'.join(plots)
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
                    'scripts/*.py', 'data/*', 'validation/native/**/*', 'validation/reference/**/*', 'supplementary/figures/*']:
        paths.update(p for p in ROOT.glob(pattern) if p.is_file())
    paths.update(ROOT / p for p in ['pyproject.toml', 'poetry.lock', 'validation/migration.json'])
    source_files = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    git_head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=False)
    snapshot = dict(package_version=project['version'], base_git_commit=git_head.stdout.strip() if git_head.returncode == 0 else None,
                    identity='Supplement input snapshot; Git ancestry is not a release identifier.', source_files=source_files)
    snapshot_json = json.dumps(snapshot, indent=2) + '\n'
    digest = hashlib.sha256(snapshot_json.encode()).hexdigest()
    blocks['source_snapshot'] = '\n'.join('% ' + line for line in snapshot_json.splitlines())
    commands = dict(PackageVersion=project['version'], SnapshotHash=digest,
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
    args = parser.parse_args()
    snapshot = generate()
    print(f"Updated standalone document from {len(snapshot['source_files'])} source/evidence files.")


if __name__ == '__main__':
    main()
