"""Tests for the robustness-study workflow."""

from __future__ import annotations

from pathlib import Path

from octa_gtrqc_sim.robustness import (
    RobustnessScenario,
    run_quantum_robustness_study,
    write_quantum_robustness_outputs,
)
from octa_gtrqc_sim.simulation import build_default_config, run_simulation_trace


def test_run_simulation_trace_returns_expected_lengths() -> None:
    """The reusable simulation helper should emit aligned trajectory arrays."""
    config = build_default_config()
    config["engine"] = "quantum"
    config["simulation_steps"] = 5
    trace = run_simulation_trace(config)

    assert len(trace.step_axis) == 5
    assert len(trace.voltages) == 5
    assert len(trace.recoverability_loss) == 5
    assert len(trace.rhos) == 5
    assert len(trace.distortions) == 5
    assert len(trace.raw_sources) == 5
    assert len(trace.effective_sources) == 5
    assert trace.final_state["hilbert_dimension_label"] == "2x2"


def test_quantum_robustness_study_writes_outputs(tmp_path: Path) -> None:
    """The robustness-study workflow should write machine-readable outputs."""
    base_config = build_default_config()
    base_config["simulation_steps"] = 4
    base_config["topology"] = "octa"
    scenarios = [
        RobustnessScenario("baseline", "Baseline configuration.", {}),
        RobustnessScenario("feedback_low", "Reduced stiffness.", {"g_oct_stiffness": 2.0}),
        RobustnessScenario("topology_ring", "Ring topology.", {"topology": "ring_6"}),
    ]
    records = run_quantum_robustness_study(
        base_config=base_config,
        delay_values=(0, 2),
        scenarios=scenarios,
    )

    assert len(records) == 6
    assert {record.scenario for record in records} == {"baseline", "feedback_low", "topology_ring"}

    outputs = write_quantum_robustness_outputs(str(tmp_path), records, delay_values=(0, 2))
    for path in outputs.values():
        assert Path(path).exists()
