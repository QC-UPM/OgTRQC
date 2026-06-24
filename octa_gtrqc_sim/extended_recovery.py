"""8x8 compatibility wrappers over the scalable relaxed Hilbert engine."""

from typing import Any, Dict

from octa_gtrqc_sim.scalable_hilbert import ScalableHilbertSpaceModel


class ExtendedRelaxedCausalModel(ScalableHilbertSpaceModel):
    """Compatibility wrapper for the 8x8 relaxed causal configuration."""

    def __init__(self, config: Dict[str, Any]) -> None:
        merged_config = dict(config)
        merged_config["hilbert_dimension"] = 8
        merged_config["dephasing_gamma"] = 0.0
        merged_config.setdefault("engine_family", "extended_causal")
        super().__init__(merged_config)


class ExtendedRelaxedQuantumModel(ScalableHilbertSpaceModel):
    """Compatibility wrapper for the 8x8 relaxed quantum configuration."""

    def __init__(self, config: Dict[str, Any]) -> None:
        merged_config = dict(config)
        merged_config["hilbert_dimension"] = 8
        merged_config.setdefault("dephasing_gamma", 0.05)
        merged_config.setdefault("engine_family", "extended_quantum")
        super().__init__(merged_config)
