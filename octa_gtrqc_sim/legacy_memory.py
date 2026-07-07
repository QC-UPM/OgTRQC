"""Legacy scalar memory engine for the octahedral gTRQC proof of concept."""

from __future__ import annotations

import math
from dataclasses import asdict
from typing import Any, Dict, List

from octa_gtrqc_sim.material_register import MaterialRegister


class OctaMemoryModel:
    """Scalar proxy execution framework for the octahedral memory benchmark.

    This engine keeps the original proof-of-concept structure: a scalar matter
    observable, a finite octahedral register, and an explicit delayed source
    buffer. It is intentionally lightweight and therefore useful as a reference
    engine when validating delay-aware workflows.

    Args:
        config: Runtime configuration dictionary.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize the scalar proxy state and delayed source buffer.

        Args:
            config: Runtime configuration dictionary.
        """
        reg_conf = config.get("initial_register", {})
        self.k_0 = MaterialRegister(
            theta_tilt=float(reg_conf.get("theta_tilt", 0.1)),
            theta_rot=float(reg_conf.get("theta_rot", 0.05)),
            delta_V_oct=float(reg_conf.get("delta_V_oct", 0.0)),
            delta_phi=float(reg_conf.get("delta_phi", 0.02)),
            epsilon_0=float(reg_conf.get("epsilon_0", 1.0)),
        )
        self.rho: float = float(config.get("initial_rho", 1.0))
        self.g_oct: float = float(config.get("g_oct_stiffness", 2.5))
        self.delay: int = max(0, int(config.get("protonic_delay_steps", 2)))
        self.delay_buffer: List[float] = [0.0] * self.delay
        self.hilbert_dimension_label = "scalar_proxy"

    def step(self, V_t: float, delta_0: float) -> Dict[str, float]:
        """Advance the scalar proxy state by one discrete step.

        Args:
            V_t: Applied voltage at the current step.
            delta_0: Recoverability-loss proxy.

        Returns:
            Dictionary containing scalar observables for the current step.
        """
        raw_source = delta_0 * self.g_oct
        self.delay_buffer.append(raw_source)
        j_eff = self.delay_buffer.pop(0) if self.delay_buffer else raw_source

        j_0 = j_eff * sum(self.k_0.to_vector())

        delta_k = -j_0 / (self.g_oct + 1e-9)
        self.k_0.theta_tilt += delta_k * 0.1
        self.k_0.theta_rot += delta_k * 0.05
        self.k_0.delta_V_oct += delta_k * 0.2

        structural_distortion = sum(abs(x) for x in self.k_0.to_vector()[:3])
        interaction_hamiltonian = 0.5 * V_t - 0.2 * structural_distortion
        self.rho = max(0.0, min(1.0, self.rho - 0.05 * interaction_hamiltonian + 0.01 * j_eff))

        return {
            "rho": self.rho,
            "distortion": structural_distortion,
            "raw_source": raw_source,
            "j_eff": j_eff,
            "j_0": j_0,
        }

    def estimate_resolution_heuristic(self, epsilon: float) -> float:
        """Estimate the heuristic resolution indicator.

        Args:
            epsilon: Resolution threshold.

        Returns:
            Heuristic resolution indicator.
        """
        if epsilon <= 0:
            epsilon = 1e-4
        n_epsilon = max(1, int(1.0 / (epsilon * (1.0 + abs(self.rho)))))
        return math.log(n_epsilon)

    def calculate_capacity(self, epsilon: float) -> float:
        """Backward-compatible alias for the heuristic resolution estimate.

        Args:
            epsilon: Resolution threshold.

        Returns:
            Heuristic resolution indicator.
        """
        return self.estimate_resolution_heuristic(epsilon)

    def get_state(self) -> Dict[str, Any]:
        """Return the current scalar-proxy state snapshot.

        Returns:
            Dictionary with the current matter, register, and delay-buffer state.
        """
        return {
            "rho": self.rho,
            "register": asdict(self.k_0),
            "buffer": list(self.delay_buffer),
        }
