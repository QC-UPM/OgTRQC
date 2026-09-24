"""Transport coefficient and mesh-refinement audits from the review notebooks."""

from dataclasses import replace
import numpy as np
import pandas as pd
from scipy.linalg import eigh_tridiagonal

from octa_gtrqc_sim.proton.transport import DeviceConfig, TransportModel, KB_EV_K, FrozenGenerator
from octa_gtrqc_sim.proton.studies import StudyResult
from octa_gtrqc_sim.proton.diagnostics import RecoverabilityDiagnostic


class TransportSensitivityStudy:
    """Audit independent transport coefficients while keeping relaxation fixed.

    Args:
        config: Optional device parameters, including the nominal transfer value.

    Attributes:
        config: Immutable device configuration.
    """

    def __init__(self, config: DeviceConfig | None = None) -> None:
        """Retain explicit device parameters for the conditional sweep.

        Args:
            config: Device parameters, including the nominal transfer value.
        """
        self.config = config or DeviceConfig()

    def run(self) -> StudyResult:
        """Execute the review addendum's seven-coefficient, three-profile audit.

        Returns:
            Conditional diffusion scales, operator changes, spectral gaps,
            conservation, detailed balance, and entropy-production residuals.
            The coefficient range [0, 2] is a stress range, not a confidence band.
        """
        cfg = self.config
        n = 32
        x = (np.arange(n) + .5) / n
        backgrounds = {'uniform_0.1': np.full(n, .1), 'uniform_0.5': np.full(n, .5),
                       'nonuniform_staggered': .3 + .12 * np.cos(2 * np.pi * x) + .05 * (-1.)**np.arange(n)}
        rows, audits = [], []
        for coefficient in (0., .25, .5, cfg.chi_transport, 1., 1.5, 2.):
            model = TransportModel(replace(cfg, chi_transport=coefficient))
            generators = {}
            for name, profile in backgrounds.items():
                generator = model.freeze(profile)
                generators[name] = generator.matrix.toarray()
                audits.append(dict(chi=coefficient, profile=name, **generator.audit()))
            q1, q5 = generators['uniform_0.1'], generators['uniform_0.5']
            change = float(np.linalg.norm(q5 - q1, 2) / np.linalg.norm(q1, 2))
            beta = 1 / (KB_EV_K * cfg.temperature_k)
            dref = cfg.diffusivity_m2_s * np.exp(-cfg.activation_ev / KB_EV_K * (1 / cfg.temperature_k - 1 / 300.))
            diffusivity = dref * np.exp(-coefficient * model.structure.e_a * .3 * beta)
            rows.append(dict(chi=coefficient, barrier_at_cbar_ev=coefficient * model.structure.e_a * .3,
                             D_eff_m2_s=float(diffusivity), diffusion_time_s=float(cfg.length_m**2 / diffusivity),
                             gap_lower_s_1=float(diffusivity * np.pi**2 / cfg.length_m**2 * np.exp(-abs(cfg.field_v_m) * cfg.length_m * beta)),
                             operator_change=change,
                             operator_change_formula=float(1 - np.exp(-coefficient * model.structure.e_a * .4 * beta))))
        return StudyResult('transport_sensitivity', dict(sensitivity=pd.DataFrame(rows), frozen_generators=pd.DataFrame(audits)),
                           dict(scope='Conditional coefficient stress range [0,2]; frozen generators, no relaxation refit or nonlinear stability claim.',
                                nominal_chi=cfg.chi_transport))


class RefinementStudy:
    """Reproduce the R3 full-generator frozen-background mesh audit.

    Args:
        config: Optional dimensioned device parameters.

    Attributes:
        model: Structure-conditioned transport model.
        duration_s: Notebook comparison time, 0.08 L²/D_ref.
    """

    def __init__(self, config: DeviceConfig | None = None) -> None:
        """Initialize the physical generator and reference propagation time.

        Args:
            config: Optional device parameters in the declared physical units.
        """
        self.model = TransportModel(config)
        cfg = self.model.config
        self.duration_s = .08 * cfg.length_m**2 / cfg.diffusivity_m2_s

    @staticmethod
    def background(n: int, case: str) -> np.ndarray:
        """Sample the prescribed smooth occupancy at cell centres.

        Args:
            n: Number of device cells.
            case: Either ``symmetric`` or ``ramp``.

        Returns:
            Smooth background occupancies used only to freeze coefficients.
        """
        x = (np.arange(n) + .5) / n
        if case == 'symmetric':
            return .3 + .1 * np.cos(2 * np.pi * x)
        if case == 'ramp':
            return .2 + .2 * x
        raise ValueError('Unknown refinement background.')

    def evolve(self, n: int, case: str, *, smooth_limit: bool = False,
               modes: int = 128) -> tuple[np.ndarray, dict]:
        """Propagate using the reversible tridiagonal eigensystem.

        Args:
            n: Number of finite-volume cells.
            case: Prescribed background identifier.
            smooth_limit: Remove the parity statistic only in reference runs.
            modes: Retained eigenmodes; the stationary component is exact.

        Returns:
            Normalized probability and generator diagnostics. Modal convergence
            must be checked separately from spatial convergence.
        """
        generator = self.model.freeze(self.background(n, case), smooth_limit=smooth_limit)
        eigenvalues, vectors = eigh_tridiagonal(-generator.diagonal,
                                                -np.sqrt(generator.forward * generator.reverse),
                                                select='i', select_range=(0, min(modes, n) - 1),
                                                lapack_driver='stebz', tol=1e-16)
        x = (np.arange(n) + .5) / n
        p0 = (1 + .2 * np.sinc(.5 / n) * np.cos(np.pi * x)) / n
        pi = generator.stationary
        sqrtpi = np.sqrt(pi)
        p = pi + sqrtpi * (vectors[:, 1:] @ (np.exp(-eigenvalues[1:] * self.duration_s)
                                            * (vectors[:, 1:].T @ ((p0 - pi) / sqrtpi))))
        row = dict(case=case, N=n, **generator.audit(), mass_error=float(abs(p.sum() - 1)))
        row['gap_ratio'] = row['gap_s_1'] / row['lower_bound_s_1']
        return p, row

    def run(self, sizes: tuple[int, ...] = (16, 32, 64, 128, 256, 512, 1024),
            reference_cells: int = 8192) -> StudyResult:
        """Compare finite parity closure with a doubled smooth-limit reference.

        Args:
            sizes: Mesh sizes dividing both reference grids.
            reference_cells: Fine reference size; paper uses 8192 and 4096.

        Returns:
            Full-generator refinement table, observed orders, reference and
            modal checks, exact-exponential replay, and alternating-grid
            counterexample. The gradient case need not converge at order two.

        Raises:
            ValueError: If reference averaging is incompatible with the meshes.
        """
        if (not sizes or min(sizes) < 16 or any(n % 2 for n in sizes) or reference_cells < 2 * max(sizes)
                or reference_cells % 2 or any((reference_cells // 2) % n for n in sizes)):
            raise ValueError('Both reference grids must be divisible by every test mesh.')
        rows, checks, arrays, orders = [], [], {}, []
        for case in ('symmetric', 'ramp'):
            half = reference_cells // 2
            coarse, _ = self.evolve(half, case, smooth_limit=True)
            fine, _ = self.evolve(reference_cells, case, smooth_limit=True)
            extra, _ = self.evolve(half, case, smooth_limit=True, modes=256)
            checks.append(dict(case=case,
                               reference_doubling_L2=float(np.linalg.norm(fine.reshape(half, 2).sum(1) - coarse) / np.linalg.norm(coarse)),
                               modal_truncation_L2=float(np.linalg.norm(coarse - extra) / np.linalg.norm(coarse))))
            arrays['reference_' + case] = fine
            case_rows = []
            for n in sizes:
                p, row = self.evolve(n, case)
                averaged = fine.reshape(n, -1).sum(1)
                row['relative_L2_error'] = float(np.linalg.norm(p - averaged) / np.linalg.norm(averaged))
                rows.append(row)
                case_rows.append(row)
                arrays[f'{case}_{n}'] = p
            sample = pd.DataFrame(case_rows)
            orders.append(dict(case=case,
                               all_grid_order=float(np.polyfit(np.log(1 / sample.N), np.log(sample.relative_L2_error), 1)[0]),
                               fine_grid_order=float(np.polyfit(np.log(1 / sample.N.iloc[-4:]), np.log(sample.relative_L2_error.iloc[-4:]), 1)[0])))
            n = 64
            generator = self.model.freeze(self.background(n, case))
            x = (np.arange(n) + .5) / n
            direct = generator.propagate((1 + .2 * np.sinc(.5 / n) * np.cos(np.pi * x)) / n, self.duration_s)
            modal, _ = self.evolve(n, case)
            checks[-1]['matrix_exponential_replay_L2'] = float(np.linalg.norm(direct - modal) / np.linalg.norm(direct))
        parity = []
        for n in sizes:
            c = .3 + .05 * (-1.)**np.arange(n)
            _, qr = self.model.structure.equilibrium(c)
            parity.append(dict(N=n, Q_R_A=qr, m_pi=qr / .06, nonvanishing_density_variance=float(np.var(c))))
        cfg, st = self.model.config, self.model.structure
        beta = 1 / (KB_EV_K * cfg.temperature_k)
        # Uniform analytic bound from R3 for the declared reference setup.
        dref = cfg.diffusivity_m2_s * np.exp(-cfg.activation_ev / KB_EV_K * (1 / cfg.temperature_k - 1 / 300.))
        dglobal = dref * np.exp(-beta * (cfg.chi_transport * st.e_a * .4 + .2 * st.e_r / 48 + .15 * st.e_a * cfg.strain / .01))
        uglobal = abs(cfg.field_v_m) * cfg.length_m + .2 * st.e_a * .2 + 2 * .1 * st.e_r / 48
        bound = 8 * dglobal / cfg.length_m**2 * np.exp(-beta * uglobal)
        return StudyResult('refinement', dict(full_generator=pd.DataFrame(rows), orders=pd.DataFrame(orders),
                                              grid_alternating_counterexample=pd.DataFrame(parity)),
                           dict(reference_cells=reference_cells, duration_s=self.duration_s, numerical_checks=checks,
                                uniform_reference_bound_s_1=float(bound),
                                uniform_bound_scope='Symmetric/ramp prescribed backgrounds, even N>=16; configured temperature, field and strain.',
                                scope='Frozen prescribed occupancy, evolving normalized probability. Smooth reference sets m_pi=0; finite test grids retain parity.'), arrays)


class HiddenStateStudy:
    """Demonstrate why mean occupancy and recoverability omit direction.

    This small deterministic illustration complements the larger synthetic risk
    ensembles retained in the original notebook; it is not their replacement.
    """

    def run(self) -> StudyResult:
        """Propagate reflected profiles under the same field-only generator.

        Returns:
            Equal mean and entropy diagnostics with distinct directed future
            centroids, labelled as a synthetic illustration.
        """
        n = 32
        x = (np.arange(n) + .5) / n
        c = .2 + .2 * x
        model = TransportModel()
        generator = model.freeze(c, structure_conditioned=False)
        duration = .08 * model.config.length_m**2 / model.config.diffusivity_m2_s
        rows = []
        for name, initial in [('ramp', c), ('reflection', c[::-1])]:
            p = generator.propagate(initial / initial.sum(), duration)
            rows.append(dict(state=name, mean=float(initial.mean()),
                             recoverability=RecoverabilityDiagnostic.evaluate(initial),
                             initial_centroid=RecoverabilityDiagnostic.directed_moments(initial)['centroid'],
                             future_centroid=float(x @ p)))
        return StudyResult('hidden_state', dict(reflected_pair=pd.DataFrame(rows)),
                           dict(scope='Synthetic reflected-pair illustration, field-only frozen propagator; not a new experimental sample or a fitted risk score.'))


class ContinuumStudy:
    """Constant-field, spatially constant-D benchmark from v3.1 section 9.

    This study is distinct from the structure-dependent R3 refinement audit.
    The representative occupancy is fixed at 0.30 only to select diffusivity.
    """

    def run(self) -> StudyResult:
        """Compare the matched exponential-rate generator on five mesh sizes.

        Returns:
            Relative errors against N=512, fitted order using N<=128, the
            mesh-independent gap bound, and discrete entropy/mass checks.
        """
        base = TransportModel()
        cfg, st = base.config, base.structure
        deff = cfg.diffusivity_m2_s * np.exp(-cfg.chi_transport * st.e_a * .3 / (KB_EV_K * cfg.temperature_k))
        model = TransportModel(replace(cfg, diffusivity_m2_s=float(deff)))
        duration = .08 * cfg.length_m**2 / deff
        bound = deff * np.pi**2 / cfg.length_m**2 * np.exp(-cfg.field_v_m * cfg.length_m / (KB_EV_K * cfg.temperature_k))

        def evolve(n: int) -> tuple[np.ndarray, FrozenGenerator]:
            """Propagate the matched equilibrium-weighted initial condition."""
            generator = model.freeze(np.full(n, .3), structure_conditioned=False)
            x = (np.arange(n) + .5) / n
            p0 = generator.stationary * (1 + .2 * np.cos(np.pi * x))
            p0 /= p0.sum()
            return generator.propagate(p0, duration), generator

        reference, _ = evolve(512)
        rows = []
        for n in (16, 32, 64, 128, 256):
            p, generator = evolve(n)
            average = reference.reshape(n, -1).sum(1)
            audit = generator.audit()
            rows.append(dict(N=n, h_m=cfg.length_m / n,
                             relative_L2_error=float(np.linalg.norm(p - average) / np.linalg.norm(average)),
                             weighted_gap_s_1=audit['gap_s_1'], gap_bound_ratio=audit['gap_s_1'] / bound,
                             mass_error=float(abs(p.sum() - 1))))
        table = pd.DataFrame(rows)
        fit_rows = table[table.N <= 128]
        order = float(np.polyfit(np.log(fit_rows.h_m), np.log(fit_rows.relative_L2_error), 1)[0])
        _, generator = evolve(64)
        p = generator.stationary * (1 + .3 * np.sin(2 * np.pi * (np.arange(64) + .5) / 64))
        p /= p.sum()
        entropy_derivative = float((generator.matrix @ p) @ np.log(p / generator.stationary))
        return StudyResult('continuum', dict(convergence=table),
                           dict(observed_order=order, D_eff_m2_s=float(deff), uniform_gap_lower_s_1=float(bound),
                                entropy_derivative_s_1=entropy_derivative,
                                scope='Constant-field, spatially constant-D benchmark. Does not establish order two for the mesh-staggered full generator.'))
