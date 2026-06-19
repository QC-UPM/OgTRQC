"""Relaxed Quantum Memory Integrator module for Octahedral gTRQC Simulation.

This module implements a rigorous von Neumann integration with endogenous 
recoverability loss calculation via relative entropy and Kraus operators.
"""

import math
from typing import Dict, Any
import numpy as np
from dataclasses import asdict
from octa_gtrqc_sim.material_register import MaterialRegister


class RelaxedQuantumModel:
    """Rigorous quantum execution framework with endogenous recoverability.

    Models the 2x2 density matrix evolution explicitly calculating information 
    loss using relative entropy against a reference thermal shadow state, 
    and applying geometric strain via a positive elastic operator.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initializes the quantum space, Kraus operators, and elastic tensors.

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
        
        self.rho_matrix = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
        self.rho_shadow = np.array([[0.5, 0.0], [0.0, 0.5]], dtype=complex)
        self.rho_scalar = float(config.get("initial_rho", 1.0))
        
        base_stiffness = float(config.get("g_oct_stiffness", 3.5))
        self.g_oct_operator = np.diag([base_stiffness, base_stiffness * 1.2, base_stiffness * 0.8])
        
        self.op_ni_z = np.array([[1, 0], [0, -1]], dtype=complex)
        self.op_ni_x = np.array([[0, 1], [1, 0]], dtype=complex)
        
        gamma = 0.05
        self.kraus_0 = np.sqrt(1 - gamma) * np.eye(2, dtype=complex)
        self.kraus_1 = np.sqrt(gamma) * self.op_ni_z

    def _matrix_log(self, mat: np.ndarray, eps: float = 1e-9) -> np.ndarray:
        """Computes the matrix logarithm using eigendecomposition.

        Args:
            mat (np.ndarray): Hermitian positive semi-definite matrix.
            eps (float): Small epsilon to prevent logarithmic divergence.

        Returns:
            np.ndarray: Evaluated matrix logarithm.
        """
        evals, evecs = np.linalg.eigh(mat)
        evals = np.maximum(evals, eps)
        return evecs @ np.diag(np.log(evals)) @ evecs.conj().T

    def _relative_entropy(self, rho: np.ndarray, sigma: np.ndarray) -> float:
        """Calculates von Neumann relative entropy between two density matrices.

        Args:
            rho (np.ndarray): Current physical state matrix.
            sigma (np.ndarray): Reference or shadow state matrix.

        Returns:
            float: Evaluated relative entropy representing information loss.
        """
        log_rho = self._matrix_log(rho)
        log_sigma = self._matrix_log(sigma)
        entropy = np.real(np.trace(rho @ (log_rho - log_sigma)))
        return max(0.0, float(entropy))

    def step(self, V_t: float, delta_0_external: float) -> Dict[str, float]:
        """Evaluates one discrete step computing endogenous recoverability loss.

        Args:
            V_t (float): Externally applied time-dependent driving potential voltage.
            delta_0_external (float): Ignored external proxy, maintained for interface compatibility.

        Returns:
            Dict[str, float]: Dictionary containing computed metrics at current frame.
        """
        dt = 0.1
        hamiltonian = V_t * self.op_ni_z
        
        commutator = hamiltonian @ self.rho_matrix - self.rho_matrix @ hamiltonian
        rho_unitary = self.rho_matrix - 1j * dt * commutator
        
        self.rho_matrix = self.kraus_0 @ rho_unitary @ self.kraus_0.conj().T + \
                          self.kraus_1 @ rho_unitary @ self.kraus_1.conj().T
        
        trace = np.real(np.trace(self.rho_matrix))
        if trace > 0.0:
            self.rho_matrix = self.rho_matrix / trace
            
        endogenous_delta = self._relative_entropy(self.rho_matrix, self.rho_shadow)
        
        geom_vector = np.array([self.k_0.theta_tilt, self.k_0.theta_rot, self.k_0.delta_V_oct])
        force_vector = endogenous_delta * (self.g_oct_operator @ geom_vector)
        
        delta_k = -force_vector * dt
        self.k_0.theta_tilt += delta_k[0]
        self.k_0.theta_rot += delta_k[1]
        self.k_0.delta_V_oct += delta_k[2]
        
        structural_distortion = sum(abs(x) for x in self.k_0.to_vector()[:3])
        self.rho_scalar = float(np.real(np.trace(self.rho_matrix @ self.op_ni_x)))
        
        return {
            "rho": self.rho_scalar,
            "distortion": float(structural_distortion),
            "endogenous_delta": endogenous_delta
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
        """Fetches complete structured inner representations.

        Returns:
            Dict[str, Any]: State snapshot mapping dictionary.
        """
        return {
            "rho": self.rho_scalar,
            "register": asdict(self.k_0)
        }
