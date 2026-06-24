"""4x4 wrapper over the scalable relaxed Hilbert engine."""

from typing import Any, Dict

from octa_gtrqc_sim.scalable_hilbert import ScalableHilbertSpaceModel


class RelaxedCausalModel(ScalableHilbertSpaceModel):
    """Compatibility wrapper for the 4x4 relaxed causal configuration."""

    def __init__(self, config: Dict[str, Any]) -> None:
        merged_config = dict(config)
        merged_config["hilbert_dimension"] = 4
        merged_config["dephasing_gamma"] = 0.0
        merged_config.setdefault("engine_family", "relaxed_causal")
        super().__init__(merged_config)
