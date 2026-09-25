Models and scientific boundaries
==================================

Structural free energy
------------------------

``StructuralModel`` retains the local radial cage coordinate :math:`Q_{A,i}`
and the mesh-staggered breathing coordinate :math:`Q_R`, in angstroms. The
420 cm⁻¹ effective cage prior gives :math:`K_A=10.3784` eV/Å²; the zero-strain
[001] breathing prior gives :math:`K_R=36.6667` eV/Å². The free energy is

.. math::

   F_{str}=\sum_i\left(\tfrac12 K_A Q_{A,i}^2-g_A c_i Q_{A,i}\right)
       +N\left(\tfrac12 K_R Q_R^2-g_R m_{\pi,N}Q_R\right).

Here :math:`g_A=K_A Q_A^{(1)}`, :math:`g_R=K_R Q_R^{bulk}`, and
:math:`m_{\pi,N}=|\sum_i(-1)^i c_i|/\sum_i c_i`. The sign convention does not
change the absolute order parameter. An empty proton configuration has zero
order. Donated-electron occupancy equals proton occupancy; independent
many-electron dynamics are not solved.

``equilibrium`` returns the exact harmonic minimizers; ``forces`` returns
negative gradients, with the breathing force expressed per cell. Positive
definiteness concerns only this two-dimensional calibrated subspace. It does
not establish stability of omitted angular, Jahn–Teller, or polar modes.

.. important::

   The alternating statistic is attached to device cells, not identified Ni
   sublattices. Its refinement limitation is retained and tested, not repaired
   by relabelling the device mesh as a crystal.

Transport
-----------

``TransportModel.freeze`` constructs a column generator :math:`Q` with
reflecting boundaries. The convention is :math:`\dot p=Qp`. For each edge,

.. math::

   k_{i\to j}=\frac{D_{ij}}{h^2}\exp[-\beta(U_j-U_i)/2],\qquad
   k_{j\to i}=\frac{D_{ij}}{h^2}\exp[+\beta(U_j-U_i)/2].

The potential includes the field and declared structural site-energy terms.
The barrier includes an explicitly supplied transport coefficient
``chi_transport``. Its nominal value transfers the relaxation fit; the
transport sensitivity study varies it independently without refitting
polarization. Geometry is in metres, field in V/m, temperature in K, energies
in eV, diffusivity in m²/s, and rates in s⁻¹.

``FrozenGenerator`` checks conservation, Boltzmann stationarity, local detailed
balance, entropy dissipation, and the weighted spectral-gap lower bound. Sparse
matrix-exponential propagation evolves a normalized probability. It does not
claim to solve nonlinear self-consistent occupancy evolution, Poisson coupling,
oxygen-vacancy kinetics, or exclusion-process saturation.

Two convergence experiments must remain distinct:

* ``continuum`` uses spatially constant diffusivity and a constant field. Its
  regression target is the paper's approximately 2.029 order against N=512.
* ``refinement`` retains structure-dependent site energies and barriers on
  each finite grid. Its smooth-limit reference sets only the parity statistic
  to zero. Symmetric and gradient backgrounds have different convergence
  behavior; the alternating-grid counterexample is exported explicitly.

Polarization relaxation
-------------------------

``RelaxationModel`` implements the original single exponential, stretched
exponential, distributed spectrum, and retrospective biexponential comparator.
For the distributed spectrum,

.. math::

   P(t;f)=\sum_j w_j(f)\exp[-t/\tau_j(f)],\qquad
   \log\tau_j=\log\tau_0+\alpha_A z_j+c_F f,

with 21 fixed :math:`z_j\in[0,1]`, :math:`f=(E_{kV/cm}-333)/200`, and
normalized exponential weights proportional to
:math:`\exp[(b_0+b_1 f)z_j+b_2(z_j-1/2)^2]`.
The original numerical parameterization uses
:math:`\alpha_A=\chi_{cond}E_A/(k_BT)`. Only that combination is identified
by this polarization fit. No concentration trajectory is an input to it.

Primary calibration uses 133, 267, and 400 kV/cm. All 87 observations at
533 kV/cm are excluded from fitting and primary uncertainty construction.
The ``review`` study repeats whole-field folds retrospectively; it does not
turn the four traces into four independent experiments.

Recoverability
----------------

``RecoverabilityDiagnostic`` evaluates the commuting Bernoulli specialization:

.. math::

   \Delta(c)=\frac1N\sum_i\left[c_i\log\frac{c_i}{\bar c}
       +(1-c_i)\log\frac{1-c_i}{1-\bar c}\right].

It is measured in nats/site. Endpoint values use the continuous limit.
Mean projection discards direction: reflected profiles have equal mean and
recoverability but can produce different directed future observations. This
quantity is absent from free energy, force, rates, and the polarization law.

The larger synthetic protocol-transfer and hidden-twin results are retained as
numeric figure inputs; the full original campaigns remain external. The native
``hidden_state`` example is explicitly smaller and is not used to claim the
notebook's AUC or signal-to-noise results.

Inference limits
------------------

Bootstrap prediction intervals resample calibration residuals pointwise;
serial correlation is not modelled. Information criteria use a working iid
Gaussian likelihood and count its shared residual variance. Profile intervals
hold the reference residual variance fixed; they are not a concentrated
unknown-variance likelihood ratio or proof of global uniqueness.
