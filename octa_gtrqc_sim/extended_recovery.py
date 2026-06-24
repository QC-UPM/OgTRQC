"""Extended 8x8 Integration Models for Octahedral gTRQC Simulation.

This module provides high-dimensionality extensions for both the causal
and quantum relaxed frameworks, evaluating a tripartite quantum system
consisting of one Nickel electron and two Hydrogen interstitial sites.
"""

import math
from typing import Dict, Any
import numpy as np
from dataclasses import asdict
from octa_gtrqc_sim.material_register import MaterialRegister


class ExtendedRelaxedCausalModel:
    """Rigorous 8x8 expanded quantum framework for causal autonomy.

    Models the evolution strictly using exact unitary transformations
    across three subsystems, deriving recoverability loss entirely from
    the partial trace over the two unobservable hydrogen sites.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        reg_conf = config.get("initial_register", {})
        self.k_0 = MaterialRegister(
            theta_tilt=float(reg_conf.get("theta_tilt", 0.1)),
            theta_rot=float(reg_conf.get("theta_rot", 0.05)),
            delta_V_oct=float(reg_conf.get("delta_V_oct", 0.0)),
            delta_phi=float(reg_conf.get("delta_phi", 0.02)),
            epsilon_0=float(reg_conf.get("epsilon_0", 1.0))
        )
        
        self.rho_matrix = np.zeros((8, 8), dtype=complex)
        self.rho_matrix[0, 0] = 1.0
        
        self.h_reference = 0.25 * np.eye(4, dtype=complex)
        self.rho_scalar = float(config.get("initial_rho", 1.0))
        
        base_stiffness = float(config.get("g_oct_stiffness", 3.5))
        self.g_oct_operator = np.diag([base_stiffness, base_stiffness * 1.2, base_stiffness * 0.8])
        
        # Load interaction parameters dynamically from configuration
        self.proton_hopping = float(config.get("proton_hopping_energy", 0.5))
        self.proton_hopping_inter = float(config.get("inter_site_hopping", 0.2))
        self.electron_proton_coupling = float(config.get("electron_proton_coupling", 1.2))
        self.ni_transverse_hopping = float(config.get("ni_transverse_hopping", 0.8)) # New parameter
        
        sz = np.array([[1, 0], [0, -1]], dtype=complex)
        sx = np.array([[0, 1], [1, 0]], dtype=complex)
        id2 = np.eye(2, dtype=complex)
        id4 = np.eye(4, dtype=complex)
        
        self.op_ni_z = np.kron(sz, id4)
        self.op_ni_x = np.kron(sx, id4)
        
        self.op_h1_x = np.kron(id2, np.kron(sx, id2))
        self.op_h2_x = np.kron(id2, np.kron(id2, sx))
        self.op_hopping_h1_h2 = np.kron(id2, np.kron(sx, sx))
        
        self.op_interaction_1 = np.kron(sz, np.kron(sz, id2))
        self.op_interaction_2 = np.kron(sz, np.kron(id2, sz))

    def _matrix_log(self, mat: np.ndarray, eps: float = 1e-9) -> np.ndarray:
        evals, evecs = np.linalg.eigh(mat)
        evals = np.maximum(evals, eps)
        return evecs @ np.diag(np.log(evals)) @ evecs.conj().T

    def _exact_unitary_operator(self, hamiltonian: np.ndarray, dt: float) -> np.ndarray:
        evals, evecs = np.linalg.eigh(hamiltonian)
        unitary_diag = np.diag(np.exp(-1j * dt * evals))
        return evecs @ unitary_diag @ evecs.conj().T

    def _relative_entropy(self, rho: np.ndarray, sigma: np.ndarray) -> float:
        log_rho = self._matrix_log(rho)
        log_sigma = self._matrix_log(sigma)
        entropy = np.real(np.trace(rho @ (log_rho - log_sigma)))
        return max(0.0, float(entropy))

    def _partial_trace_hydrogens(self, rho_8x8: np.ndarray) -> np.ndarray:
        rho_reshaped = rho_8x8.reshape((2, 2, 2, 2, 2, 2))
        trace_h2 = np.trace(rho_reshaped, axis1=2, axis2=5)
        trace_h1_h2 = np.trace(trace_h2, axis1=1, axis2=3)
        return trace_h1_h2

    def step(self, V_t: float, delta_0_external: float) -> Dict[str, float]:
        dt = 0.1
        
        # Hamiltonian now includes transverse hopping for the Nickel subsystem
        h_total = (V_t * self.op_ni_z + 
                   self.ni_transverse_hopping * self.op_ni_x +
                   self.proton_hopping * (self.op_h1_x + self.op_h2_x) + 
                   self.proton_hopping_inter * self.op_hopping_h1_h2 +
                   self.electron_proton_coupling * (self.op_interaction_1 + self.op_interaction_2))
        
        unitary_op = self._exact_unitary_operator(h_total, dt)
        self.rho_matrix = unitary_op @ self.rho_matrix @ unitary_op.conj().T
        
        trace = np.real(np.trace(self.rho_matrix))
        if trace > 0.0:
            self.rho_matrix = self.rho_matrix / trace
            
        rho_ni_reduced = self._partial_trace_hydrogens(self.rho_matrix)
        rho_shadow = np.kron(rho_ni_reduced, self.h_reference)
        
        endogenous_delta = self._relative_entropy(self.rho_matrix, rho_shadow)
        
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
        if epsilon <= 0:
            epsilon = 1e-4
        n_epsilon = max(1, int(1.0 / (epsilon * (1.0 + abs(self.rho_scalar)))))
        return math.log(n_epsilon)

    def get_state(self) -> Dict[str, Any]:
        return {
            "rho": self.rho_scalar,
            "register": asdict(self.k_0)
        }


class ExtendedRelaxedQuantumModel:
    """Rigorous 8x8 expanded quantum framework with environmental dephasing.

    Models the exact unitary evolution of the tripartite system but
    additionally applies Kraus phase damping channels to the Nickel 
    subsystem, representing explicit interaction with an unmodeled thermal bath.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        reg_conf = config.get("initial_register", {})
        self.k_0 = MaterialRegister(
            theta_tilt=float(reg_conf.get("theta_tilt", 0.1)),
            theta_rot=float(reg_conf.get("theta_rot", 0.05)),
            delta_V_oct=float(reg_conf.get("delta_V_oct", 0.0)),
            delta_phi=float(reg_conf.get("delta_phi", 0.02)),
            epsilon_0=float(reg_conf.get("epsilon_0", 1.0))
        )
        
        self.rho_matrix = np.zeros((8, 8), dtype=complex)
        self.rho_matrix[0, 0] = 1.0
        
        self.h_reference = 0.25 * np.eye(4, dtype=complex)
        self.rho_scalar = float(config.get("initial_rho", 1.0))
        
        base_stiffness = float(config.get("g_oct_stiffness", 3.5))
        self.g_oct_operator = np.diag([base_stiffness, base_stiffness * 1.2, base_stiffness * 0.8])
        
        # Load interaction parameters dynamically from configuration
        self.proton_hopping = float(config.get("proton_hopping_energy", 0.5))
        self.proton_hopping_inter = float(config.get("inter_site_hopping", 0.2))
        self.electron_proton_coupling = float(config.get("electron_proton_coupling", 1.2))
        self.ni_transverse_hopping = float(config.get("ni_transverse_hopping", 0.8)) # New parameter
        self.dephasing_gamma = float(config.get("dephasing_gamma", 0.05)) # Parametrize Kraus strength
        
        sz = np.array([[1, 0], [0, -1]], dtype=complex)
        sx = np.array([[0, 1], [1, 0]], dtype=complex)
        id2 = np.eye(2, dtype=complex)
        id4 = np.eye(4, dtype=complex)
        id8 = np.eye(8, dtype=complex)
        
        self.op_ni_z = np.kron(sz, id4)
        self.op_ni_x = np.kron(sx, id4)
        
        self.op_h1_x = np.kron(id2, np.kron(sx, id2))
        self.op_h2_x = np.kron(id2, np.kron(id2, sx))
        self.op_hopping_h1_h2 = np.kron(id2, np.kron(sx, sx))
        
        self.op_interaction_1 = np.kron(sz, np.kron(sz, id2))
        self.op_interaction_2 = np.kron(sz, np.kron(id2, sz))
        
        self.kraus_0 = np.sqrt(1 - self.dephasing_gamma) * id8
        self.kraus_1 = np.sqrt(self.dephasing_gamma) * self.op_ni_z

    def _matrix_log(self, mat: np.ndarray, eps: float = 1e-9) -> np.ndarray:
        evals, evecs = np.linalg.eigh(mat)
        evals = np.maximum(evals, eps)
        return evecs @ np.diag(np.log(evals)) @ evecs.conj().T

    def _exact_unitary_operator(self, hamiltonian: np.ndarray, dt: float) -> np.ndarray:
        evals, evecs = np.linalg.eigh(hamiltonian)
        unitary_diag = np.diag(np.exp(-1j * dt * evals))
        return evecs @ unitary_diag @ evecs.conj().T

    def _relative_entropy(self, rho: np.ndarray, sigma: np.ndarray) -> float:
        log_rho = self._matrix_log(rho)
        log_sigma = self._matrix_log(sigma)
        entropy = np.real(np.trace(rho @ (log_rho - log_sigma)))
        return max(0.0, float(entropy))

    def _partial_trace_hydrogens(self, rho_8x8: np.ndarray) -> np.ndarray:
        rho_reshaped = rho_8x8.reshape((2, 2, 2, 2, 2, 2))
        trace_h2 = np.trace(rho_reshaped, axis1=2, axis2=5)
        trace_h1_h2 = np.trace(trace_h2, axis1=1, axis2=3)
        return trace_h1_h2

    def step(self, V_t: float, delta_0_external: float) -> Dict[str, float]:
        dt = 0.1
        
        # Hamiltonian includes transverse hopping for the Nickel subsystem
        h_total = (V_t * self.op_ni_z + 
                   self.ni_transverse_hopping * self.op_ni_x +
                   self.proton_hopping * (self.op_h1_x + self.op_h2_x) + 
                   self.proton_hopping_inter * self.op_hopping_h1_h2 +
                   self.electron_proton_coupling * (self.op_interaction_1 + self.op_interaction_2))
        
        unitary_op = self._exact_unitary_operator(h_total, dt)
        rho_unitary = unitary_op @ self.rho_matrix @ unitary_op.conj().T
        
        self.rho_matrix = self.kraus_0 @ rho_unitary @ self.kraus_0.conj().T + \
                          self.kraus_1 @ rho_unitary @ self.kraus_1.conj().T
        
        trace = np.real(np.trace(self.rho_matrix))
        if trace > 0.0:
            self.rho_matrix = self.rho_matrix / trace
            
        rho_ni_reduced = self._partial_trace_hydrogens(self.rho_matrix)
        rho_shadow = np.kron(rho_ni_reduced, self.h_reference)
        
        endogenous_delta = self._relative_entropy(self.rho_matrix, rho_shadow)
        
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
        if epsilon <= 0:
            epsilon = 1e-4
        n_epsilon = max(1, int(1.0 / (epsilon * (1.0 + abs(self.rho_scalar)))))
        return math.log(n_epsilon)

    def get_state(self) -> Dict[str, Any]:
        return {
            "rho": self.rho_scalar,
            "register": asdict(self.k_0)
        }