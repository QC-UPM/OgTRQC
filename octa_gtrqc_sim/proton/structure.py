"""Dimensioned two-mode structural free energy (paper sections 2.4--2.5)."""

from dataclasses import dataclass
import numpy as np
from scipy.constants import atomic_mass, elementary_charge, speed_of_light


@dataclass(frozen=True)
class StructuralModel:
    """Literature-constrained local cage and mesh-staggered breathing model.

    Attributes:
        bond_length_a: Reference Ni--O bond length in angstroms.
        volume_expansion: Fractional local cage expansion at unit occupancy.
        frequency_cm: Effective cage spectral prior in inverse centimetres.
        q_r_bulk_a: Bulk breathing amplitude in angstroms.
        breathing_curvature: Zero-strain [001] curvature in meV per formula
            unit per squared percent of bulk amplitude.

    Notes:
        The retained positive Hessian does not establish stability of omitted
        tilt, polar, or Jahn--Teller modes. The alternating device-cell closure
        is a mesh-defined proxy, not an identified crystallographic order.
    """

    bond_length_a: float = 1.942
    volume_expansion: float = 0.12
    frequency_cm: float = 420.
    q_r_bulk_a: float = 0.06
    breathing_curvature: float = 0.0066

    def __post_init__(self) -> None:
        """Require finite positive physical priors for both retained modes."""
        values = np.array(list(self.__dict__.values()))
        if not np.isfinite(values).all() or np.any(values <= 0):
            raise ValueError('Structural calibration inputs must be finite and positive.')

    @property
    def k_a(self) -> float:
        """float: Uniform cage stiffness in eV/angstrom squared."""
        omega = 2 * np.pi * speed_of_light * self.frequency_cm * 100
        return float(15.999 * atomic_mass * omega**2 / (elementary_charge / 1e-20))

    @property
    def k_r(self) -> float:
        """float: Reference breathing stiffness in eV/angstrom squared."""
        return 20 * self.breathing_curvature / self.q_r_bulk_a**2

    @property
    def q_a_unit(self) -> float:
        """float: Equilibrium cage coordinate at unit occupancy in angstroms."""
        return float(np.sqrt(6) * self.bond_length_a * ((1 + self.volume_expansion)**(1 / 3) - 1))

    @property
    def e_a(self) -> float:
        """float: Uniform cage relaxation energy in eV."""
        return 0.5 * self.k_a * self.q_a_unit**2

    @property
    def e_r(self) -> float:
        """float: Breathing relaxation energy in eV per formula unit."""
        return 0.5 * self.k_r * self.q_r_bulk_a**2

    @property
    def hessian(self) -> np.ndarray:
        """numpy.ndarray: Two-mode reference Hessian in eV/angstrom squared."""
        return np.diag([self.k_a, self.k_r])

    @staticmethod
    def validate_profile(profile: np.ndarray) -> np.ndarray:
        """Validate a finite, nonempty one-dimensional occupancy profile.

        Args:
            profile: Mean proton occupancies, each in the interval [0, 1].

        Returns:
            Float array of occupancies.

        Raises:
            ValueError: If the input is empty, nonfinite, or outside [0, 1].
        """
        c = np.asarray(profile, dtype=float)
        if c.ndim != 1 or c.size == 0 or not np.isfinite(c).all() or np.any((c < 0) | (c > 1)):
            raise ValueError('Occupancy must be a nonempty finite vector in [0, 1].')
        return c

    def equilibrium(self, profile: np.ndarray) -> tuple[np.ndarray, float]:
        """Compute the occupancy-conditioned minimizers of structural energy.

        Args:
            profile: Mean occupancies; donated-electron count equals occupancy.

        Returns:
            Local cage coordinates and the mesh-staggered coordinate, both in
            angstroms. The empty-proton configuration has zero breathing order.
        """
        c = self.validate_profile(profile)
        order = abs((-1.)**np.arange(c.size) @ c) / max(float(c.sum()), 1e-15)
        return self.q_a_unit * c, float(self.q_r_bulk_a * order)

    def free_energy(self, profile: np.ndarray, q_a: np.ndarray, q_r: float) -> float:
        """Evaluate equation (25) without any recoverability dependence.

        Args:
            profile: Mean proton occupancies.
            q_a: One radial coordinate per cell, in angstroms.
            q_r: Shared mesh-staggered breathing coordinate, in angstroms.

        Returns:
            Structural free energy in eV for the entire device mesh.
        """
        c = self.validate_profile(profile)
        qa_star, qr_star = self.equilibrium(c)
        qa = np.asarray(q_a, dtype=float)
        if qa.shape != c.shape or not np.isfinite(qa).all() or not np.isfinite(q_r):
            raise ValueError('Structural coordinates must be finite and match the mesh.')
        return float(np.sum(0.5 * self.k_a * qa**2 - self.k_a * qa_star * qa)
                     + c.size * (0.5 * self.k_r * q_r**2 - self.k_r * qr_star * q_r))

    def forces(self, profile: np.ndarray, q_a: np.ndarray, q_r: float) -> tuple[np.ndarray, float]:
        """Return negative energy gradients, with breathing force per cell.

        Args:
            profile: Mean proton occupancies.
            q_a: Local cage coordinates in angstroms.
            q_r: Shared breathing coordinate in angstroms.

        Returns:
            Local cage forces and breathing force per cell, in eV/angstrom.
        """
        self.free_energy(profile, q_a, q_r)  # shared input validation
        qa_star, qr_star = self.equilibrium(profile)
        return -self.k_a * (np.asarray(q_a) - qa_star), -self.k_r * (q_r - qr_star)
