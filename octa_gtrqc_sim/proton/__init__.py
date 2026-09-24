"""Paper-aligned classical proton transport and independent relaxation models.

Recoverability is a read-only diagnostic. The models in this namespace do not
inherit the quantum-geometric feedback assumptions of the historical engines.
"""

from octa_gtrqc_sim.proton.dataset import PolarizationDataset
from octa_gtrqc_sim.proton.structure import StructuralModel
from octa_gtrqc_sim.proton.transport import DeviceConfig, TransportModel

__all__ = ['PolarizationDataset', 'StructuralModel', 'DeviceConfig', 'TransportModel']
