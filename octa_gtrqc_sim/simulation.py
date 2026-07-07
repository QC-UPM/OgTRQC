"""Reusable simulation helpers for standard runs and robustness studies."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Protocol, Sequence, Tuple

import yaml

from octa_gtrqc_sim.causal_integrator import CausalSufficiencyModel
from octa_gtrqc_sim.causal_recovery import RelaxedCausalModel
from octa_gtrqc_sim.extended_recovery import ExtendedRelaxedCausalModel, ExtendedRelaxedQuantumModel
from octa_gtrqc_sim.legacy_memory import OctaMemoryModel
from octa_gtrqc_sim.quantum_memory import QuantumMemoryModel
from octa_gtrqc_sim.quantum_recovery import RelaxedQuantumModel
from octa_gtrqc_sim.reports import MarkdownReportView, PlotlyHtmlView
from octa_gtrqc_sim.scalable_hilbert import ScalableHilbertSpaceModel


class MemoryModel(Protocol):
    """Structural protocol implemented by all simulation engines."""

    hilbert_dimension_label: str

    def step(self, V_t: float, delta_0: float) -> Dict[str, float]:
        """Advance the engine by one time step."""

    def estimate_resolution_heuristic(self, epsilon: float) -> float:
        """Estimate the heuristic resolution indicator."""

    def get_state(self) -> Dict[str, Any]:
        """Return the current state snapshot."""


DEFAULT_CONFIG: Dict[str, Any] = {
    "engine": "legacy",
    "topology": "octa",
    "output_directory": "reports",
    "simulation_steps": 6,
    "g_oct_stiffness": 3.0,
    "protonic_delay_steps": 2,
    "epsilon_bound": 0.02,
    "time_step": 0.1,
    "numerical_tolerance": 1e-9,
    "initial_rho": 1.0,
    "initial_density_population": 1.0,
    "ni_transverse_hopping": 0.8,
    "dephasing_gamma": 0.05,
    "hilbert_dimension": 8,
    "proton_hopping_energy": 0.5,
    "inter_site_hopping": 0.2,
    "electron_proton_coupling": 1.2,
    "initial_register": {
        "theta_tilt": 0.12,
        "theta_rot": 0.06,
        "delta_V_oct": 0.0,
        "delta_phi": 0.03,
        "epsilon_0": 1.0,
    },
}


@dataclass(frozen=True)
class SimulationTrace:
    """Structured output of a simulation run.

    Attributes:
        step_axis: One-based simulation step indices.
        voltages: Applied voltages by step.
        recoverability_loss: Recoverability-loss proxy by step.
        rhos: Scalar matter observable by step.
        distortions: Structural distortion by step.
        raw_sources: Instantaneous raw source by step.
        effective_sources: Effective delayed or endogenous source by step.
        epsilon_sweep: Resolution thresholds used for heuristic evaluation.
        heuristic_values: Heuristic resolution values aligned with ``epsilon_sweep``.
        final_state: Final state snapshot returned by the selected engine.
        null_test_passed: Whether the embedded null-test check passed.
    """

    step_axis: List[int]
    voltages: List[float]
    recoverability_loss: List[float]
    rhos: List[float]
    distortions: List[float]
    raw_sources: List[float]
    effective_sources: List[float]
    epsilon_sweep: List[float]
    heuristic_values: List[float]
    final_state: Dict[str, Any]
    null_test_passed: bool


def build_default_config() -> Dict[str, Any]:
    """Return a deep-copyable default configuration dictionary.

    Returns:
        Default runtime configuration.
    """
    default_copy = dict(DEFAULT_CONFIG)
    default_copy["initial_register"] = dict(DEFAULT_CONFIG["initial_register"])
    return default_copy


def merge_config(base_config: Mapping[str, Any], overrides: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Merge a base configuration with optional overrides.

    Args:
        base_config: Base configuration dictionary.
        overrides: Optional override dictionary.

    Returns:
        Merged configuration dictionary.
    """
    merged = dict(base_config)
    merged["initial_register"] = dict(base_config.get("initial_register", {}))
    if not overrides:
        return merged
    for key, value in overrides.items():
        if key == "initial_register" and isinstance(value, Mapping):
            merged["initial_register"].update(value)
        else:
            merged[key] = value
    return merged


def load_config(config_path: Optional[str]) -> Dict[str, Any]:
    """Load the runtime configuration from disk when a YAML path is provided.

    Args:
        config_path: Optional YAML configuration path.

    Returns:
        Runtime configuration dictionary.
    """
    config = build_default_config()
    if not config_path or not os.path.exists(config_path):
        return config
    with open(config_path, "r", encoding="utf-8") as file_stream:
        user_config = yaml.safe_load(file_stream)
    if user_config and isinstance(user_config, dict):
        config = merge_config(config, user_config)
    return config


def instantiate_model(config: Mapping[str, Any]) -> MemoryModel:
    """Instantiate the simulation engine selected in ``config``.

    Args:
        config: Runtime configuration dictionary.

    Returns:
        Concrete memory-model instance.

    Raises:
        ValueError: If the engine alias is not recognized.
    """
    engine_type = str(config.get("engine", "legacy"))
    runtime_config = dict(config)
    if engine_type == "causal":
        model: MemoryModel = CausalSufficiencyModel(runtime_config)
        model.hilbert_dimension_label = "4x4"
        return model
    if engine_type == "quantum":
        model = QuantumMemoryModel(runtime_config)
        model.hilbert_dimension_label = "2x2"
        return model
    if engine_type == "legacy":
        return OctaMemoryModel(runtime_config)
    if engine_type == "relaxed_quantum":
        return RelaxedQuantumModel(runtime_config)
    if engine_type == "relaxed_causal":
        return RelaxedCausalModel(runtime_config)
    if engine_type == "extended_quantum":
        return ExtendedRelaxedQuantumModel(runtime_config)
    if engine_type == "extended_causal":
        return ExtendedRelaxedCausalModel(runtime_config)
    if engine_type == "scalable_relaxed":
        return ScalableHilbertSpaceModel(runtime_config)
    raise ValueError(f"Unrecognized mathematical integration engine: {engine_type}")


def generate_analytical_profiles(steps: int) -> Tuple[List[float], List[float]]:
    """Generate the built-in driving profiles used by the presenter.

    Args:
        steps: Number of discrete simulation steps.

    Returns:
        Tuple containing voltage and recoverability-loss profiles.
    """
    voltage_profile: List[float] = []
    recoverability_profile: List[float] = []
    for step_index in range(steps):
        voltage = 1.5 * math.sin(math.pi * step_index / (steps / 2.0)) * math.exp(-step_index / (steps * 1.5))
        voltage_profile.append(max(0.0, float(voltage)))
        recoverability = 0.3 * math.exp(-math.pow(step_index - (steps / 3.0), 2) / (steps * 0.5))
        recoverability_profile.append(float(recoverability))
    return voltage_profile, recoverability_profile


def run_simulation_trace(config: Mapping[str, Any]) -> SimulationTrace:
    """Run a simulation and return its full trace without side effects.

    Args:
        config: Runtime configuration dictionary.

    Returns:
        Structured simulation trace.
    """
    runtime_config = dict(config)
    total_steps = runtime_config.get("simulation_steps", 6)
    if not isinstance(total_steps, int) or total_steps <= 0:
        total_steps = 6

    model = instantiate_model(runtime_config)
    voltage_profile, recoverability_loss = generate_analytical_profiles(total_steps)

    step_axis: List[int] = []
    history_rhos: List[float] = []
    history_distortions: List[float] = []
    history_raw_sources: List[float] = []
    history_eff_sources: List[float] = []

    for step_index in range(total_steps):
        metrics = model.step(voltage_profile[step_index], recoverability_loss[step_index])
        step_axis.append(step_index + 1)
        history_rhos.append(metrics["rho"])
        history_distortions.append(metrics["distortion"])
        history_raw_sources.append(metrics.get("raw_source", 0.0))
        history_eff_sources.append(metrics.get("j_eff", metrics.get("endogenous_delta", 0.0)))

    epsilon_sweep = list(runtime_config.get("goal_4_epsilon_sweep", [0.1, 0.05, 0.02, 0.01, 0.005]))
    heuristic_values = [model.estimate_resolution_heuristic(epsilon) for epsilon in epsilon_sweep]

    final_state = model.get_state()
    final_state["final_resolution_heuristic_estimation"] = model.estimate_resolution_heuristic(
        float(runtime_config.get("epsilon_bound", 0.05))
    )
    final_state.setdefault("hilbert_dimension_label", getattr(model, "hilbert_dimension_label", "scalar_proxy"))

    null_model = OctaMemoryModel(runtime_config)
    null_metrics = null_model.step(V_t=1.0, delta_0=0.0)
    null_test_passed = math.isclose(null_metrics["j_eff"], 0.0, abs_tol=1e-7) and math.isclose(
        null_metrics["j_0"], 0.0, abs_tol=1e-7
    )

    return SimulationTrace(
        step_axis=step_axis,
        voltages=voltage_profile,
        recoverability_loss=recoverability_loss,
        rhos=history_rhos,
        distortions=history_distortions,
        raw_sources=history_raw_sources,
        effective_sources=history_eff_sources,
        epsilon_sweep=epsilon_sweep,
        heuristic_values=heuristic_values,
        final_state=final_state,
        null_test_passed=null_test_passed,
    )


def write_standard_reports(config: Mapping[str, Any], trace: SimulationTrace) -> str:
    """Write the standard HTML and Markdown reports for a simulation trace.

    Args:
        config: Runtime configuration dictionary.
        trace: Simulation trace returned by :func:`run_simulation_trace`.

    Returns:
        Path to the generated Markdown summary report.
    """
    target_dir = str(config.get("output_directory", "reports"))
    hilbert_dimension_label = str(trace.final_state.get("hilbert_dimension_label", "scalar_proxy"))
    plotly_view = PlotlyHtmlView(output_dir=target_dir, hilbert_dimension_label=hilbert_dimension_label)
    plotly_view.generate_goals_1_2_chart(trace.step_axis, trace.voltages, trace.rhos, trace.distortions)
    plotly_view.generate_goal_3_chart(trace.step_axis, trace.raw_sources, trace.effective_sources)
    plotly_view.generate_goal_4_chart(trace.epsilon_sweep, trace.heuristic_values)

    capacity_sweep = {
        epsilon: heuristic for epsilon, heuristic in zip(trace.epsilon_sweep, trace.heuristic_values, strict=True)
    }
    md_logger = MarkdownReportView(output_dir=target_dir, hilbert_dimension_label=hilbert_dimension_label)
    return md_logger.write_summary_report(
        config=dict(config),
        steps=trace.step_axis,
        voltages=trace.voltages,
        rhos=trace.rhos,
        distortions=trace.distortions,
        capacity_sweep=capacity_sweep,
        final_state=trace.final_state,
    )
