"""Read-only state-sufficiency diagnostics, independent of physical evolution."""

import numpy as np
from scipy.special import xlogy
from octa_gtrqc_sim.proton.structure import StructuralModel


class RecoverabilityDiagnostic:
    """Bernoulli relative entropy under projection to mean occupancy.

    This diagnostic is dimensionless (nats per site). It supplies no forces,
    hopping rates, current, or closure of unresolved kinetic state.
    """

    @staticmethod
    def evaluate(profile: np.ndarray) -> float:
        """Evaluate equation (10), including uniform endpoint profiles.

        Args:
            profile: Mean site occupancies in [0, 1].

        Returns:
            Nonnegative information loss in nats per site. Uniform zero and
            uniform one profiles return zero by continuity.
        """
        c = StructuralModel.validate_profile(profile)
        mean = float(c.mean())
        if mean == 0 or mean == 1:
            return 0.
        value = xlogy(c, c / mean) + xlogy(1 - c, (1 - c) / (1 - mean))
        return max(0., float(value.mean()))

    @staticmethod
    def directed_moments(profile: np.ndarray) -> dict[str, float]:
        """Measure directional information discarded by the mean projection.

        Args:
            profile: Occupancies on equally spaced cell centres.

        Returns:
            Dimensionless centroid, variance, and skewness. Empty-proton
            profiles use the notebook's zero-mass regularization.
        """
        c = StructuralModel.validate_profile(profile)
        x = (np.arange(c.size) + 0.5) / c.size
        mass = max(float(c.sum()), 1e-15)
        centroid = float(x @ c / mass)
        variance = float((x - centroid)**2 @ c / mass)
        skewness = float((x - centroid)**3 @ c / mass / (variance**1.5 + 1e-15))
        return dict(centroid=centroid, variance=variance, skewness=skewness)
