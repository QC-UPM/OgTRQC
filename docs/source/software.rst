Software Architecture & Engineering Blueprints
==============================================

The execution engine is structured using a strict Model-View-Presenter decoupling paradigm built on Python 3.12. This modular layout ensures that physical processing kernels remain completely isolated from standard terminal presentation views or persistence logging layers. The architectural evolution of this suite introduces a factory pattern within the presentation layer. Depending on the execution parameters, the presenter dynamically binds to either the legacy phenomenological model or the rigorous quantum density matrix integrator, both sharing a common public interface.

Engine Class Hierarchy Diagram
------------------------------
The relationships, inherited structures, and operational boundaries of the software components are mapped out below, demonstrating the implementation of the dual-engine architecture.

.. mermaid::

   classDiagram
      class MaterialRegister {
          +float theta_tilt
          +float theta_rot
          +float delta_V_oct
          +float delta_phi
          +float epsilon_0
          +to_vector() list
      }
      class IMemoryModel {
          <<interface>>
          +step(V_t, delta_0) dict
          +calculate_capacity(epsilon) float
          +get_state() dict
      }
      class OctaMemoryModel {
          <<Legacy Phenomenological>>
          -float rho_scalar
          +step(V_t, delta_0) dict
      }
      class QuantumMemoryModel {
          <<Rigorous Von Neumann>>
          -ndarray rho_matrix
          +step(V_t, delta_0) dict
      }
      IMemoryModel <|.. OctaMemoryModel
      IMemoryModel <|.. QuantumMemoryModel
      OctaMemoryModel --> MaterialRegister
      QuantumMemoryModel --> MaterialRegister
      class SimulationPresenter {
          -IMemoryModel model
          +run_simulation()
      }
      SimulationPresenter --> IMemoryModel

Legacy versus Quantum Integration Flow
--------------------------------------
The transformation matrix routing for data tracking during model updates diverges based on the selected mathematical engine. The following flowchart compares the legacy phenomenological approximation against the strict quantum integration loop.

.. mermaid::

   graph TD
      Start((Time Step Evaluation)) --> Fork{Selected Engine}
      Fork -->|Legacy| L1[Retrieve scalar delayed source from list buffer]
      L1 --> L2[Compute linear structural projection]
      L2 --> L3[Update discrete vector parameters]
      L3 --> L4[Apply bounded scalar CPTP proxy map to rho]
      L4 --> EndLegacy((Return Scalar Metrics))
      Fork -->|Quantum| Q1[Extract delayed thermodynamic source from deque buffer]
      Q1 --> Q2[Solve differential response of the curvature register]
      Q2 --> Q3[Build Hamiltonian matrix with applied voltage and geometric perturbation]
      Q3 --> Q4[Compute complex commutator]
      Q4 --> Q5[Execute von Neumann integration step over dt]
      Q5 --> Q6[Apply trace-preserving projection to density matrix]
      Q6 --> Q7[Extract macroscopic conductance from current operator trace]
      Q7 --> EndQuantum((Return Tensor Metrics))

Execution Sequence Flow
-----------------------
The timeline interaction model for a discrete operational simulation window maps onto the following execution trace, showcasing the dynamic factory instantiation.

.. mermaid::

   sequenceDiagram
      autonumber
      Participant CLI as Main Terminal
      Participant P as SimulationPresenter
      Participant M as Selected Memory Model
      Participant V as Execution View
      CLI ->> P: Initialize Framework passing configuration
      P ->> V: Display localized greeting
      P ->> M: Instantiate required physical engine via Factory
      loop Discretized Temporal Integration
          P ->> M: step(Voltage, Recoverability Loss)
          M ->> M: Update material register using delay buffer
          M ->> M: Evolve quantum state representation
          M -->> P: Return observable thermodynamic metrics
          P ->> V: Output localized step telemetry
      end
      P ->> M: calculate_capacity(epsilon bounds)
      M -->> P: Return Kolmogorov memory capacity
      P ->> V: render_results(final_state_summary)
      V -->> CLI: Generate HTML reports and Markdown tabular data
