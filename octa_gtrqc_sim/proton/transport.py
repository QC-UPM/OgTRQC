"""Frozen, structure-conditioned column generators with local detailed balance.

No concentration-to-polarization observation map is assumed. Probability
propagation is a frozen linear benchmark, not nonlinear occupancy evolution.
"""

from dataclasses import dataclass
import numpy as np
from scipy.constants import Boltzmann, elementary_charge
from scipy.linalg import eigh_tridiagonal
from scipy.sparse import diags, csc_matrix
from scipy.sparse.linalg import expm_multiply

from octa_gtrqc_sim.proton.structure import StructuralModel

KB_EV_K = Boltzmann / elementary_charge


@dataclass(frozen=True)
class DeviceConfig:
    """Dimensioned device parameters independent of the relaxation fit.

    Attributes:
        length_m: One-dimensional device length in metres.
        temperature_k: Temperature in kelvin.
        field_v_m: Constant longitudinal electric field in volts/metre.
        diffusivity_m2_s: Reference diffusivity at 300 K in square metres/second.
        activation_ev: Arrhenius migration energy in eV.
        strain: Dimensionless imposed strain, within the declared ±3% range.
        chi_transport: Explicit conditional barrier coefficient. Its nominal
            value transfers a relaxation fit; it is not independently calibrated.
    """

    length_m: float = 100e-9
    temperature_k: float = 300.
    field_v_m: float = 2e5
    diffusivity_m2_s: float = float(np.sqrt(6e-19 * 3e-18))
    activation_ev: float = 0.41
    strain: float = 0.
    chi_transport: float = 0.9698094585796684

    def __post_init__(self) -> None:
        """Reject nonphysical or out-of-scope numerical parameters."""
        vals = np.array(list(self.__dict__.values()))
        if not np.isfinite(vals).all() or min(self.length_m, self.temperature_k, self.diffusivity_m2_s) <= 0:
            raise ValueError('Device values must be finite; length, temperature, and diffusivity positive.')
        if self.activation_ev < 0 or self.chi_transport < 0 or abs(self.strain) > .03:
            raise ValueError('Use nonnegative barriers and imposed strain within [-0.03, 0.03].')


@dataclass(frozen=True)
class FrozenGenerator:
    """Tridiagonal reversible generator and its structural background.

    Attributes:
        forward: Rates from cell i to i+1 in inverse seconds.
        reverse: Rates from cell i+1 to i in inverse seconds.
        potential_ev: Site energies in eV.
        edge_diffusivity: Edge diffusivities in square metres/second.
        q_a: Occupancy-conditioned cage coordinates in angstroms.
        q_r: Mesh-staggered breathing coordinate in angstroms.
        config: Device parameters used to construct these frozen coefficients.
    """

    forward: np.ndarray
    reverse: np.ndarray
    potential_ev: np.ndarray
    edge_diffusivity: np.ndarray
    q_a: np.ndarray
    q_r: float
    config: DeviceConfig

    @property
    def diagonal(self) -> np.ndarray:
        """numpy.ndarray: Negative outgoing rates of the column generator."""
        d = np.zeros(self.potential_ev.size)
        d[:-1] -= self.forward
        d[1:] -= self.reverse
        return d

    @property
    def matrix(self) -> csc_matrix:
        """scipy.sparse.csc_matrix: Sparse matrix Q satisfying dp/dt = Qp."""
        return diags([self.reverse, self.diagonal, self.forward], [1, 0, -1], format='csc')

    @property
    def stationary(self) -> np.ndarray:
        """numpy.ndarray: Normalized Boltzmann stationary probability."""
        logw = -self.potential_ev / (KB_EV_K * self.config.temperature_k)
        weights = np.exp(logw - logw.max())
        return weights / weights.sum()

    def propagate(self, probability: np.ndarray, duration_s: float) -> np.ndarray:
        """Evolve a normalized probability under unchanged coefficients.

        Args:
            probability: Nonnegative initial probability with unit total mass.
            duration_s: Nonnegative propagation duration in seconds.

        Returns:
            Probability from the sparse matrix exponential. No clipping or
            renormalization masks mass-conservation errors.

        Raises:
            ValueError: If probability shape, normalization, or time is invalid.
        """
        p = np.asarray(probability, dtype=float)
        if (p.shape != self.potential_ev.shape or not np.isfinite(p).all()
                or np.any(p < 0) or not np.isclose(p.sum(), 1., atol=1e-12, rtol=0)
                or not np.isfinite(duration_s) or duration_s < 0):
            raise ValueError('Expected normalized finite probability and nonnegative finite time.')
        return expm_multiply(self.matrix * duration_s, p)

    def audit(self) -> dict[str, float]:
        """Check conservation, reversibility, gap bound, and entropy dissipation.

        Returns:
            Numerical residuals, positive spectral gap and lower bound in
            inverse seconds, and entropy derivative at the notebook's probe.
            The checks concern a frozen generator, not nonlinear convergence.
        """
        n = len(self.potential_ev)
        beta = 1 / (KB_EV_K * self.config.temperature_k)
        pi = self.stationary
        if np.any(pi == 0):
            raise ValueError('Stationary distribution underflows at this field/temperature.')
        eigs = eigh_tridiagonal(-self.diagonal, -np.sqrt(self.forward * self.reverse),
                               select='i', select_range=(0, 1), eigvals_only=True)
        x = (np.arange(n) + .5) / n
        p = .15 + .7 * np.exp(-((x - .35) / .18)**2)
        p /= p.sum()
        q = self.matrix
        scale = max(float(np.max(abs(self.diagonal))), 1e-300)
        bound = (4 * self.edge_diffusivity.min() / (self.config.length_m / n)**2
                 * np.sin(np.pi / (2 * n))**2 * np.exp(-beta * np.ptp(self.potential_ev)))
        return dict(gap_s_1=float(eigs[1]), lower_bound_s_1=float(bound),
                    entropy_derivative_s_1=float((q @ p) @ np.log(p / pi)),
                    db_residual=float(np.max(abs(np.log(self.forward / self.reverse)
                                                 + beta * np.diff(self.potential_ev)))),
                    relative_column_residual=float(np.max(abs(np.asarray(q.sum(axis=0)))) / scale),
                    relative_stationarity_error=float(np.linalg.norm(q @ pi) / scale),
                    D_min=float(self.edge_diffusivity.min()), D_max=float(self.edge_diffusivity.max()),
                    Q_R_A=self.q_r)


class TransportModel:
    """Construct paper generators from occupancy and explicit device parameters.

    Args:
        config: Device geometry, forcing, temperature, and barrier coefficient.
        structure: Optional two-mode structural model.

    Attributes:
        config: Immutable device configuration.
        structure: Structural free-energy model.
    """

    def __init__(self, config: DeviceConfig | None = None, structure: StructuralModel | None = None) -> None:
        """Store independent physical configuration and structural priors.

        Args:
            config: Immutable device parameters, or the paper defaults.
            structure: Optional calibrated two-mode structural model.
        """
        self.config = config or DeviceConfig()
        self.structure = structure or StructuralModel()

    def freeze(self, profile: np.ndarray, *, smooth_limit: bool = False,
               structure_conditioned: bool = True) -> FrozenGenerator:
        """Construct local-detailed-balance rates for a prescribed background.

        Args:
            profile: Mean occupancy per coarse device cell; at least two cells.
            smooth_limit: Set only mesh-staggered order to zero for the R3
                smooth-reference comparison. Finite-mesh tests keep it enabled.
            structure_conditioned: Include cage and breathing site energies and
                barriers. False selects the spatially constant-D field benchmark.

        Returns:
            Frozen reversible generator with reflecting end boundaries.

        Raises:
            ValueError: If the mesh is too small or rates overflow/underflow.
        """
        c = self.structure.validate_profile(profile)
        if c.size < 2:
            raise ValueError('Transport requires at least two cells.')
        c = np.clip(c, 1e-12, 1 - 1e-12)  # original notebook convention
        cfg, st = self.config, self.structure
        qa, qr = st.equilibrium(c)
        if smooth_limit:
            qr = 0.
        signs = (-1.)**np.arange(c.size)
        h = cfg.length_m / c.size
        x = (np.arange(c.size) + .5) * h
        beta = 1 / (KB_EV_K * cfg.temperature_k)
        dref = cfg.diffusivity_m2_s * np.exp(-cfg.activation_ev / KB_EV_K * (1 / cfg.temperature_k - 1 / 300.))
        u = -cfg.field_v_m * x
        barrier = np.zeros(c.size - 1)
        if structure_conditioned:
            order = qr / st.q_r_bulk_a
            u = u - .20 * st.e_a * (qa / st.q_a_unit) - .10 * st.e_r * order * signs
            barrier = (cfg.chi_transport * st.e_a * .5 * (qa[:-1] + qa[1:]) / st.q_a_unit
                       + .20 * st.e_r * order + .15 * st.e_a * cfg.strain / .01)
        de = dref * np.exp(-beta * barrier)
        forward = de / h**2 * np.exp(-.5 * beta * np.diff(u))
        reverse = de / h**2 * np.exp(.5 * beta * np.diff(u))
        if not np.isfinite(np.r_[forward, reverse]).all() or min(forward.min(), reverse.min()) <= 0:
            raise ValueError('Rates are outside floating-point range for these parameters.')
        return FrozenGenerator(forward, reverse, u, de, qa, qr, cfg)
