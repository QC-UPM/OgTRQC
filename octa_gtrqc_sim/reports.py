"""Plotly and Markdown report generators for Octahedral gTRQC Simulation."""

import os
from typing import Any, Dict, List

import plotly.graph_objects as go
from plotly.subplots import make_subplots


class ReportNamingMixin:
    def __init__(self, output_dir: str, hilbert_dimension_label: str) -> None:
        self.output_dir = output_dir
        self.hilbert_dimension_label = hilbert_dimension_label
        os.makedirs(self.output_dir, exist_ok=True)

    def _suffix(self) -> str:
        return f"hilbert_{self.hilbert_dimension_label}"

    def _artifact_filename(self, stem: str, extension: str) -> str:
        return f"{stem}_{self._suffix()}.{extension}"


class PlotlyHtmlView(ReportNamingMixin):
    """Graphics engine responsible for compiling metrics data into interactive HTML plots."""

    def __init__(self, output_dir: str = "reports", hilbert_dimension_label: str = "scalar_proxy") -> None:
        super().__init__(output_dir=output_dir, hilbert_dimension_label=hilbert_dimension_label)

    def generate_goals_1_2_chart(
        self,
        steps: List[int],
        voltages: List[float],
        rhos: List[float],
        distortions: List[float],
    ) -> str:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(
                x=steps,
                y=rhos,
                name="Quantum Coherence (rho)",
                mode="lines+markers",
                line=dict(color="blue", width=3),
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=steps,
                y=distortions,
                name="Octahedral Distortion",
                mode="lines+markers",
                line=dict(color="crimson", width=3, dash="dash"),
            ),
            secondary_y=True,
        )
        fig.add_trace(
            go.Scatter(
                x=steps,
                y=voltages,
                name="Driving Voltage V(t)",
                mode="markers",
                marker=dict(size=12, symbol="diamond", color="gold"),
            ),
            secondary_y=False,
        )
        fig.update_layout(
            title=(
                "<b>Goals 1 & 2: Quantum-Geometric Coupling Profile</b>"
                f"<br>H_xNdNiO_3 Memory Trajectory | Hilbert {self.hilbert_dimension_label}"
            ),
            xaxis_title="Simulation Time Steps (Discrete Delta t)",
            template="plotly_dark",
            legend=dict(x=0.05, y=0.95),
        )
        fig.update_yaxes(title_text="Quantum Matter Proxy State (rho)", secondary_y=False)
        fig.update_yaxes(title_text="Structural Distortion (Angular/Volumetric)", secondary_y=True)
        path = os.path.join(self.output_dir, self._artifact_filename("goal_1_2_coupling", "html"))
        fig.write_html(path)
        return path

    def generate_goal_3_chart(self, steps: List[int], j_raw: List[float], j_eff: List[float]) -> str:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=steps,
                y=j_raw,
                name="Raw Source J(t)",
                mode="lines",
                line=dict(color="cyan", width=2, dash="dot"),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=steps,
                y=j_eff,
                name="Effective Protonic Delayed Source J_eff(t - d_elay)",
                mode="lines+markers",
                line=dict(color="lime", width=3),
            )
        )
        fig.update_layout(
            title=(
                "<b>Goal 3: Non-Markovian Protonic Latency Validation</b>"
                f"<br>Memory Horizon Retardation Phase Shifts | Hilbert {self.hilbert_dimension_label}"
            ),
            xaxis_title="Time Steps",
            yaxis_title="Coupling Source Strength (Arbitrary Units)",
            template="plotly_dark",
        )
        path = os.path.join(self.output_dir, self._artifact_filename("goal_3_latency", "html"))
        fig.write_html(path)
        return path

    def generate_goal_4_chart(self, epsilons: List[float], capacities: List[float]) -> str:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=epsilons,
                y=capacities,
                mode="lines+markers",
                line=dict(color="darkorange", width=3),
                marker=dict(size=8),
            )
        )
        fig.update_layout(
            title=(
                "<b>Goal 4: Heuristic Resolution Indicator</b>"
                f"<br>Conductance-coupled proxy as epsilon narrows | Hilbert {self.hilbert_dimension_label}"
            ),
            xaxis_title="Resolution Boundary Metric (Epsilon)",
            yaxis_title="Heuristic Resolution Estimate H_res(epsilon)",
            xaxis_autorange="reversed",
            template="plotly_dark",
        )
        path = os.path.join(self.output_dir, self._artifact_filename("goal_4_resolution_heuristic", "html"))
        fig.write_html(path)
        return path

    def generate_goal_5_chart(self, steps: List[int], null_j_eff: List[float], null_j_0: List[float]) -> str:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=steps, y=null_j_eff, name="Null J_eff", mode="lines+markers", line=dict(color="purple", width=3))
        )
        fig.add_trace(
            go.Scatter(x=steps, y=null_j_0, name="Null J_0 (Gradient Backreaction)", mode="lines", line=dict(color="grey", width=2, dash="dash"))
        )
        fig.update_layout(
            title=(
                "<b>Goal 5: Null-Test Dynamic Source Preservation</b>"
                f"<br>Assertion of Zero Field Response when Delta_0 = 0 | Hilbert {self.hilbert_dimension_label}"
            ),
            xaxis_title="Time Steps",
            yaxis_title="Source Amplitude Matrix Limits",
            yaxis=dict(range=[-0.5, 0.5]),
            template="plotly_dark",
        )
        path = os.path.join(self.output_dir, self._artifact_filename("goal_5_null_test", "html"))
        fig.write_html(path)
        return path


class MarkdownReportView(ReportNamingMixin):
    """Handles the serialization of simulation execution data into readable Markdown tables."""

    def __init__(self, output_dir: str = "reports", hilbert_dimension_label: str = "scalar_proxy") -> None:
        super().__init__(output_dir=output_dir, hilbert_dimension_label=hilbert_dimension_label)

    def write_summary_report(
        self,
        config: Dict[str, Any],
        steps: List[int],
        voltages: List[float],
        rhos: List[float],
        distortions: List[float],
        capacity_sweep: Dict[float, float],
        final_state: Dict[str, Any],
    ) -> str:
        report_path = os.path.join(self.output_dir, self._artifact_filename("report", "md"))
        md_content: List[str] = []
        md_content.append("# Octahedral gTRQC Simulation Execution Summary Report")
        md_content.append(f"**Target Application Core:** Hydrogenated Neodymium Nickelate ($H_xNdNiO_3$)")
        md_content.append(f"**Hilbert Space Declaration:** {self.hilbert_dimension_label}\n")
        md_content.append("## 1. Initial Experimental Context Parameters")
        md_content.append("| Parameter Configuration | Applied Value |")
        md_content.append("| :--- | :--- |")
        md_content.append(f"| Total Configured Simulation Steps | {config.get('simulation_steps')} |")
        md_content.append(f"| Hilbert Dimension | {self.hilbert_dimension_label} |")
        md_content.append(f"| G_oct Graphistic Stiffness Coefficient | {config.get('g_oct_stiffness')} |")
        md_content.append(f"| Protonic Latency Delay Steps ($d_{{elay}}$) | {config.get('protonic_delay_steps')} |")
        md_content.append(f"| Base Resolution Boundary ($\\epsilon$) | {config.get('epsilon_bound')} |")
        md_content.append(f"| Initial Boundary Coherence state ($\\rho_{{0}}$) | {config.get('initial_rho')} |\n")
        md_content.append("## 2. Matter-Geometry Quantum Coupling Timeline Trajectory")
        md_content.append("| Step | Applied Voltage V(t) | Quantum Coherence (rho) | Octahedral Cage Distortion |")
        md_content.append("| :---: | :---: | :---: | :---: |")
        for i in range(len(steps)):
            md_content.append(f"| {steps[i]:03d} | {voltages[i]:.2f} V | {rhos[i]:.4f} | {distortions[i]:.4f} |")
        md_content.append("\n")
        md_content.append("## 3. Goal 4: Heuristic Resolution Indicator")
        md_content.append("The formal Kolmogorov-Tikhomirov capacity over expansive tensor networks is acknowledged as a tractable but computationally prohibitive target for this initial proof of concept. Therefore, Goal 4 reports a conductance-coupled heuristic scalar indicator instead of claiming an exact metric-entropy computation.\n")
        md_content.append("| Resolution Boundary Condition ($\\epsilon$) | Heuristic Resolution Estimate $H_{{res}}(\\epsilon)$ |")
        md_content.append("| :---: | :---: |")
        for eps, cap in capacity_sweep.items():
            md_content.append(f"| {eps:.3f} | {cap:.4f} |")
        md_content.append("\n")
        md_content.append("## 4. Terminal Octahedral Geometrical Register Metrics")
        reg = final_state.get("register", {})
        md_content.append(f"- **Final Quantum Matrix Proxy ($\\rho_{{final}}$):** {final_state.get('rho')}")
        md_content.append(f"- **Hilbert Space Declaration:** {final_state.get('hilbert_dimension_label', self.hilbert_dimension_label)}")
        md_content.append(f"- **Hidden Binary Subsystems:** {final_state.get('hidden_site_count', 'n/a')}")
        md_content.append(f"- **Octahedral Tilting Angle ($\\theta_{{tilt}}$):** {reg.get('theta_tilt', 0.0):.6f}")
        md_content.append(f"- **Octahedral Rotation Angle ($\\theta_{{rot}}$):** {reg.get('theta_rot', 0.0):.6f}")
        md_content.append(f"- **Cage Volume Displacement ($\\delta V_{{oct}}$):** {reg.get('delta_V_oct', 0.0):.6f}")
        md_content.append(f"- **Ni-O-Ni Bond Angular Deviation ($\\delta\\phi$):** {reg.get('delta_phi', 0.0):.6f}")
        if 'buffer' in final_state:
            md_content.append(f"- **Protonic Buffer Remanence Array:** {final_state.get('buffer')}")
        md_content.append("\n---")
        md_content.append("*Report automatically generated by the Octahedral gTRQC Suite.*")
        with open(report_path, "w", encoding="utf-8") as file_stream:
            file_stream.write("\n".join(md_content))
        return report_path
