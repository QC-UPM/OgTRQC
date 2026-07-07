"""Robustness-study workflow for the delayed quantum proof of concept."""

from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from octa_gtrqc_sim.simulation import (
    build_default_config,
    load_config,
    merge_config,
    run_simulation_trace,
)


@dataclass(frozen=True)
class RobustnessScenario:
    """Single-parameter perturbation used in the robustness study.

    Attributes:
        name: Stable scenario identifier.
        description: Human-readable description of the perturbation.
        overrides: Configuration overrides applied to the baseline configuration.
    """

    name: str
    description: str
    overrides: Dict[str, Any]


@dataclass(frozen=True)
class RobustnessRecord:
    """Summary metrics for one scenario-delay combination."""

    scenario: str
    description: str
    delay_steps: int
    time_step: float
    initial_density_population: float
    g_oct_stiffness: float
    dephasing_gamma: float
    numerical_tolerance: float
    topology: str
    geometry_scale: float
    final_rho: float
    final_distortion: float
    peak_distortion: float
    mean_distortion: float
    peak_effective_source: float
    mean_abs_source_gap: float
    null_test_passed: bool


def default_quantum_scenarios() -> List[RobustnessScenario]:
    """Return the default one-at-a-time perturbations for the quantum engine.

    Returns:
        List of default robustness scenarios.
    """
    return [
        RobustnessScenario("baseline", "Reference quantum delayed-memory configuration.", {}),
        RobustnessScenario("time_step_low", "Halved integration time step.", {"time_step": 0.05}),
        RobustnessScenario("time_step_high", "Doubled integration time step.", {"time_step": 0.2}),
        RobustnessScenario(
            "initial_population_low",
            "Lower initial matter-state population in the visible basis state.",
            {"initial_density_population": 0.25, "initial_rho": 0.25},
        ),
        RobustnessScenario(
            "initial_population_mid",
            "Mixed initial matter-state population in the visible basis state.",
            {"initial_density_population": 0.5, "initial_rho": 0.5},
        ),
        RobustnessScenario("feedback_low", "Reduced backreaction stiffness.", {"g_oct_stiffness": 1.5}),
        RobustnessScenario("feedback_high", "Increased backreaction stiffness.", {"g_oct_stiffness": 4.5}),
        RobustnessScenario("dephasing_low", "No dephasing channel.", {"dephasing_gamma": 0.0}),
        RobustnessScenario("dephasing_high", "Enhanced dephasing channel.", {"dephasing_gamma": 0.15}),
        RobustnessScenario("tolerance_loose", "Looser numerical tolerance.", {"numerical_tolerance": 1e-6}),
        RobustnessScenario("tolerance_tight", "Tighter numerical tolerance.", {"numerical_tolerance": 1e-12}),
        RobustnessScenario("topology_ring", "Ring graph topology with the same six-node size.", {"topology": "ring_6"}),
        RobustnessScenario("topology_chain", "Chain graph topology with the same six-node size.", {"topology": "chain_6"}),
        RobustnessScenario("topology_star", "Star graph topology with the same six-node size.", {"topology": "star_6"}),
        RobustnessScenario("topology_complete", "Complete graph topology with the same six-node size.", {"topology": "complete_6"}),
        RobustnessScenario(
            "geometry_soft",
            "Smaller initial octahedral register amplitudes.",
            {
                "initial_register": {
                    "theta_tilt": 0.06,
                    "theta_rot": 0.03,
                    "delta_phi": 0.015,
                }
            },
        ),
        RobustnessScenario(
            "geometry_strong",
            "Larger initial octahedral register amplitudes.",
            {
                "initial_register": {
                    "theta_tilt": 0.18,
                    "theta_rot": 0.09,
                    "delta_phi": 0.045,
                }
            },
        ),
    ]


def _geometry_scale(config: Mapping[str, Any]) -> float:
    """Estimate a simple geometry-initialization scale factor.

    Args:
        config: Scenario-specific runtime configuration.

    Returns:
        Relative scale of the initial geometric amplitudes.
    """
    register = config.get("initial_register", {})
    numerator = float(register.get("theta_tilt", 0.0)) + float(register.get("theta_rot", 0.0)) + abs(
        float(register.get("delta_phi", 0.0))
    )
    denominator = 0.12 + 0.06 + 0.03
    return numerator / denominator if denominator else 1.0


def summarize_trace(
    scenario: RobustnessScenario,
    config: Mapping[str, Any],
    delay_steps: int,
) -> RobustnessRecord:
    """Run one scenario-delay configuration and summarize the resulting trace.

    Args:
        scenario: Robustness scenario definition.
        config: Fully merged runtime configuration.
        delay_steps: Delay length in simulation steps.

    Returns:
        Summary metrics for the run.
    """
    trace = run_simulation_trace(config)
    return RobustnessRecord(
        scenario=scenario.name,
        description=scenario.description,
        delay_steps=delay_steps,
        time_step=float(config.get("time_step", 0.1)),
        initial_density_population=float(config.get("initial_density_population", config.get("initial_rho", 1.0))),
        g_oct_stiffness=float(config.get("g_oct_stiffness", 0.0)),
        dephasing_gamma=float(config.get("dephasing_gamma", 0.0)),
        numerical_tolerance=float(config.get("numerical_tolerance", 1e-9)),
        topology=str(config.get("topology", "octa")),
        geometry_scale=_geometry_scale(config),
        final_rho=trace.rhos[-1],
        final_distortion=trace.distortions[-1],
        peak_distortion=max(trace.distortions),
        mean_distortion=mean(trace.distortions),
        peak_effective_source=max(abs(value) for value in trace.effective_sources),
        mean_abs_source_gap=mean(abs(raw - eff) for raw, eff in zip(trace.raw_sources, trace.effective_sources, strict=True)),
        null_test_passed=trace.null_test_passed,
    )


def run_quantum_robustness_study(
    base_config: Optional[Mapping[str, Any]] = None,
    delay_values: Sequence[int] = (0, 1, 2, 5),
    scenarios: Optional[Sequence[RobustnessScenario]] = None,
) -> List[RobustnessRecord]:
    """Run the default delay-focused robustness study on the quantum engine.

    Args:
        base_config: Optional baseline configuration.
        delay_values: Delay steps tested in each scenario.
        scenarios: Optional custom scenario sequence.

    Returns:
        Flat list of scenario-delay summary records.
    """
    baseline = merge_config(build_default_config(), base_config or {})
    baseline["engine"] = "quantum"
    scenario_list = list(scenarios or default_quantum_scenarios())

    records: List[RobustnessRecord] = []
    for scenario in scenario_list:
        scenario_config = merge_config(baseline, scenario.overrides)
        for delay_steps in delay_values:
            run_config = merge_config(
                scenario_config,
                {
                    "protonic_delay_steps": int(delay_steps),
                    "engine": "quantum",
                },
            )
            records.append(summarize_trace(scenario, run_config, delay_steps))
    return records


def _records_to_rows(records: Iterable[RobustnessRecord]) -> List[Dict[str, Any]]:
    """Convert summary records into JSON/CSV-friendly row dictionaries."""
    return [record.__dict__.copy() for record in records]


def _write_json(path: str, rows: Sequence[Mapping[str, Any]]) -> None:
    """Write study rows to a JSON file.

    Args:
        path: Output JSON path.
        rows: JSON-serializable row dictionaries.
    """
    with open(path, "w", encoding="utf-8") as file_stream:
        json.dump(list(rows), file_stream, indent=2)


def _write_csv(path: str, rows: Sequence[Mapping[str, Any]]) -> None:
    """Write study rows to a CSV file.

    Args:
        path: Output CSV path.
        rows: Row dictionaries.
    """
    if not rows:
        return
    with open(path, "w", encoding="utf-8", newline="") as file_stream:
        writer = csv.DictWriter(file_stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: str, rows: Sequence[Mapping[str, Any]], delay_values: Sequence[int]) -> None:
    """Write a concise Markdown narrative for the robustness study.

    Args:
        path: Output Markdown path.
        rows: Study rows.
        delay_values: Delay values tested in the study.
    """
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["scenario"]), []).append(row)

    lines: List[str] = [
        "# Robustness Study Summary",
        "",
        "This report documents a delay-focused sensitivity analysis for the `quantum` engine.",
        f"Tested delay steps: {', '.join(str(value) for value in delay_values)}.",
        "",
        "The study varies one factor at a time around the baseline configuration: time step, initial matter-state population, feedback stiffness, dephasing strength, numerical tolerance, geometry initialization, and graph topology.",
        "",
        "Topology note: the present study now compares several built-in six-node graph topologies through reduced topology-aware couplings, but topology dependence should still be interpreted cautiously because not every engine carries a full node-resolved graph state.",
        "",
    ]

    baseline_rows = grouped.get("baseline", [])
    if baseline_rows:
        lines.extend(
            [
                "## Baseline Delay Trend",
                "",
                "| Delay steps | Peak distortion | Mean distortion | Final rho |",
                "| :---: | :---: | :---: | :---: |",
            ]
        )
        for row in baseline_rows:
            lines.append(
                f"| {row['delay_steps']} | {row['peak_distortion']:.6f} | {row['mean_distortion']:.6f} | {row['final_rho']:.6f} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Scenario Summary",
            "",
            "| Scenario | Topology | Delay steps | Peak distortion | Mean abs source gap | Null test |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['topology']} | {row['delay_steps']} | {row['peak_distortion']:.6f} | {row['mean_abs_source_gap']:.6f} | {'pass' if row['null_test_passed'] else 'fail'} |"
        )
    lines.append("")

    with open(path, "w", encoding="utf-8") as file_stream:
        file_stream.write("\n".join(lines))


def write_quantum_robustness_outputs(
    output_directory: str,
    records: Sequence[RobustnessRecord],
    delay_values: Sequence[int],
) -> Dict[str, str]:
    """Persist the robustness-study outputs to disk.

    Args:
        output_directory: Target directory for study artifacts.
        records: Summary records returned by the study runner.
        delay_values: Delay values used in the study.

    Returns:
        Mapping from artifact kind to output path.
    """
    os.makedirs(output_directory, exist_ok=True)
    rows = _records_to_rows(records)

    json_path = os.path.join(output_directory, "robustness_quantum_delay_study.json")
    csv_path = os.path.join(output_directory, "robustness_quantum_delay_study.csv")
    md_path = os.path.join(output_directory, "robustness_quantum_delay_study.md")

    _write_json(json_path, rows)
    _write_csv(csv_path, rows)
    _write_markdown(md_path, rows, delay_values)
    return {"json": json_path, "csv": csv_path, "markdown": md_path}


def main() -> None:
    """Run the robustness study from the command line."""
    parser = argparse.ArgumentParser(
        description="Run a delay-focused robustness study for the quantum octahedral gTRQC engine."
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        help="Optional YAML configuration file used as the baseline study configuration.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="robustness_reports",
        help="Directory where JSON, CSV, and Markdown outputs will be written.",
    )
    args = parser.parse_args()

    base_config = load_config(args.config)
    base_config["engine"] = "quantum"
    delay_values = (0, 1, 2, 5)
    records = run_quantum_robustness_study(base_config=base_config, delay_values=delay_values)
    outputs = write_quantum_robustness_outputs(args.output, records, delay_values)

    print("Robustness study completed.")
    for label, path in outputs.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
