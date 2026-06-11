"""Plotly HTML Report Generator for Octahedral gTRQC Simulation.

This module extends the MVP View layer to automatically generate interactive
HTML standalone visualizations for each physical goal analyzed in the simulation.
"""

import os
from typing import List, Dict, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class PlotlyHtmlView:
    """Graphics engine responsible for compiling metrics data into interactive HTML plots.
    
    Complies with document reporting goals by outputting individual charts 
    for coupling, protonic latency, capacity, and validation limits.
    """

    def __init__(self, output_dir: str = "reports") -> None:
        """Initializes the view engine and ensures target directories exist.

        Args:
            output_dir (str): Base directory path where HTML files will be written.
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_goals_1_2_chart(self, steps: List[int], voltages: List[float], rhos: List[float], distortions: List[float]) -> str:
        """Generates the Dynamic Geometry-Matter Coupling and Hysteresis chart.

        Args:
            steps (List[int]): Simulation execution step index array.
            voltages (List[float]): Applied driving voltage profile vector.
            rhos (List[float]): Quantum density matrix proxy trajectory.
            distortions (List[float]): Octahedral cage geometric distortion metric.

        Returns:
            str: Absolute file path to the compiled HTML asset.
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Core Quantum Matter State trajectory
        fig.add_trace(
            go.Scatter(x=steps, y=rhos, name="Quantum Coherence (rho)", mode="lines+markers",
                       line=dict(color="blue", width=3)),
            secondary_y=False
        )

        # Structural Backreaction Cage Distortion trajectory
        fig.add_trace(
            go.Scatter(x=steps, y=distortions, name="Octahedral Distortion", mode="lines+markers",
                       line=dict(color="crimson", width=3, dash="dash")),
            secondary_y=True
        )

        # Voltage reference profile overlay
        fig.add_trace(
            go.Scatter(x=steps, y=voltages, name="Driving Voltage V(t)", mode="markers",
                       marker=dict(size=12, symbol="diamond", color="gold")),
            secondary_y=False
        )

        fig.update_layout(
            title="<b>Goals 1 & 2: Quantum-Geometric Coupling Profile</b><br>H_xNdNiO_3 Memory Trajectory",
            xaxis_title="Simulation Time Steps (Discrete Delta t)",
            template="plotly_dark",
            legend=dict(x=0.05, y=0.95)
        )

        fig.update_yaxes(title_text="Quantum Matter Proxy State (rho)", secondary_y=False)
        fig.update_yaxes(title_text="Structural Distortion (Angular/Volumetric)", secondary_y=True)

        path = os.path.join(self.output_dir, "goal_1_2_coupling.html")
        fig.write_html(path)
        return path

    def generate_goal_3_chart(self, steps: List[int], j_raw: List[float], j_eff: List[float]) -> str:
        """Generates the Protonic Latency and Non-Markovian Delay Line chart.

        Args:
            steps (List[int]): Simulation execution step index array.
            j_raw (List[float]): Instantaneous raw generation source.
            j_eff (List[float]): Delayed effective backreaction source.

        Returns:
            str: Absolute file path to the compiled HTML asset.
        """
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=steps, y=j_raw, name="Raw Source J(t)", mode="lines",
                                 line=dict(color="cyan", width=2, dash="dot")))
        fig.add_trace(go.Scatter(x=steps, y=j_eff, name="Effective Protonic Delayed Source J_eff(t - d_elay)", mode="lines+markers",
                                 line=dict(color="lime", width=3)))

        fig.update_layout(
            title="<b>Goal 3: Non-Markovian Protonic Latency Validation</b><br>Memory Horizon Retardation Phase Shifts",
            xaxis_title="Time Steps",
            yaxis_title="Coupling Source Strength (Arbitrary Units)",
            template="plotly_dark"
        )

        path = os.path.join(self.output_dir, "goal_3_latency.html")
        fig.write_html(path)
        return path

    def generate_goal_4_chart(self, epsilons: List[float], capacities: List[float]) -> str:
        """Generates the Kolmogorov-Tikhomirov Entropic Memory Capacity scaling chart.

        Args:
            epsilons (List[float]): Resolution bounds sampling vector.
            capacities (List[float]): Computed C_atom(epsilon) values vector.

        Returns:
            str: Absolute file path to the compiled HTML asset.
        """
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=epsilons, y=capacities, mode="lines+markers",
                                 line=dict(color="darkorange", width=3),
                                 marker=dict(size=8)))

        fig.update_layout(
            title="<b>Goal 4: Kolmogorov Atomic Information Capacity Bound</b><br>Scaling limits as epsilon resolution narrows",
            xaxis_title="Resolution Boundary Metric (Epsilon)",
            yaxis_title="Entropy Capacity Log(N_eps)",
            xaxis_autorange="reversed",  # Standard representation showing epsilon going to 0
            template="plotly_dark"
        )

        path = os.path.join(self.output_dir, "goal_4_capacity.html")
        fig.write_html(path)
        return path

    def generate_goal_5_chart(self, steps: List[int], null_j_eff: List[float], null_j_0: List[float]) -> str:
        """Generates the Thermodynamic Null-Test Energy Conservation chart.

        Args:
            steps (List[int]): Simulation execution step index array.
            null_j_eff (List[float]): Effective source tracker under Delta_0 = 0.
            null_j_0 (List[float]): Vector gradient projection under Delta_0 = 0.

        Returns:
            str: Absolute file path to the compiled HTML asset.
        """
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=steps, y=null_j_eff, name="Null J_eff", mode="lines+markers", line=dict(color="purple", width=3)))
        fig.add_trace(go.Scatter(x=steps, y=null_j_0, name="Null J_0 (Gradient Backreaction)", mode="lines", line=dict(color="grey", width=2, dash="dash")))

        fig.update_layout(
            title="<b>Goal 5: Null-Test Dynamic Source Preservation</b><br>Assertion of Zero Field Response when Delta_0 = 0",
            xaxis_title="Time Steps",
            yaxis_title="Source Amplitude Matrix Limits",
            yaxis=dict(range=[-0.5, 0.5]),
            template="plotly_dark"
        )

        path = os.path.join(self.output_dir, "goal_5_null_test.html")
        fig.write_html(path)
        return path




"""Markdown Experiment Logger for Octahedral gTRQC Simulation.

Extends the reporting suite to automatically write tabular textual summaries
and execution metrics to standalone Markdown files.
"""

import os
from typing import List, Dict, Any


class MarkdownReportView:
    """Handles the serialization of simulation execution data into readable Markdown tables."""

    def __init__(self, output_dir: str = "reports") -> None:
        """Initializes the markdown reporting engine.

        Args:
            output_dir (str): Destination directory for the telemetry summary file.
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def write_summary_report(self,
                             config: Dict[str, Any],
                             steps: List[int],
                             voltages: List[float],
                             rhos: List[float],
                             distortions: List[float],
                             capacity_sweep: Dict[float, float],
                             final_state: Dict[str, Any]) -> str:
        """Compiles configurations, timelines, and goal evaluations into a Markdown file.

        Args:
            config (Dict[str, Any]): Full execution configuration map used by the Presenter.
            steps (List[int]): Array of step indexes.
            voltages (List[float]): Checked voltage profile.
            rhos (List[float]): Calculated density matrix trace history.
            distortions (List[float]): Evaluated physical cage distortion history.
            capacity_sweep (Dict[float, float]): Goal 4 resolution-to-capacity pairs.
            final_state (Dict[str, Any]): Dictionary describing the terminal register state.

        Returns:
            str: Path to the generated report file.
        """
        report_path = os.path.join(self.output_dir, "report.md")

        md_content = []
        md_content.append("# Octahedral gTRQC Simulation Execution Summary Report")
        md_content.append(f"**Target Application Core:** Hydrogenated Neodymium Nickelate ($H_xNdNiO_3$)\n")

        # 1. Metadatos del Experimento (Configuración Inicial)
        md_content.append("## 1. Initial Experimental Context Parameters")
        md_content.append("| Parameter Configuration | Applied Value |")
        md_content.append("| :--- | :--- |")
        md_content.append(f"| Total Configured Simulation Steps | {config.get('simulation_steps')} |")
        md_content.append(f"| G_oct Graphistic Stiffness Coefficient | {config.get('g_oct_stiffness')} |")
        md_content.append(f"| Protonic Latency Delay Steps ($d_{{elay}}$) | {config.get('protonic_delay_steps')} |")
        md_content.append(f"| Base Resolution Boundary ($\\epsilon$) | {config.get('epsilon_bound')} |")
        md_content.append(f"| Initial Boundary Coherence state ($\\rho_{{0}}$) | {config.get('initial_rho')} |\n")

        # 2. Tabla Principal de Evolución Temporal (Goals 1, 2 & 3)
        md_content.append("## 2. Matter-Geometry Quantum Coupling Timeline Trajectory")
        md_content.append("| Step | Applied Voltage V(t) | Quantum Coherence (rho) | Octahedral Cage Distortion |")
        md_content.append("| :---: | :---: | :---: | :---: |")
        for i in range(len(steps)):
            md_content.append(f"| {steps[i]:03d} | {voltages[i]:.2f} V | {rhos[i]:.4f} | {distortions[i]:.4f} |")
        md_content.append("\n")

        # 3. Muestreo de Capacidad de Kolmogorov (Goal 4)
        md_content.append("## 3. Goal 4: Kolmogorov-Tikhomirov Entropy Capacity Bounds")
        md_content.append("| Resolution Boundary Condition ($\\epsilon$) | Atomic Memory Capacity $C_{{atom}}(\\epsilon)$ |")
        md_content.append("| :---: | :---: |")
        for eps, cap in capacity_sweep.items():
            md_content.append(f"| {eps:.3f} | {cap:.4f} |")
        md_content.append("\n")

        # 4. Estado de Salida del Registro de Memoria
        md_content.append("## 4. Terminal Octahedral Geometrical Register Metrics")
        reg = final_state.get("register", {})
        md_content.append(f"- **Final Quantum Matrix Proxy ($\\rho_{{final}}$):** {final_state.get('rho')}")
        md_content.append(f"- **Octahedral Tilting Angle ($\\theta_{{tilt}}$):** {reg.get('theta_tilt', 0.0):.6f}")
        md_content.append(f"- **Octahedral Rotation Angle ($\\theta_{{rot}}$):** {reg.get('theta_rot', 0.0):.6f}")
        md_content.append(f"- **Cage Volume Displacement ($\\delta V_{{oct}}$):** {reg.get('delta_V_oct', 0.0):.6f}")
        md_content.append(f"- **Ni-O-Ni Bond Angular Deviation ($\\delta\\phi$):** {reg.get('delta_phi', 0.0):.6f}")
        md_content.append(f"- **Protonic Buffer Remanence Array:** {final_state.get('buffer')}\n")

        md_content.append("---")
        md_content.append("*Report automatically generated by the Octahedral gTRQC Suite.*")

        # Escribir el archivo
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))

        return report_path

