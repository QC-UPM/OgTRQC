"""2x2 wrapper over the scalable relaxed Hilbert engine."""

from typing import Any, Dict

from octa_gtrqc_sim.scalable_hilbert import ScalableHilbertSpaceModel


class RelaxedQuantumModel(ScalableHilbertSpaceModel):
    """Compatibility wrapper for the 2x2 relaxed quantum configuration."""

    def __init__(self, config: Dict[str, Any]) -> None:
        merged_config = dict(config)
        merged_config["hilbert_dimension"] = 2
        merged_config.setdefault("dephasing_gamma", 0.05)
        merged_config.setdefault("engine_family", "relaxed_quantum")
        super().__init__(merged_config)
