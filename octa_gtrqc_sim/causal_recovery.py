"""Relaxed Causal Sufficiency Integrator module for Octahedral gTRQC Simulation.

This module provides an expanded Hilbert space execution framework computing
endogenous memory loss through partial traces and relative entropy evaluation,
while enforcing exact unitary matrix exponential dynamics to maintain strict
quantum probability limits.
"""

import math
from typing import Dict, Any
import numpy as np
from dataclasses import asdict
from octa_gtrqc_sim.material_register import MaterialRegister


class RelaxedCausalModel:
    """Rigorous expanded quantum execution framework for causal autonomy.

    Models the 4x4 density matrix evolution strictly using exact unitary
    transformations, deriving recoverability loss by comparing the full
    atomistic state against its conditionally expected visible shadow state
    over the reduced sub-algebra.
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
        
        self.rho_matrix = np.zeros((4, 4), dtype=complex)
        self.rho_matrix[0, 0] = 1.0
        
        self.h_reference = np.array([[0.5, 0.0], [0.0, 0.5]], dtype=complex)
        self.rho_scalar = float(config.get("initial_rho", 1.0))
        
        base_stiffness = float(config.get("g_oct_stiffness", 3.5))
        self.g_oct_operator = np.diag([base_stiffness, base_stiffness * 1.2, base_stiffness * 0.8])
        
        self.proton_hopping = float(config.get("proton_hopping_energy", 0.5))
        self.electron_proton_coupling = float(config.get("electron_proton_coupling", 1.2))
        self.ni_transverse_hopping = float(config.get("ni_transverse_hopping", 0.8))
        
        sz = np.array([[1, 0], [0, -1]], dtype=complex)
        sx = np.array([[0, 1], [1, 0]], dtype=complex)
        id2 = np.eye(2, dtype=complex)
        
        self.op_ni_z = np.kron(sz, id2)
        self.op_ni_x = np.kron(sx, id2)
        self.op_h_x = np.kron(id2, sx)
        self.op_interaction = np.kron(sz, sz)

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

    def _partial_trace_hydrogen(self, rho_4x4: np.ndarray) -> np.ndarray:
        rho_reshaped = rho_4x4.reshape((2, 2, 2, 2))
        return np.trace(rho_reshaped, axis1=1, axis2=3)

    def step(self, V_t: float, delta_0_external: float) -> Dict[str, float]:
        dt = 0.1
        
        h_total = (V_t * self.op_ni_z + 
                   self.ni_transverse_hopping * self.op_ni_x +
                   self.proton_hopping * self.op_h_x + 
                   self.electron_proton_coupling * self.op_interaction)
        
        unitary_op = self._exact_unitary_operator(h_total, dt)
        self.rho_matrix = unitary_op @ self.rho_matrix @ unitary_op.conj().T
        
        trace = np.real(np.trace(self.rho_matrix))
        if trace > 0.0:
            self.rho_matrix = self.rho_matrix / trace
            
        rho_ni_reduced = self._partial_trace_hydrogen(self.rho_matrix)
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