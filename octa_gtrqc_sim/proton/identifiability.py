"""Calibration-only fixed-scale profiles from the R2.5 notebook."""

import numpy as np
import pandas as pd
from scipy.optimize import least_squares, brentq
from scipy.stats import chi2
from octa_gtrqc_sim.proton.dataset import PolarizationDataset
from octa_gtrqc_sim.proton.relaxation import RelaxationModel, FitResult
from octa_gtrqc_sim.proton.studies import StudyResult


class IdentifiabilityStudy:
    """Profile nuisance parameters without using the 533 kV/cm observations.

    Args:
        data: Optional experimental dataset.

    Attributes:
        data: Dataset, with only its first three columns used in this study.
        model: Distributed-relaxation law in original chi_cond coordinates.
    """

    def __init__(self, data: PolarizationDataset | None = None) -> None:
        """Initialize calibration-only diagnostics and the spectrum model.

        Args:
            data: Optional experimental dataset; the final field is excluded.
        """
        self.data = data or PolarizationDataset.load()
        self.model = RelaxationModel()

    def run(self, *, additional_profiles: bool = True) -> StudyResult:
        """Reproduce the 31-point alpha profile and optional five extra profiles.

        Args:
            additional_profiles: Also profile log_tau0, b0, b1, b2, and cF with
                bounded nuisance refits and connected-component endpoint search.

        Returns:
            Original accepted-grid alpha interval, covariance-derived correlation,
            nuisance optima, convergence diagnostics, and extra profile endpoints.
            These are fixed residual-scale support intervals, not proof of global
            uniqueness or independent physical identification.
        """
        model, data = self.model, self.data
        fit = model.fit(data)
        theta, (lo, hi) = fit.theta, model.bounds
        sigma2 = float(fit.optimizer.fun @ fit.optimizer.fun / (fit.optimizer.fun.size - 6))
        cutoff = float(chi2.ppf(.95, 1))
        cov = fit.covariance
        se = np.sqrt(np.diag(cov))
        correlation = cov / np.outer(se, se)
        rows = []
        free = np.array([0, 2, 3, 4, 5])
        for value in np.linspace(max(.05, theta[1] - .5), min(3., theta[1] + .5), 31):
            def residual(x: np.ndarray) -> np.ndarray:
                """Evaluate the reference calibration objective at fixed coefficient."""
                th = theta.copy()
                th[1], th[free] = value, x
                return model.residual(th, data)
            result = least_squares(residual, theta[free], bounds=(lo[free], hi[free]), max_nfev=3000)
            row = dict(chi_cond=float(value), alpha_A=float(value * model.energy_scale),
                       sse=float(result.fun @ result.fun), success=bool(result.success))
            row.update({f'fit_{j}': float(v) for j, v in zip(free, result.x)})
            rows.append(row)
        grid = pd.DataFrame(rows)
        if not grid.success.all():
            raise RuntimeError('An original alpha-profile nuisance fit did not converge.')
        grid['stat'] = (grid.sse - grid.sse.min()) / sigma2
        inside = grid[grid.stat <= cutoff]
        names = ['log_tau0', 'alpha_A', 'b0', 'b1', 'b2', 'cF']
        corr = pd.DataFrame(correlation, columns=names)
        corr.insert(0, 'parameter', names)
        tables = dict(original_alpha_profile_31_points=grid, parameter_correlation=corr)
        intervals = []
        if additional_profiles:
            for j in (0, 2, 3, 4, 5):
                summary, profile = self._profile(j, fit, sigma2, cutoff)
                intervals.append(summary)
                tables['profile_' + names[j]] = profile
            tables['additional_profile_intervals'] = pd.DataFrame(intervals)
        _, analytic = model.prediction_jacobian(theta, data.time_s, data.fields_kv_cm[:3])
        return StudyResult('identifiability', tables,
                           dict(alpha_A=float(theta[1] * model.energy_scale), chi_cond=float(theta[1]),
                                alpha_accepted_grid_interval=[float(inside.alpha_A.min()), float(inside.alpha_A.max())],
                                sigma2_fixed=sigma2, cutoff=cutoff, holdout_observations_used=False,
                                calibration_observations=261, covariance=cov.tolist(),
                                jacobian_condition=float(np.linalg.cond(fit.optimizer.jac)),
                                alpha_jacobian_condition=float(np.linalg.cond(analytic @ np.diag([1, 1 / model.energy_scale, 1, 1, 1, 1]))),
                                analytic_jacobian_max_difference=float(np.max(abs(analytic - fit.optimizer.jac))),
                                scope='Working Gaussian fixed-scale profiles; positive alpha convention; original accepted-grid interval retained.'))

    def _profile(self, index: int, fit: FitResult, sigma2: float, cutoff: float) -> tuple[dict, pd.DataFrame]:
        """Compute one R2.5 profile using covariance-informed nuisance starts.

        Args:
            index: Fixed parameter index, excluding the original grid coefficient.
            fit: Calibration-only reference fit.
            sigma2: Residual variance fixed at the reference optimum.
            cutoff: One-parameter chi-square support threshold.

        Returns:
            Connected-interval summary and all evaluated nuisance optima.
        """
        model, data = self.model, self.data
        theta, cov = fit.theta, fit.covariance
        lo, hi = model.bounds
        free = np.delete(np.arange(6), index)
        cache: dict[float, dict] = {}
        sse0 = float(fit.optimizer.fun @ fit.optimizer.fun)
        se = np.sqrt(cov[index, index])

        def evaluate(value: float) -> dict:
            """Cache the best converged nuisance fit for a fixed profile value."""
            key = float(value)
            if key in cache:
                return cache[key]
            base = theta.copy()
            base[index] = value
            starts = [theta[free], np.clip(theta + cov[:, index] / cov[index, index] * (value - theta[index]),
                                           lo + 1e-9, hi - 1e-9)[free]]
            if cache:
                starts.append(min(cache.items(), key=lambda kv: abs(kv[0] - value))[1]['theta'][free])
            def unpack(x: np.ndarray) -> np.ndarray:
                """Restore the six-parameter vector from five nuisance parameters."""
                th = base.copy()
                th[free] = x
                return th
            def residual(x: np.ndarray) -> np.ndarray:
                """Evaluate the reference calibration objective at fixed coefficient."""
                p, _ = model.prediction_jacobian(unpack(x), data.time_s, data.fields_kv_cm[:3])
                return p - data.observed[:, :3].T.reshape(-1)
            def jacobian(x: np.ndarray) -> np.ndarray:
                """Select nuisance columns of the analytic calibration Jacobian."""
                return model.prediction_jacobian(unpack(x), data.time_s, data.fields_kv_cm[:3])[1][:, free]
            candidates = [least_squares(residual, np.clip(start, lo[free] + 1e-9, hi[free] - 1e-9), jac=jacobian,
                                       bounds=(lo[free], hi[free]), xtol=1e-10, ftol=1e-10, gtol=1e-10, max_nfev=4000)
                          for start in starts]
            result = min(candidates, key=lambda r: float(r.fun @ r.fun))
            if not result.success:
                raise RuntimeError(f'Nuisance profile failed at parameter {index} = {value}.')
            sse = float(result.fun @ result.fun)
            entry = dict(value=key, sse=sse, theta=unpack(result.x), stat=(sse - sse0) / sigma2,
                         success=bool(result.success), optimality=float(result.optimality), nfev=int(result.nfev),
                         active_nuisance=int(np.sum(abs(result.active_mask) > 0)))
            cache[key] = entry
            return entry

        grid = np.unique(np.r_[np.linspace(max(lo[index], theta[index] - 5 * se), theta[index], 31),
                               np.linspace(theta[index], min(hi[index], theta[index] + 5 * se), 31)])
        for value in sorted(grid, key=lambda a: abs(a - theta[index])):
            evaluate(value)
        endpoints = []
        for side in (-1, 1):
            seq = sorted([a for a in cache if side * (a - theta[index]) >= 0], reverse=side < 0)
            previous, bracket = theta[index], None
            for value in seq:
                if evaluate(value)['stat'] >= cutoff:
                    bracket = sorted([previous, value])
                    break
                previous = value
            if bracket is None:
                bound = lo[index] if side < 0 else hi[index]
                for value in np.linspace(previous, bound, 31)[1:]:
                    if evaluate(value)['stat'] >= cutoff:
                        bracket = sorted([previous, value])
                        break
                    previous = value
            endpoints.append(float(previous) if bracket is None else float(brentq(
                lambda a: evaluate(a)['stat'] - cutoff, *bracket, xtol=2e-7)))
        name = ['log_tau0', 'chi_cond', 'b0', 'b1', 'b2', 'cF'][index]
        summary = dict(parameter=name, estimate=float(theta[index]), lower=endpoints[0], upper=endpoints[1],
                       local_se=float(se), lower_at_bound=bool(abs(endpoints[0] - lo[index]) < 1e-6),
                       upper_at_bound=bool(abs(endpoints[1] - hi[index]) < 1e-6), cutoff=cutoff)
        records = []
        for _, entry in sorted(cache.items()):
            row = {k: v for k, v in entry.items() if k != 'theta'}
            row.update({f'fit_{j}': float(v) for j, v in enumerate(entry['theta'])})
            records.append(row)
        return summary, pd.DataFrame(records)
