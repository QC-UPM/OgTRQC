"""Independent phenomenological polarization models and calibration-only fits.

Transport trajectories are never inputs to these models. The positive fitted
coefficient chi_cond maps to alpha_A = chi_cond E_A/(k_B T); transferring it to
transport is an explicit hypothesis, not a common-mechanism validation.
"""

from dataclasses import dataclass
from enum import Enum
import numpy as np
from scipy.optimize import least_squares, OptimizeResult

from octa_gtrqc_sim.proton.dataset import PolarizationDataset
from octa_gtrqc_sim.proton.structure import StructuralModel
from octa_gtrqc_sim.proton.transport import KB_EV_K


class RelaxationKind(str, Enum):
    """Supported field-law comparators, retaining the notebook parameter counts."""

    SINGLE = 'single'
    STRETCHED = 'stretched'
    DISTRIBUTED = 'distributed'
    BIEXPONENTIAL = 'biexponential'


@dataclass
class FitResult:
    """Calibration output with its training partition recorded explicitly.

    Attributes:
        kind: Selected relaxation law.
        training_indices: Field columns used in optimization.
        optimizer: SciPy optimization result, including Jacobian and residuals.
        start_audit: Training SSE and convergence status for each fixed start.
    """

    kind: RelaxationKind
    training_indices: tuple[int, ...]
    optimizer: OptimizeResult
    start_audit: list[dict]

    @property
    def theta(self) -> np.ndarray:
        """numpy.ndarray: Fitted parameter vector in the notebook convention."""
        return self.optimizer.x

    @property
    def covariance(self) -> np.ndarray:
        """numpy.ndarray: Local fixed-variance Jacobian covariance estimate."""
        r, j = self.optimizer.fun, self.optimizer.jac
        sigma2 = float(r @ r / (r.size - self.theta.size))
        return sigma2 * np.linalg.pinv(j.T @ j)


class RelaxationModel:
    """Predict and fit field-dependent polarization relaxation curves.

    Args:
        kind: Relaxation law; defaults to the 21-state distributed spectrum.
        structure: Structural energy scale used only to express chi_cond.
        temperature_k: Spectrum temperature in kelvin.

    Attributes:
        kind: Model identifier.
        structure: Literature-based structural scale.
        temperature_k: Spectrum temperature.
        z: The 21 fixed dimensionless spectrum coordinates.
    """

    def __init__(self, kind: RelaxationKind | str = RelaxationKind.DISTRIBUTED,
                 structure: StructuralModel | None = None, temperature_k: float = 300.) -> None:
        """Initialize the selected spectrum and physical conversion scale.

        Args:
            kind: Field-dependent relaxation law.
            structure: Optional literature-derived energy scale.
            temperature_k: Positive spectrum temperature in kelvin.
        """
        self.kind = RelaxationKind(kind)
        self.structure = structure or StructuralModel()
        if not np.isfinite(temperature_k) or temperature_k <= 0:
            raise ValueError('Temperature must be finite and positive.')
        self.temperature_k = temperature_k
        self.z = np.linspace(0., 1., 21)

    @property
    def energy_scale(self) -> float:
        """float: Conversion factor from chi_cond to the identifiable alpha_A."""
        return self.structure.e_a / (KB_EV_K * self.temperature_k)

    @property
    def bounds(self) -> tuple[np.ndarray, np.ndarray]:
        """tuple: Parameter bounds retained verbatim from the source notebooks."""
        values = {
            RelaxationKind.SINGLE: ([-20., -10.], [5., 10.]),
            RelaxationKind.STRETCHED: ([-20., -10., -10., -10.], [5., 10., 10., 10.]),
            RelaxationKind.DISTRIBUTED: ([np.log(1e-6), .05, -20., -20., -20., -5.],
                                       [0., 3., 20., 20., 20., 5.]),
            RelaxationKind.BIEXPONENTIAL: ([-20., -10., -20., -10., -10., -10.],
                                         [5., 10., 5., 10., 10., 10.]),
        }
        return tuple(np.asarray(v) for v in values[self.kind])

    @property
    def starts(self) -> list[np.ndarray]:
        """list: Fixed initialization vectors; selection uses training SSE only."""
        if self.kind == RelaxationKind.SINGLE:
            return [np.array([np.log(.01), .5])]
        if self.kind == RelaxationKind.STRETCHED:
            return [np.array([np.log(.005), .5, -1., -.5])]
        if self.kind == RelaxationKind.DISTRIBUTED:
            return [np.array([np.log(7e-4), 1., 0., 0., 0., 1.])]
        return [np.array([np.log(a), .5, np.log(b), .5, 0., 0.])
                for a, b in [(1e-4, .1), (1e-3, 1.), (1e-2, 10.)]]

    def predict(self, theta: np.ndarray, time_s: np.ndarray, field_kv_cm: float) -> np.ndarray:
        """Evaluate a curve without observing its experimental target values.

        Args:
            theta: Parameter vector in the notebook's original convention.
            time_s: Finite nonnegative observation times in seconds.
            field_kv_cm: Applied field in kV/cm, scaled as (field - 333)/200.

        Returns:
            Normalized polarization at the requested times.

        Raises:
            ValueError: If time, field, or parameter shape is invalid.
        """
        th, t = np.asarray(theta, dtype=float), np.asarray(time_s, dtype=float)
        if (th.shape != self.bounds[0].shape or not np.isfinite(th).all()
                or t.ndim != 1 or not np.isfinite(t).all() or np.any(t < 0)
                or not np.isfinite(field_kv_cm)):
            raise ValueError('Invalid parameter vector, field, or time grid.')
        f = (field_kv_cm - 333.) / 200.
        if self.kind == RelaxationKind.SINGLE:
            return np.exp(-t / np.exp(th[0] + th[1] * f))
        if self.kind == RelaxationKind.STRETCHED:
            beta = .05 + .90 / (1 + np.exp(-np.clip(th[2] + th[3] * f, -50., 50.)))
            return np.exp(-(t / np.exp(th[0] + th[1] * f))**beta)
        if self.kind == RelaxationKind.BIEXPONENTIAL:
            w = 1 / (1 + np.exp(-(th[4] + th[5] * f)))
            return (w * np.exp(-t / np.exp(th[0] + th[1] * f))
                    + (1 - w) * np.exp(-t / np.exp(th[2] + th[3] * f)))
        tau = np.exp(np.clip(th[0] + th[1] * self.energy_scale * self.z + th[5] * f, -50., 50.))
        logits = (th[2] + th[3] * f) * self.z + th[4] * (self.z - .5)**2
        w = np.exp(logits - logits.max())
        w /= w.sum()
        return np.exp(-t[:, None] / tau[None, :]) @ w

    def residual(self, theta: np.ndarray, data: PolarizationDataset,
                 training_indices: tuple[int, ...] = (0, 1, 2)) -> np.ndarray:
        """Concatenate residuals only from the declared training fields.

        Args:
            theta: Trial parameter vector.
            data: Experimental time grid and traces.
            training_indices: Field columns included in calibration.

        Returns:
            Residual vector ordered first by field, then by observation time.
        """
        return np.concatenate([self.predict(theta, data.time_s, data.fields_kv_cm[i])
                               - data.observed[:, i] for i in training_indices])

    def fit(self, data: PolarizationDataset,
            training_indices: tuple[int, ...] = (0, 1, 2)) -> FitResult:
        """Fit with the original starts, bounds, budgets, and tolerances.

        Args:
            data: Experimental observations.
            training_indices: Explicit field partition. The default excludes
                all 87 observations at 533 kV/cm.

        Returns:
            Best converged candidate selected by training SSE alone.

        Raises:
            ValueError: If indices are empty, repeated, or invalid.
            RuntimeError: If any prescribed optimizer start fails to converge.
        """
        if (not training_indices or len(set(training_indices)) != len(training_indices)
                or any(i not in range(4) for i in training_indices)):
            raise ValueError('Training indices must be distinct valid field columns.')
        options = dict(max_nfev=20000, xtol=1e-11, ftol=1e-11, gtol=1e-11)
        if self.kind in (RelaxationKind.SINGLE, RelaxationKind.STRETCHED):
            options = dict(max_nfev=10000 if self.kind == RelaxationKind.SINGLE else 15000)
        candidates = [least_squares(self.residual, start, bounds=self.bounds,
                                   args=(data, training_indices), **options) for start in self.starts]
        if not all(r.success for r in candidates):
            raise RuntimeError(f'Optimization failed for {self.kind.value}.')
        audit = [dict(start=i, sse=float(r.fun @ r.fun), success=bool(r.success),
                      theta=r.x.tolist()) for i, r in enumerate(candidates)]
        best = min(candidates, key=lambda r: float(r.fun @ r.fun))
        return FitResult(self.kind, tuple(training_indices), best, audit)

    def prediction_jacobian(self, theta: np.ndarray, time_s: np.ndarray,
                            fields_kv_cm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Evaluate the R2.5 analytic distributed-spectrum Jacobian.

        Args:
            theta: Six distributed-spectrum parameters.
            time_s: Observation times in seconds.
            fields_kv_cm: Calibration fields in kV/cm.

        Returns:
            Flattened predictions and a six-column analytic Jacobian, both
            ordered by field then time. Used for nuisance-parameter profiles.

        Raises:
            ValueError: If the model is not the distributed spectrum.
        """
        if self.kind != RelaxationKind.DISTRIBUTED:
            raise ValueError('Analytic spectrum Jacobian requires the distributed model.')
        z, z2 = self.z, (self.z - .5)**2
        f = (np.asarray(fields_kv_cm) - 333.) / 200.
        lt = theta[0] + theta[1] * self.energy_scale * z[None, :] + theta[5] * f[:, None]
        logits = (theta[2] + theta[3] * f[:, None]) * z + theta[4] * z2
        w = np.exp(logits - logits.max(axis=1, keepdims=True))
        w /= w.sum(axis=1, keepdims=True)
        u = time_s[None, :, None] * np.exp(-lt)[:, None, :]
        wg = w[:, None, :] * np.exp(-u)
        dl = (wg * u).sum(axis=2)
        dc = (wg * u * z).sum(axis=2) * self.energy_scale
        db = (wg * (z[None, None, :] - (w * z).sum(axis=1)[:, None, None])).sum(axis=2)
        db2 = (wg * (z2[None, None, :] - (w * z2).sum(axis=1)[:, None, None])).sum(axis=2)
        jac = np.stack([dl, dc, db, f[:, None] * db, db2, f[:, None] * dl], axis=2).reshape(-1, 6)
        return wg.sum(axis=2).reshape(-1), jac


def experimental_metrics(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    """Compute the notebook's prediction and residual-correlation metrics.

    Args:
        observed: Experimental normalized polarization.
        predicted: Model prediction on the same time grid.

    Returns:
        RMSE, range-normalized RMSE, R-squared, MAE, lag-one residual
        correlation, and Durbin--Watson statistic.
    """
    residual = np.asarray(predicted) - observed
    rmse = float(np.sqrt(np.mean(residual**2)))
    return dict(RMSE=rmse, NRMSE=rmse / max(float(np.ptp(observed)), 1e-15),
                R2=1 - float(residual @ residual) / max(float(np.sum((observed - observed.mean())**2)), 1e-15),
                MAE=float(np.mean(abs(residual))),
                lag1=float(np.corrcoef(residual[:-1], residual[1:])[0, 1]),
                durbin_watson=float(np.sum(np.diff(residual)**2) / max(float(residual @ residual), 1e-15)))
