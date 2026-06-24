"""Scalable relaxed Hilbert-space engines for Octahedral gTRQC Simulation."""

import math
from dataclasses import asdict
from typing import Any, Dict, List

import numpy as np

from octa_gtrqc_sim.material_register import MaterialRegister


class ScalableHilbertSpaceModel:
    """Relaxed quantum engine parameterized by Hilbert-space dimension.

    The first subsystem always represents the visible Nickel degree of freedom.
    Any additional binary subsystems represent hidden protonic sectors, so the
    total Hilbert dimension is ``2 ** (1 + hidden_site_count)``.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        reg_conf = config.get("initial_register", {})
        self.k_0 = MaterialRegister(
            theta_tilt=float(reg_conf.get("theta_tilt", 0.1)),
            theta_rot=float(reg_conf.get("theta_rot", 0.05)),
            delta_V_oct=float(reg_conf.get("delta_V_oct", 0.0)),
            delta_phi=float(reg_conf.get("delta_phi", 0.02)),
            epsilon_0=float(reg_conf.get("epsilon_0", 1.0)),
        )

        self.hilbert_dimension = self._validate_hilbert_dimension(
            int(config.get("hilbert_dimension", 2))
        )
        self.subsystem_count = int(round(math.log2(self.hilbert_dimension)))
        self.hidden_site_count = max(0, self.subsystem_count - 1)
        self.hilbert_dimension_label = f"{self.hilbert_dimension}x{self.hilbert_dimension}"
        self.engine_family = str(config.get("engine_family", "scalable_relaxed"))

        self.rho_matrix = np.zeros((self.hilbert_dimension, self.hilbert_dimension), dtype=complex)
        self.rho_matrix[0, 0] = 1.0
        self.rho_scalar = float(config.get("initial_rho", 1.0))

        base_stiffness = float(config.get("g_oct_stiffness", 3.5))
        self.g_oct_operator = np.diag(
            [base_stiffness, base_stiffness * 1.2, base_stiffness * 0.8]
        )

        self.ni_transverse_hopping = float(config.get("ni_transverse_hopping", 0.8))
        self.proton_hopping = float(config.get("proton_hopping_energy", 0.5))
        self.inter_site_hopping = float(config.get("inter_site_hopping", 0.2))
        self.electron_proton_coupling = float(config.get("electron_proton_coupling", 1.2))
        self.dephasing_gamma = max(0.0, float(config.get("dephasing_gamma", 0.0)))

        self.id2 = np.eye(2, dtype=complex)
        self.sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)
        self.sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)
        self.identity_total = np.eye(self.hilbert_dimension, dtype=complex)

        self.op_ni_z = self._operator_on_subsystem(self.sigma_z, 0)
        self.op_ni_x = self._operator_on_subsystem(self.sigma_x, 0)
        self.hidden_x_ops = [
            self._operator_on_subsystem(self.sigma_x, idx)
            for idx in range(1, self.subsystem_count)
        ]
        self.hidden_z_ops = [
            self._operator_on_subsystem(self.sigma_z, idx)
            for idx in range(1, self.subsystem_count)
        ]
        self.hidden_reference = self._build_hidden_reference()

        self.kraus_0 = np.sqrt(max(0.0, 1.0 - self.dephasing_gamma)) * self.identity_total
        self.kraus_1 = np.sqrt(self.dephasing_gamma) * self.op_ni_z

    @staticmethod
    def _validate_hilbert_dimension(hilbert_dimension: int) -> int:
        if hilbert_dimension < 2:
            raise ValueError("Hilbert dimension must be at least 2.")
        if hilbert_dimension & (hilbert_dimension - 1):
            raise ValueError("Hilbert dimension must be a power of two.")
        return hilbert_dimension

    def _operator_on_subsystem(self, local_operator: np.ndarray, subsystem_index: int) -> np.ndarray:
        factors: List[np.ndarray] = []
        for idx in range(self.subsystem_count):
            factors.append(local_operator if idx == subsystem_index else self.id2)
        full_operator = factors[0]
        for factor in factors[1:]:
            full_operator = np.kron(full_operator, factor)
        return full_operator

    def _build_hidden_reference(self) -> np.ndarray:
        if self.hidden_site_count == 0:
            return 0.5 * np.eye(2, dtype=complex)
        hidden_dim = 2 ** self.hidden_site_count
        return np.eye(hidden_dim, dtype=complex) / hidden_dim

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

    def _reduced_nickel_state(self, rho_matrix: np.ndarray) -> np.ndarray:
        if self.hidden_site_count == 0:
            return rho_matrix
        reshaped = rho_matrix.reshape((2,) * (2 * self.subsystem_count))
        current_total = self.subsystem_count
        for subsystem_index in range(self.subsystem_count - 1, 0, -1):
            reshaped = np.trace(reshaped, axis1=subsystem_index, axis2=subsystem_index + current_total)
            current_total -= 1
        return reshaped.reshape((2, 2))

    def _build_shadow_state(self) -> np.ndarray:
        if self.hidden_site_count == 0:
            return self.hidden_reference
        rho_ni_reduced = self._reduced_nickel_state(self.rho_matrix)
        return np.kron(rho_ni_reduced, self.hidden_reference)

    def _build_total_hamiltonian(self, voltage: float) -> np.ndarray:
        h_total = voltage * self.op_ni_z + self.ni_transverse_hopping * self.op_ni_x
        if self.hidden_x_ops:
            h_total = h_total + self.proton_hopping * sum(self.hidden_x_ops)
        if len(self.hidden_x_ops) >= 2:
            adjacency_sum = np.zeros_like(h_total)
            for left, right in zip(self.hidden_x_ops[:-1], self.hidden_x_ops[1:]):
                adjacency_sum = adjacency_sum + (left @ right)
            h_total = h_total + self.inter_site_hopping * adjacency_sum
        if self.hidden_z_ops:
            interaction_sum = np.zeros_like(h_total)
            for hidden_z in self.hidden_z_ops:
                interaction_sum = interaction_sum + (self.op_ni_z @ hidden_z)
            h_total = h_total + self.electron_proton_coupling * interaction_sum
        return h_total

    def step(self, V_t: float, delta_0_external: float) -> Dict[str, float]:
        dt = 0.1
        h_total = self._build_total_hamiltonian(V_t)

        unitary_op = self._exact_unitary_operator(h_total, dt)
        rho_unitary = unitary_op @ self.rho_matrix @ unitary_op.conj().T

        if self.dephasing_gamma > 0.0:
            self.rho_matrix = (
                self.kraus_0 @ rho_unitary @ self.kraus_0.conj().T
                + self.kraus_1 @ rho_unitary @ self.kraus_1.conj().T
            )
        else:
            self.rho_matrix = rho_unitary

        trace = np.real(np.trace(self.rho_matrix))
        if trace > 0.0:
            self.rho_matrix = self.rho_matrix / trace

        shadow_state = self._build_shadow_state()
        endogenous_delta = self._relative_entropy(self.rho_matrix, shadow_state)

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
            "endogenous_delta": endogenous_delta,
        }

    def estimate_resolution_heuristic(self, epsilon: float) -> float:
        if epsilon <= 0:
            epsilon = 1e-4
        n_epsilon = max(1, int(1.0 / (epsilon * (1.0 + abs(self.rho_scalar)))))
        return math.log(n_epsilon)

    def calculate_capacity(self, epsilon: float) -> float:
        """Backward-compatible alias for the heuristic resolution estimate."""
        return self.estimate_resolution_heuristic(epsilon)

    def get_state(self) -> Dict[str, Any]:
        return {
            "rho": self.rho_scalar,
            "register": asdict(self.k_0),
            "hilbert_dimension": self.hilbert_dimension,
            "hilbert_dimension_label": self.hilbert_dimension_label,
            "hidden_site_count": self.hidden_site_count,
            "dephasing_gamma": self.dephasing_gamma,
        }
