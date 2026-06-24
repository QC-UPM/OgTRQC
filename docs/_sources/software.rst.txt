Software Architecture and Engineering Blueprints
================================================

The execution engine is structured using a strict Model-View-Presenter decoupling paradigm built on Python. This modular layout ensures that physical processing kernels remain completely isolated from standard terminal presentation views or persistence logging layers. The presentation layer can dynamically bind legacy phenomenological engines, fixed-dimension quantum engines, or a scalable relaxed Hilbert-space engine that spans 2x2, 4x4, 8x8, and 16x16 configurations from one computational core.

Engine Class Hierarchy Diagram
------------------------------
The relationships, inherited structures, and operational boundaries of the software components are mapped out below, demonstrating the implementation of the multi-engine architecture.


Engine Campaign Matrix
----------------------
The refactored execution layer distinguishes between user-facing campaign aliases and the effective engine implementation used internally.

.. list-table:: Engine Alias Matrix
   :widths: 18 14 28 22
   :header-rows: 1

   * - User-Facing Alias
     - Hilbert Space
     - Internal Implementation
     - Default Output Folder
   * - ``legacy``
     - scalar proxy
     - ``OctaMemoryModel``
     - ``reports_legacy``
   * - ``quantum``
     - ``2x2``
     - ``QuantumMemoryModel``
     - ``reports_quantum``
   * - ``causal``
     - ``4x4``
     - ``CausalSufficiencyModel``
     - ``reports_causal``
   * - ``relaxed_quantum``
     - ``2x2``
     - ``ScalableHilbertSpaceModel`` via compatibility wrapper
     - ``reports_relaxed_quantum``
   * - ``relaxed_causal``
     - ``4x4``
     - ``ScalableHilbertSpaceModel`` via compatibility wrapper
     - ``reports_relaxed_causal``
   * - ``extended_quantum``
     - ``8x8``
     - ``ScalableHilbertSpaceModel`` via compatibility wrapper
     - ``reports_extended_quantum``
   * - ``extended_causal``
     - ``8x8``
     - ``ScalableHilbertSpaceModel`` via compatibility wrapper
     - ``reports_extended_causal``
   * - ``scalable_relaxed``
     - configurable: ``2x2``, ``4x4``, ``8x8``, ``16x16``
     - ``ScalableHilbertSpaceModel``
     - ``reports_scalable_h*``

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
          +estimate_resolution_heuristic(epsilon) float
          +get_state() dict
      }
      class OctaMemoryModel {
          <<Legacy Phenomenological>>
          +step(V_t, delta_0) dict
      }
      class QuantumMemoryModel {
          <<Rigorous Von Neumann>>
          +step(V_t, delta_0) dict
      }
      class CausalSufficiencyModel {
          <<Expanded Tensor Space>>
          +step(V_t, delta_0) dict
      }
      class ScalableHilbertSpaceModel {
          <<Dimension-Scalable Relaxed>>
          +step(V_t, delta_0) dict
      }
      IMemoryModel <|.. OctaMemoryModel
      IMemoryModel <|.. QuantumMemoryModel
      IMemoryModel <|.. CausalSufficiencyModel
      IMemoryModel <|.. ScalableHilbertSpaceModel
      OctaMemoryModel --> MaterialRegister
      QuantumMemoryModel --> MaterialRegister
      CausalSufficiencyModel --> MaterialRegister
      ScalableHilbertSpaceModel --> MaterialRegister
      class SimulationPresenter {
          -IMemoryModel model
          +run_simulation()
      }
      SimulationPresenter --> IMemoryModel

Integration Flow and Endogenous Entropy Derivation
--------------------------------------------------
The transformation matrix routing for data tracking during model updates diverges based on the selected mathematical engine. The following flowchart compares the standard driven models against the relaxed autonomous integration loop.

.. mermaid::

   graph TD
      Start((Time Step Evaluation)) --> Fork{Selected Engine Strategy}
      Fork -->|External Driven| Ext1[Extract delayed external thermodynamic source]
      Ext1 --> Ext2[Solve differential response of the curvature register]
      Ext2 --> Ext3[Compute standard von Neumann integration over dt]
      Ext3 --> Ext4[Extract macroscopic conductance trace]
      Ext4 --> EndExternal((Return Standard Metrics))
      Fork -->|Endogenous Relaxed| End1[Construct total Hamiltonian with expanded Hilbert tensor]
      End1 --> End2[Compute unitary evolution step]
      End2 --> End3[Apply completely positive map via Kraus Operators]
      End3 --> End4[Derive conditional expected shadow state via partial trace]
      End4 --> End5[Calculate von Neumann relative entropy]
      End5 --> End6[Project endogenous information loss onto positive elastic tensor]
      End6 --> End7[Update structural coordinate vector]
      End7 --> EndRelaxed((Return Autonomous Metrics))

Execution Sequence Flow
-----------------------
The timeline interaction model for a discrete operational simulation window maps onto the following execution trace, showcasing the dynamic factory instantiation and the autonomous evaluation step.

.. mermaid::

   sequenceDiagram
      autonumber
      Participant CLI as Main Terminal
      Participant P as SimulationPresenter
      Participant M as Selected Memory Engine
      Participant V as Execution View
      CLI ->> P: Initialize Framework passing configuration
      P ->> V: Display localized greeting
      P ->> M: Instantiate required physical engine via Factory
      loop Discretized Temporal Integration
          P ->> M: step(Voltage, Ignored External Loss)
          M ->> M: Evolve quantum state representation
          M ->> M: Calculate relative entropy against shadow state
          M ->> M: Apply geometric strain via elastic operator
          M -->> P: Return observable thermodynamic metrics
          P ->> V: Output localized step telemetry
      end
      P ->> M: estimate_resolution_heuristic(epsilon bounds)
      M -->> P: Return heuristic resolution indicator
      P ->> V: render_results(final_state_summary)
      V -->> CLI: Generate HTML reports and Markdown tabular data
