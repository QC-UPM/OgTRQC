"""Model--View--Presenter orchestration and portable scientific artifacts."""

from pathlib import Path
from typing import Protocol, Callable
import hashlib
import json
import platform

import numpy as np
import scipy

from octa_gtrqc_sim.proton.studies import CalibrationStudy, StudyResult
from octa_gtrqc_sim.proton.identifiability import IdentifiabilityStudy
from octa_gtrqc_sim.proton.audits import RefinementStudy, TransportSensitivityStudy, HiddenStateStudy, ContinuumStudy


class StudyView(Protocol):
    """Presentation interface independent of all scientific model choices."""

    def render(self, result: StudyResult) -> Path:
        """Persist or display a completed study.

        Args:
            result: Presentation-neutral tables, arrays, and metadata.

        Returns:
            Location of the rendered artifact.
        """
        ...


class ArtifactView:
    """Write study tables, provenance, and publication-friendly figures.

    Args:
        output_directory: Destination for one subdirectory per study.

    Attributes:
        output_directory: Root of the generated artifacts.
    """

    def __init__(self, output_directory: str | Path) -> None:
        """Select the artifact root without creating files until rendering.

        Args:
            output_directory: Destination for named study directories.
        """
        self.output_directory = Path(output_directory)

    def render(self, result: StudyResult) -> Path:
        """Export CSV, strict JSON, NPZ, Markdown, and available vector figures.

        Args:
            result: Completed scientific study.

        Returns:
            Directory containing outputs and a SHA-256 artifact manifest.
        """
        root = self.output_directory / result.name
        root.mkdir(parents=True, exist_ok=True)
        produced: list[Path] = []
        for name, table in result.tables.items():
            path = root / f'{name}.csv'
            table.to_csv(path, index=False)
            produced.append(path)
        metadata = dict(result.metadata)
        metadata['environment'] = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__)
        path = root / 'metadata.json'
        path.write_text(json.dumps(metadata, indent=2, allow_nan=False) + '\n')
        produced.append(path)
        if result.arrays:
            path = root / 'arrays.npz'
            np.savez_compressed(path, **result.arrays)
            produced.append(path)
        produced.extend(self._figures(result, root))
        report = root / 'README.md'
        lines = [f'# {result.name.replace("_", " ").title()}', '', str(metadata.get('scope', 'Paper-aligned study.')), '',
                 'Numerical tables and metadata are generated from the package models.', '',
                 *[f'- [{p.name}]({p.name})' for p in produced], '']
        report.write_text('\n'.join(lines))
        produced.append(report)
        manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in produced}
        (root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        return root

    def _figures(self, result: StudyResult, root: Path) -> list[Path]:
        """Render scientific plots as standalone PDF and SVG files.

        Args:
            result: Study data; plotting never refits a model.
            root: Study output directory.

        Returns:
            Paths of generated figure files, or an empty list if not applicable.
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        figure = None
        if 'predictions' in result.tables:
            table = result.tables['predictions']
            selected = table[table.field_kv_cm == 533]
            figure, axis = plt.subplots(figsize=(7, 4.5))
            observed = selected.drop_duplicates('time_s')
            axis.scatter(observed.time_s, observed.observed, s=12, color='black', label='Published 533 kV/cm')
            for name, group in selected.groupby('model', sort=False):
                axis.plot(group.time_s, group.predicted, label=name)
            axis.set(xscale='log', xlabel='Time (s)', ylabel='Normalized polarization')
            axis.legend()
        elif 'full_generator' in result.tables:
            figure, axis = plt.subplots(figsize=(6, 4))
            for name, group in result.tables['full_generator'].groupby('case', sort=False):
                axis.loglog(group.N, group.relative_L2_error, 'o-', label=name)
            axis.set(xlabel='Device cells N', ylabel='Relative L2 error')
            axis.legend()
        elif 'original_alpha_profile_31_points' in result.tables:
            figure, axis = plt.subplots(figsize=(6, 4))
            table = result.tables['original_alpha_profile_31_points']
            axis.plot(table.alpha_A, table.stat, 'o-')
            axis.axhline(result.metadata['cutoff'], linestyle='--', color='black')
            axis.set(xlabel='Dimensionless spectrum slope alpha_A', ylabel='Fixed-scale profile statistic')
        elif 'prediction_intervals' in result.tables:
            figure, axis = plt.subplots(figsize=(7, 4.5))
            table = result.tables['prediction_intervals']
            axis.fill_between(table.time_s, table.lower, table.upper, alpha=.2, label='Pointwise 95% interval')
            axis.scatter(table.time_s, table.observed, s=12, label='Holdout')
            axis.plot(table.time_s, table.predicted, label='Distributed spectrum')
            axis.set(xscale='log', xlabel='Time (s)', ylabel='Normalized polarization')
            axis.legend()
        if figure is None:
            return []
        figure.tight_layout()
        paths = [root / 'figure.pdf', root / 'figure.svg']
        for path in paths:
            figure.savefig(path)
        plt.close(figure)
        return paths


class PaperPresenter:
    """Coordinate paper studies and a replaceable artifact view.

    Args:
        view: Rendering implementation; no model imports a view.
        progress: Optional status callback, called before each study.

    Attributes:
        view: Selected output interface.
        progress: Progress notification callback.
    """

    def __init__(self, view: StudyView, progress: Callable[[str], None] | None = None) -> None:
        """Bind scientific orchestration to a replaceable presentation layer.

        Args:
            view: Object implementing the StudyView protocol.
            progress: Optional notification callback receiving a status string.
        """
        self.view = view
        self.progress = progress or (lambda message: None)

    def run(self, study: str = 'calibration', *, bootstrap_repetitions: int = 100,
            additional_profiles: bool = True, reference_cells: int = 8192) -> list[Path]:
        """Execute one named study or the complete native paper campaign.

        Args:
            study: Calibration, review, uncertainty, identifiability, refinement,
                transport_sensitivity, hidden_state, start_sensitivity, or all.
            bootstrap_repetitions: Refits for calibration-only uncertainty.
            additional_profiles: Include the five R2.5 nuisance profiles.
            reference_cells: Fine mesh for the R3 refinement reference.

        Returns:
            Output directories produced by the selected view.

        Raises:
            ValueError: If the study name is not recognized.
        """
        calibration = CalibrationStudy()
        jobs = {
            'calibration': calibration.run,
            'review': lambda: calibration.run(retrospective=True),
            'uncertainty': lambda: calibration.bootstrap(bootstrap_repetitions),
            'identifiability': lambda: IdentifiabilityStudy().run(additional_profiles=additional_profiles),
            'transport_sensitivity': TransportSensitivityStudy().run,
            'continuum': ContinuumStudy().run,
            'refinement': lambda: RefinementStudy().run(reference_cells=reference_cells),
            'hidden_state': HiddenStateStudy().run,
            'start_sensitivity': calibration.start_sensitivity,
        }
        if study != 'all' and study not in jobs:
            raise ValueError(f'Unknown study: {study}')
        selected = jobs if study == 'all' else {study: jobs[study]}
        outputs = []
        for name, job in selected.items():
            self.progress(f'Running {name} ...')
            outputs.append(self.view.render(job()))
        return outputs
