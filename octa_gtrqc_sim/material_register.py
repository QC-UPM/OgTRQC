"""Material geometry register definition module.

Provides the core data structure for the octahedral geometry
tracker across all simulation engines.
"""

from dataclasses import dataclass
from typing import List

@dataclass
class MaterialRegister:
    """Represents the material octahedral curvature surrogate register vector.

    Attributes:
        theta_tilt (float): Octahedral tilting angle component.
        theta_rot (float): Octahedral rotation angle component.
        delta_V_oct (float): Local discrete change in octahedral cage volume.
        delta_phi (float): Deviation of the internal Ni-O-Ni bond angle.
        epsilon_0 (float): Baseline energy profile parameter.
    """
    theta_tilt: float
    theta_rot: float
    delta_V_oct: float
    delta_phi: float
    epsilon_0: float

    def to_vector(self) -> List[float]:
        """Flattens the register parameters into a mathematical float vector.

        Returns:
            List[float]: Vector list representing localized geometry configurations.
        """
        return [self.theta_tilt, self.theta_rot, self.delta_V_oct, self.delta_phi, self.epsilon_0]


