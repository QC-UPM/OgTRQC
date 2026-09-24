Comparative Analysis and Endogenous Recoverability Validation
=============================================================

.. warning::

   Historical prototype documentation. These quantum-geometric engines and
   their recoverability-to-force assumptions do not implement the current
   proton-transport paper. See :doc:`paper_models` and :doc:`reproduction`.


The comparative analysis of the data extracted from the generated reports reveals a profound shift in the interpretation of thermodynamic inertia when transitioning from externally driven models to endogenously relaxed architectures. When observing the coupling trajectory between matter and geometry, the original models exhibited a progressive and pronounced increase in the distortion of the octahedral cage. Conversely, both the relaxed quantum and relaxed causal models show a structural behavior where the geometric distortion does not accumulate, but rather decays significantly throughout the simulation steps, leading to a complete nullification of the final volume displacement.

This mechanical relaxation confirms that the dissipation of quantum information exists and continues to operate on the system, but its real physical impact is governed by internal dynamics rather than empirically forced profiles. By expanding the Hilbert space and computing the recoverability defect through von Neumann relative entropy, the simulation demonstrates that the latent entanglement swiftly dilutes the purity of the visible electronic subspace. However, the resulting endogenous elastic force is fundamentally insufficient to maintain the crystal lattice in a state of permanent macroscopic torsion.


Campaign Mapping
----------------
The reporting folders and engine aliases now follow an explicit Hilbert-dimension convention. This makes each generated artifact traceable to the effective state-space size used during execution.

.. list-table:: Campaign-to-Hilbert Mapping
   :widths: 18 14 24 24
   :header-rows: 1

   * - Alias / Campaign
     - Hilbert Space
     - Report Folder
     - Effective Engine
   * - ``legacy``
     - scalar proxy
     - ``reports_legacy``
     - ``OctaMemoryModel``
   * - ``quantum``
     - ``2x2``
     - ``reports_quantum``
     - ``QuantumMemoryModel``
   * - ``causal``
     - ``4x4``
     - ``reports_causal``
     - ``CausalSufficiencyModel``
   * - ``relaxed_quantum``
     - ``2x2``
     - ``reports_relaxed_quantum``
     - ``ScalableHilbertSpaceModel`` via wrapper
   * - ``relaxed_causal``
     - ``4x4``
     - ``reports_relaxed_causal``
     - ``ScalableHilbertSpaceModel`` via wrapper
   * - ``extended_quantum``
     - ``8x8``
     - ``reports_extended_quantum``
     - ``ScalableHilbertSpaceModel`` via wrapper
   * - ``extended_causal``
     - ``8x8``
     - ``reports_extended_causal``
     - ``ScalableHilbertSpaceModel`` via wrapper
   * - ``scalable_relaxed`` + ``--hilbert-dim 2``
     - ``2x2``
     - ``reports_scalable_h2``
     - ``ScalableHilbertSpaceModel``
   * - ``scalable_relaxed`` + ``--hilbert-dim 4``
     - ``4x4``
     - ``reports_scalable_h4``
     - ``ScalableHilbertSpaceModel``
   * - ``scalable_relaxed`` + ``--hilbert-dim 8``
     - ``8x8``
     - ``reports_scalable_h8``
     - ``ScalableHilbertSpaceModel``
   * - ``scalable_relaxed`` + ``--hilbert-dim 16``
     - ``16x16``
     - ``reports_scalable_h16``
     - ``ScalableHilbertSpaceModel``

.. raw:: html

   <div style="display: flex; flex-direction: column; gap: 20px;">
       <h3>Endogenous Relaxed Quantum Coupling</h3>
       <iframe src="../../reports_relaxed_quantum/goal_1_2_coupling_hilbert_2x2.html" height="600px" width="100%" style="border:none;"></iframe>
       <h3>Endogenous Relaxed Causal Coupling</h3>
       <iframe src="../../reports_relaxed_causal/goal_1_2_coupling_hilbert_4x4.html" height="600px" width="100%" style="border:none;"></iframe>
   </div>

These results critically correct the initial assumption that the memory of the device arises exclusively from the physical rigidity of the crystal lattice. The high structural deformation postulated in early iterations was a mathematical artifact caused by attempting to fit a geometric model operating under an insufficient algebra. The rigorous application of a positive elastic operator allows the system to resolve its own causal autonomy, empirically proving the theoretical theorem that hidden algebraic memory can masquerade as curvature.

The true inertia and storage capacity of the hydrogenated nickelate cell lie entirely within the rich topology of its latent quantum states. This is corroborated by the Kolmogorov and Tikhomirov entropic capacity limits, which maintain exceptionally high values above six for ultra fine resolution boundaries in the relaxed integrations. The crystallographic scaffold does not need to undergo extreme physical bending to exhibit memory retentiveness, as the device efficiently compresses its temporal history into the algebraic correlations of the hidden hydrogen polarons.

.. raw:: html

   <div style="display: flex; flex-direction: column; gap: 20px;">
       <h3>Relaxed Quantum Capacity Bounds</h3>
       <iframe src="../../reports_relaxed_quantum/goal_4_resolution_heuristic_hilbert_2x2.html" height="600px" width="100%" style="border:none;"></iframe>
       <h3>Relaxed Causal Capacity Bounds</h3>
       <iframe src="../../reports_relaxed_causal/goal_4_resolution_heuristic_hilbert_4x4.html" height="600px" width="100%" style="border:none;"></iframe>
   </div>
