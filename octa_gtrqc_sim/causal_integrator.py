"""Causal Sufficiency Integrator module for Octahedral gTRQC Simulation.

This module provides a fully autonomous, expanded Hilbert space execution framework.
It tracks both Nickel electronic states and Hydrogen protonic polarons explicitly,
eliminating artificial history buffers and achieving causal sufficiency.
"""

import math
from typing import Dict, Any
import numpy as np
from dataclasses import asdict
from octa_gtrqc_sim.material_register import MaterialRegister


class CausalSufficiencyModel:
    """Rigorous expanded quantum execution framework for causal autonomy.

    Models the 4x4 density matrix evolution of the combined electron-proton 
    tensor space. Geometric backreaction is driven instantaneously by the 
    explicit expectation value of the protonic degrees of freedom.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initializes the expanded quantum space and structural operators.

        Args:
            config (Dict[str, Any]): Dictionary containing configuration variables.
        """
        reg_conf = config.get("initial_register", {})
        self.k_0 = MaterialRegister(
            theta_tilt=float(reg_conf.get("theta_tilt", 0.1)),
            theta_rot=float(reg_conf.get("theta_rot", 0.05)),
            delta_V_oct=float(reg_conf.get("delta_V_oct", 0.0)),
            delta_phi=float(reg_conf.get("delta_phi", 0.02)),
            epsilon_0=float(reg_conf.get("epsilon_0", 1.0))
        )
        
        self.rho_matrix: np.ndarray = np.zeros((4, 4), dtype=complex)
        self.rho_matrix[0, 0] = 1.0
        
        self.rho_scalar: float = float(config.get("initial_rho", 1.0))
        self.g_oct: float = float(config.get("g_oct_stiffness", 2.5))
        
        self.proton_hopping: float = 0.5
        self.electron_proton_coupling: float = 1.2
        
        sz = np.array([[1, 0], [0, -1]], dtype=complex)
        sx = np.array([[0, 1], [1, 0]], dtype=complex)
        id2 = np.eye(2, dtype=complex)
        
        self.op_ni_z = np.kron(sz, id2)
        self.op_ni_x = np.kron(sx, id2)
        self.op_h_z = np.kron(id2, sz)
        self.op_h_x = np.kron(id2, sx)
        self.op_interaction = np.kron(sz, sz)

    def step(self, V_t: float, delta_0: float) -> Dict[str, float]:
        """Evaluates one discrete step delta_t of the causally sufficient system.

        Solves the autonomous von Neumann integration over the expanded 4x4 space
        and derives instantaneous geometric strain from the latent protonic distribution.

        Args:
            V_t (float): Externally applied time-dependent driving potential voltage.
            delta_0 (float): Recoverability loss proxy value.

        Returns:
            Dict[str, float]: Dictionary containing computed metrics at current frame.
        """
        dt = 0.1
        
        h_ni = V_t * self.op_ni_z
        h_h = self.proton_hopping * self.op_h_x
        h_int = self.electron_proton_coupling * self.op_interaction
        
        h_total = h_ni + h_h + h_int
        
        commutator = h_total @ self.rho_matrix - self.rho_matrix @ h_total
        self.rho_matrix = self.rho_matrix - 1j * dt * commutator
        
        trace = np.real(np.trace(self.rho_matrix))
        if trace > 0.0:
            self.rho_matrix = self.rho_matrix / trace
            
        proton_expectation = np.real(np.trace(self.rho_matrix @ self.op_h_z))
        
        raw_source = delta_0 * self.g_oct
        j_eff = proton_expectation * raw_source
        j_0 = j_eff * sum(self.k_0.to_vector())
        
        delta_k = - (j_0 / (self.g_oct + 1e-9)) * dt
        
        self.k_0.theta_tilt += delta_k * 0.1
        self.k_0.theta_rot += delta_k * 0.05
        self.k_0.delta_V_oct += delta_k * 0.2
        
        structural_distortion = sum(abs(x) for x in self.k_0.to_vector()[:3])
        
        conductance = np.real(np.trace(self.rho_matrix @ self.op_ni_x))
        self.rho_scalar = float(conductance)
        
        return {
            "rho": self.rho_scalar,
            "distortion": float(structural_distortion),
            "raw_source": float(raw_source),
            "j_eff": float(j_eff),
            "j_0": float(j_0)
        }

    def calculate_capacity(self, epsilon: float) -> float:
        """Calculates Kolmogorov-Tikhomirov capacity.

        Args:
            epsilon (float): Resolution bound metrics parameter.

        Returns:
            float: Evaluated atomic information capacity value.
        """
        if epsilon <= 0:
            epsilon = 1e-4
        n_epsilon = max(1, int(1.0 / (epsilon * (1.0 + abs(self.rho_scalar)))))
        return math.log(n_epsilon)

    def get_state(self) -> Dict[str, Any]:
        """Fetches complete structured inner representations without history buffers.

        Returns:
            Dict[str, Any]: State snapshot mapping dictionary.
        """
        return {
            "rho": self.rho_scalar,
            "register": asdict(self.k_0),
            "buffer": [] 
        }
