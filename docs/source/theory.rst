Theoretical Framework: gTRQC in :math:`H_xNdNiO_3` Heterostructures
===================================================================

Generalized Time-Recoverable Quantum Control (gTRQC)
----------------------------------------------------
The framework of Generalized Time-Recoverable Quantum Control (**gTRQC**) provides a closed-loop algebraic paradigm designed to model the non-Markovian feedback loops that occur between quantum matter states and localized structural crystal matrices. 

In this architectural suite, the host unit cell is mathematically modeled as an isolated :math:`NiO_6` octahedral geometry graph. The six vertices denote oxygen ligated positions (:math:`O^{2-}`) defining the electronic field, while the central coordination position acts as the active Nickel (:math:`Ni`) electronic system center. Its orbital configuration, valence state, and polaronic correlations constitute the active non-volatile register.

.. math::

   \mathcal{H}_{cell} = \mathcal{H}_{Ni} \otimes \mathcal{H}_{O6} \otimes \ell^2(\Omega_H) \otimes \ell^2(\Omega_{oct})

Where :math:`\Omega_H` defines the bounded configuration spaces of localized proton-polaron interstitial anomalies and :math:`\Omega_{oct}` represents the tensor space of discrete octahedral lattice states.

Lattice Distortion and Protonic Latency Coupling
------------------------------------------------
The quantum coherence parameter of the device state matrix (:math:`\rho`) evolves dynamically driven by external electrical stimulation protocols :math:`V(t)` combined with localized microstrain fields. 

Mechanical deviations in the coordination environment—parameterized by tilt components (:math:`\theta_{tilt}`), rotative deflections (:math:`\theta_{rot}`), and volume expansions (:math:`\Delta V_{oct}`)—experience structural feedback driven by the instantaneous quantum recoverability loss metric :math:`\Delta_0(t)`.

The foundational raw driving force source of structural geometric strain :math:`J_0(t)` is formalized as follows:

.. math::

   J_0(t) = \Delta_0(t) \cdot g_{oct}

Where :math:`g_{oct}` serves as the graphistic stiffness modifier of the crystal environment. Protonic latency—caused by spatial transport delays of structural interstitial hydrogen defects—introduces non-instantaneous retroactivity modeled via an explicit step delay loop :math:`d_{elay}`:

.. math::

   J_{eff}(t) = J_0(t) - \kappa \cdot J_0(t - d_{elay})

Kolmogorov-Tikhomirov Metric Entropy Bounds
-------------------------------------------
Following the functional space mapping principles defined by Kolmogorov and Tikhomirov (1961) regarding the metric :math:`\epsilon`-capacity of continuous sets, the absolute information capability metric of the atomic register element (:math:`C_{atom}(\epsilon)`) is evaluated through the grouping cardinality of protonic trajectory sets that remain functionally indistinguishable given a resolution threshold :math:`\epsilon`:

.. math::

   C_{atom}(\epsilon) = \log_2(N_\epsilon)

Where :math:`N_\epsilon` denotes the total available subset of stable spatial configurations of hydrogen polarons whose future memory readback signals are separated by a minimum Euclidean distance of :math:`\epsilon`.
