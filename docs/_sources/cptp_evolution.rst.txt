Exact Unitary Evolution and CPTP Map Rigor
==========================================

The initial proof of concept implementations employed an explicit Euler differential approximation to evaluate the von Neumann equation. While computationally economical, linear approximations fail to strictly preserve the underlying probability trace and positive semi-definite boundaries of quantum density matrices over extended integration windows or beneath rapidly fluctuating Hamiltonian potentials. 

To overcome this vulnerability and satisfy the most stringent requirements of physical mathematical modeling, the relaxed integration engines (``RelaxedQuantumModel`` and ``RelaxedCausalModel``) were upgraded to deploy Exact Unitary Matrix Exponentials. By performing the eigendecomposition of the Hermitian Hamiltonian, the software explicitly calculates the matrix exponential representing the exact temporal evolution operator. Multiplying the state by this operator inherently protects the positivity boundary conditions prior to any environmental phase damping applied via Kraus operators, rendering the entire cycle a true Completely Positive Trace-Preserving (CPTP) map.

Unified Class Architecture Diagram
----------------------------------
The following diagram showcases the architectural injection of the exact unitary calculation methods directly into the object-oriented physics processing layers.

.. mermaid::

   classDiagram
      class MaterialRegister {
          +float theta_tilt
          +float theta_rot
          +float delta_V_oct
          +float delta_phi
          +float epsilon_0
      }
      
      class IMemoryModel {
          <<interface>>
          +step(V_t, delta_0) dict
      }
      
      class RelaxedQuantumModel {
          -ndarray rho_matrix
          -ndarray kraus_0
          -ndarray kraus_1
          +step(V_t, delta_0) dict
          -_exact_unitary_operator(hamiltonian, dt) ndarray
          -_relative_entropy(rho, sigma) float
      }
      
      class RelaxedCausalModel {
          -ndarray rho_matrix
          -ndarray op_interaction
          +step(V_t, delta_0) dict
          -_exact_unitary_operator(hamiltonian, dt) ndarray
          -_partial_trace_hydrogen(rho_4x4) ndarray
          -_relative_entropy(rho, sigma) float
      }

      IMemoryModel <|.. RelaxedQuantumModel
      IMemoryModel <|.. RelaxedCausalModel
      RelaxedQuantumModel --> MaterialRegister
      RelaxedCausalModel --> MaterialRegister

Integration Sequence Diagram
----------------------------
The sequence trace details the step-by-step rigorous mapping constructed within a single discretization phase, starting from the external signal all the way down to the macroscopically measurable material geometry drift.

.. mermaid::

   sequenceDiagram
      autonumber
      Participant Presenter as Simulation Presenter
      Participant Model as Relaxed Engine Matrix Core
      Participant Register as Octahedral Material Register
      
      Presenter ->> Model: Invokes step(V_t)
      Model ->> Model: Builds complete Hermitian Hamiltonian H(t)
      Model ->> Model: Decomposes H(t) extracting eigenvalues
      Model ->> Model: Constructs Exact Unitary Operator U = exp(-i*H*dt)
      Model ->> Model: Evolves state exactly rho_unitary = U * rho * U_adjoint
      Model ->> Model: Applies CPTP Kraus channels for phase damping
      Model ->> Model: Derives reduced sub-algebra shadow trace
      Model ->> Model: Computes von Neumann relative entropy
      Model ->> Model: Projects resultant force via positive diagonal elastic tensor
      Model ->> Register: Updates structural vector parameters
      Register -->> Model: Yields macroscopic distortion sum
      Model -->> Presenter: Returns strict metrics dictionary payload

Execution Instance Object Diagram
---------------------------------
This memory map illustrates a specific programmatic snapshot running inside the Python runtime environment, representing the active linkages during the calculation of the relative entropy feedback mechanism.

.. mermaid::

   objectDiagram
      object ModelInstance {
          class: RelaxedCausalModel
          rho_scalar: 0.05
          dt: 0.1
          proton_hopping: 0.5
      }
      
      object TensorSpace {
          class: numpy.ndarray
          shape: (4, 4)
          dtype: complex
          property: Trace-Preserved Unitary State
      }
      
      object GeometryRegister {
          class: MaterialRegister
          theta_tilt: 0.118
          theta_rot: 0.059
          delta_V_oct: 0.0
      }
      
      ModelInstance --|> TensorSpace : Manages Exact
      ModelInstance --|> GeometryRegister : Distorts Elastically
