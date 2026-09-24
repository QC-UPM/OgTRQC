"""Reproducible calibration, retrospective comparison, and uncertainty studies."""

from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from octa_gtrqc_sim.proton.dataset import PolarizationDataset
from octa_gtrqc_sim.proton.relaxation import RelaxationKind, RelaxationModel, FitResult, experimental_metrics


@dataclass
class StudyResult:
    """Presentation-neutral output of a scientific study.

    Attributes:
        name: Stable study identifier used as the output directory name.
        tables: Named data frames exported as CSV files.
        metadata: JSON-serializable configuration, scope, and numerical summaries.
        arrays: Named numeric arrays exported together as compressed NPZ.
    """

    name: str
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    arrays: dict[str, np.ndarray] = field(default_factory=dict)


class CalibrationStudy:
    """Primary holdout evaluation and separately labelled retrospective refits.

    Args:
        data: Optional offline dataset; loaded from package resources by default.

    Attributes:
        data: Experimental observations with provenance.
    """

    def __init__(self, data: PolarizationDataset | None = None) -> None:
        """Load offline observations or retain an explicitly supplied dataset.

        Args:
            data: Experimental observations with their provenance metadata.
        """
        self.data = data or PolarizationDataset.load()

    def run(self, *, retrospective: bool = False) -> StudyResult:
        """Fit the declared comparators without selecting on held-out outcomes.

        Args:
            retrospective: Run all four leave-one-field-out folds and the
                six-parameter biexponential comparator from the review addendum.
                False reproduces the three original strict-holdout models.

        Returns:
            Scores, point predictions, fit parameters, starts, and working
            Gaussian information criteria. Only the primary fold is strict.
        """
        data = self.data
        folds = range(4) if retrospective else (3,)
        kinds = list(RelaxationKind) if retrospective else list(RelaxationKind)[:3]
        scores, points, parameters, criteria, starts = [], [], [], [], []
        for fold in folds:
            train = tuple(i for i in range(4) if i != fold)
            for kind in kinds:
                model = RelaxationModel(kind)
                result = model.fit(data, train)
                predicted = model.predict(result.theta, data.time_s, data.fields_kv_cm[fold])
                n, k = result.optimizer.fun.size, result.theta.size + 1
                sse = float(result.optimizer.fun @ result.optimizer.fun)
                label = dict(field_kv_cm=float(data.fields_kv_cm[fold]), model=kind.value)
                scores.append(dict(**label, parameters=k - 1, train_sse=sse,
                                   train_n=n, **experimental_metrics(data.observed[:, fold], predicted)))
                points.extend(dict(**label, time_s=float(t), observed=float(y), predicted=float(p))
                              for t, y, p in zip(data.time_s, data.observed[:, fold], predicted))
                parameters.append(dict(**label, training_fields_kv_cm=data.fields_kv_cm[list(train)].tolist(),
                                       theta=result.theta.tolist(), success=bool(result.optimizer.success),
                                       nfev=int(result.optimizer.nfev)))
                starts.extend(dict(**label, **record) for record in result.start_audit)
                if fold == 3:
                    dev = n * np.log(sse / n)
                    criteria.append(dict(model=kind.value, likelihood_parameters=k, n=n, sse=sse,
                                         AIC=dev + 2 * k, AICc=dev + 2 * k + 2 * k * (k + 1) / (n - k - 1),
                                         BIC=dev + k * np.log(n)))
        ic = pd.DataFrame(criteria)
        for col in ('AIC', 'AICc', 'BIC'):
            ic['delta_' + col] = ic[col] - ic[col].min()
        return StudyResult('review' if retrospective else 'calibration',
                           dict(scores=pd.DataFrame(scores), predictions=pd.DataFrame(points), information_criteria=ic),
                           dict(fits=parameters, start_audit=starts, provenance=data.provenance,
                                scope=('Retrospective whole-field refits; not four independent experiments.' if retrospective
                                       else 'Strict 533 kV/cm holdout; calibration fields 133, 267, 400 only.'),
                                likelihood='Working iid homoscedastic Gaussian; fitted variance counted. Temporal correlation is not modelled.'))

    def bootstrap(self, repetitions: int = 100, seed: int = 20260802 + 701) -> StudyResult:
        """Reproduce calibration-residual prediction intervals from v3.1.

        Args:
            repetitions: Number of parameter refits; the paper uses 100.
            seed: Deterministic random seed used by the original notebook.

        Returns:
            Pointwise 95% prediction bands, retained parameter draws, coverage,
            and an evaluation-only 1500-draw holdout RMSE interval. Residuals
            are resampled pointwise, so serial correlation remains a limitation.

        Raises:
            ValueError: If fewer than two replicates are requested.
            RuntimeError: If fewer than two optimizer fits succeed.
        """
        if repetitions < 2:
            raise ValueError('At least two bootstrap repetitions are required.')
        model, data = RelaxationModel(), self.data
        fit = model.fit(data)
        rng = np.random.default_rng(seed)
        prediction = np.column_stack([model.predict(fit.theta, data.time_s, f) for f in data.fields_kv_cm[:3]])
        residual = data.observed[:, :3] - prediction
        params, holdout = [], []
        for _ in range(repetitions):
            boot_y = prediction.copy()
            for j in range(3):
                boot_y[:, j] += rng.choice(residual[:, j], size=len(data.time_s), replace=True)
            def objective(theta: np.ndarray) -> np.ndarray:
                """Return residuals against calibration-only bootstrap observations."""
                return np.concatenate([model.predict(theta, data.time_s, data.fields_kv_cm[j]) - boot_y[:, j]
                                       for j in range(3)])
            candidate = least_squares(objective, fit.theta, bounds=model.bounds, max_nfev=3000,
                                      xtol=1e-8, ftol=1e-8, gtol=1e-8)
            if candidate.success and np.isfinite(candidate.x).all():
                params.append(candidate.x)
                holdout.append(model.predict(candidate.x, data.time_s, 533.))
        if len(holdout) < 2:
            raise RuntimeError('Too few converged bootstrap replicates.')
        predictive = np.asarray(holdout) + np.asarray([rng.choice(residual.ravel(), size=len(data.time_s), replace=True)
                                                       for _ in holdout])
        low, high = np.quantile(predictive, [.025, .975], axis=0)
        y, pred = data.observed[:, 3], model.predict(fit.theta, data.time_s, 533.)
        errors = []
        for _ in range(1500):
            idx = rng.integers(0, len(y), size=len(y))
            errors.append(float(np.sqrt(np.mean((pred[idx] - y[idx])**2))))
        return StudyResult('uncertainty',
                           dict(prediction_intervals=pd.DataFrame(dict(time_s=data.time_s, observed=y, predicted=pred,
                                                                      lower=low, upper=high))),
                           dict(seed=seed, requested_replicates=repetitions, successful_replicates=len(params),
                                coverage=float(np.mean((y >= low) & (y <= high))), mean_width=float(np.mean(high - low)),
                                evaluation_only_rmse_interval=np.quantile(errors, [.025, .975]).tolist(),
                                scope='Calibration-only pointwise residual bootstrap; not simultaneous bands or correlation-aware intervals.'),
                           dict(parameters=np.asarray(params), holdout_predictions=np.asarray(holdout)))

    def start_sensitivity(self) -> StudyResult:
        """Reproduce addendum optimizer-start checks without replacing fits.

        Returns:
            Training-SSE differences for three fixed starts per original model
            per field fold. Neither holdout errors nor this audit select the
            reported original predictions.
        """
        rows = []
        for fold in range(4):
            train = tuple(i for i in range(4) if i != fold)
            for kind in list(RelaxationKind)[:3]:
                model = RelaxationModel(kind)
                reference = model.fit(self.data, train)
                starts = [model.starts[0].copy() for _ in range(3)]
                starts[1][0] -= 1
                starts[2][0] += 1
                if kind == RelaxationKind.DISTRIBUTED:
                    starts[1][1], starts[2][1] = .5, 1.5
                for i, start in enumerate(starts):
                    fit = least_squares(model.residual, start, bounds=model.bounds, args=(self.data, train),
                                        max_nfev=20000, ftol=1e-11, xtol=1e-11, gtol=1e-11)
                    rows.append(dict(field_kv_cm=float(self.data.fields_kv_cm[fold]), model=kind.value, start=i,
                                     success=bool(fit.success), rss_difference=float(fit.fun @ fit.fun - reference.optimizer.fun @ reference.optimizer.fun)))
        return StudyResult('start_sensitivity', dict(audit=pd.DataFrame(rows)),
                           dict(scope='Numerical start audit; original predictions are retained.'))
