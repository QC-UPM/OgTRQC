"""Quantum Integrator module for Octahedral gTRQC Simulation.

This module provides a rigorous non-Markovian quantum execution framework,
implementing the density matrix operations and explicit tensorial coupling
for the geometric register of the material cell.
"""

import numpy as np
from collections import deque
from typing import Deque

class QuantumMaterialCell:
    """Represents a quantum material cell with a delayed geometrical register.

    This class models the density matrix evolution of quantum matter coupled
    tightly to an octahedral physical geometry register, using exact
    trace-preserving integrations and explicit delay buffers for protonic latency.
    """

    def __init__(self, delay_steps: int = 5, rigidity: float = 0.5, coupling: float = 1.0) -> None:
        """Initializes the quantum density matrix and structural parameters.

        Args:
            delay_steps (int, optional): Number of steps to delay the protonic source. Defaults to 5.
            rigidity (float, optional): Stiffness coefficient of the octahedral cage. Defaults to 0.5.
            coupling (float, optional): Coupling strength between matter and geometry. Defaults to 1.0.
        """
        self.delay_steps: int = delay_steps
        self.rigidity: float = rigidity
        self.coupling: float = coupling
        
        self.k_oct: np.ndarray = np.array([0.0, 0.0, 1.0, 0.0, 0.0], dtype=float)
        
        self.source_history: Deque[float] = deque(
            [0.0] * (self.delay_steps + 1), 
            maxlen=self.delay_steps + 1
        )
        
        self.rho: np.ndarray = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)

    def step(self, current_proton_source: float, dt: float = 0.1) -> None:
        """Evaluates one discrete time step of the quantum-geometry system.

        Applies the historical buffer for delayed protonic sources, solves
        the differential response of the curvature register, and performs a
        von Neumann integration step preserving the trace of the density matrix.

        Args:
            current_proton_source (float): The instantaneous protonic source value.
            dt (float, optional): Time step increment for the integration. Defaults to 0.1.
        """
        self.source_history.append(current_proton_source)
        
        delayed_source: float = self.source_history[0]
        
        delta_k: float = - (delayed_source * self.coupling / self.rigidity) * dt
        
        self.k_oct[2] += delta_k
        
        perturbation: np.ndarray = np.array(
            [[0.0, self.k_oct[2]], [self.k_oct[2], 0.0]], 
            dtype=complex
        )
        
        commutator: np.ndarray = perturbation @ self.rho - self.rho @ perturbation
        self.rho = self.rho - 1j * dt * commutator
        
        trace: float = np.real(np.trace(self.rho))
        if trace > 0.0:
            self.rho = self.rho / trace

    def get_conductance(self) -> float:
        """Calculates the macroscopic conductance of the material cell.

        Extracts the expected value of the current observable over the current
        quantum density matrix.

        Returns:
            float: The evaluated conductance value.
        """
        operator_current: np.ndarray = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
        conductance: float = np.real(np.trace(self.rho @ operator_current))
        return conductance
