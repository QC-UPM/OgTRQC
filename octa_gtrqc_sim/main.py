"""Octahedral gTRQC Hydrogenated Nickelate Memory Simulation Suite.

This module provides a full non-Markovian simulation environment for analyzing
the interaction between quantum matter states and localized octahedral geometric
distortion registers inside hydrogenated rare-earth nickelates (H_xNdNiO_3).
"""

import argparse
import math
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import yaml
from octa_gtrqc_sim.reports import PlotlyHtmlView, MarkdownReportView

# =============================================================================
# i18n TRANSLATIONS DICTIONARY
# =============================================================================
I18N_DICT: Dict[str, Dict[str, str]] = {
    "en": {
        "welcome": "Starting Octahedral gTRQC Simulation...",
        "loading_config": "Loading parameters from configuration file: {path}",
        "running_goal": "Executing Simulation Goal {goal}: {desc}",
        "sim_step": "Step {step:03d} | V(t)={v:.2f}V | rho={rho:.4f} | Octa Distortion={dist:.4f}",
        "capacity_res": "Calculated Kolmogorov Atom Capacity C_atom(epsilon={eps}): {cap:.4f}",
        "null_test_pass": "Null-Test Verification Passed: Dynamic source vanishes under zero recoverability loss.",
        "null_test_fail": "Null-Test Verification Failed!",
        "done": "Simulation process completed successfully."
    },
    "es": {
        "welcome": "Iniciando la Simulación gTRQC Octaédrica...",
        "loading_config": "Cargando parámetros desde el archivo de configuración: {path}",
        "running_goal": "Ejecutando Objetivo de Simulación {goal}: {desc}",
        "sim_step": "Paso {step:03d} | V(t)={v:.2f}V | rho={rho:.4f} | Distorsión Octa={dist:.4f}",
        "capacity_res": "Capacidad Atómica de Kolmogorov C_atom(epsilon={eps}) calculada: {cap:.4f}",
        "null_test_pass": "Verificación de Prueba Nula Exitosa: El origen dinámico se desvanece con pérdida de recuperabilidad cero.",
        "null_test_fail": "¡Fallo en la Verificación de la Prueba Nula!",
        "done": "Proceso de simulación completado con éxito."
    },
    "fr": {
        "welcome": "Démarrage de la Simulation gTRQC Octaédrique...",
        "loading_config": "Chargement des paramètres depuis le fichier: {path}",
        "running_goal": "Exécution de l'Objectif de Simulation {goal}: {desc}",
        "sim_step": "Étape {step:03d} | V(t)={v:.2f}V | rho={rho:.4f} | Distorsion Octa={dist:.4f}",
        "capacity_res": "Capacité Atomique de Kolmogorov C_atom(epsilon={eps}) calculée: {cap:.4f}",
        "null_test_pass": "Vérification du Test Nul Réussie: La source dynamique s'annule sous une perte de récupérabilité nulle.",
        "null_test_fail": "Échec de la Vérification du Test Nul!",
        "done": "Processus de simulation terminé avec succès."
    },
    "de": {
        "welcome": "Starte oktaedrische gTRQC-Simulation...",
        "loading_config": "Lade Parameter aus der Konfigurationsdatei: {path}",
        "running_goal": "Ausführen von Simulationsziel {goal}: {desc}",
        "sim_step": "Schritt {step:03d} | V(t)={v:.2f}V | rho={rho:.4f} | Okta-Verzerrung={dist:.4f}",
        "capacity_res": "Berechnete Kolmogorov-Atomkapazität C_atom(epsilon={eps}): {cap:.4f}",
        "null_test_pass": "Nulltest-Verifizierung Bestanden: Dynamische Quelle verschwindet bei Null-Wiederherstellbarkeitsverlust.",
        "null_test_fail": "Nulltest-Verifizierung Fehlgeschlagen!",
        "done": "Simulationsprozess erfolgreich abgeschlossen."
    }
}


# =============================================================================
# MODEL LAYER
# =============================================================================
@dataclass
class MaterialRegister:
    """Represents the material octahedral curvature surrogate register vector.

    Attributes:
        theta_tilt (float): Octahedral tilting angle component.
        theta_rot (float): Octahedral rotation angle component.
        delta_V_oct (float): Local discrete change in octahedral cage volume.
        delta_phi (float): Deviation of the internal Ni-O-Ni bond angle.
        epsilon_0 (float): Baseline energy profile parameter.
    """
    theta_tilt: float
    theta_rot: float
    delta_V_oct: float
    delta_phi: float
    epsilon_0: float

    def to_vector(self) -> List[float]:
        """Flattens the register parameters into a mathematical float vector.

        Returns:
            List[float]: Vector list representing localized geometry configurations.
        """
        return [self.theta_tilt, self.theta_rot, self.delta_V_oct, self.delta_phi, self.epsilon_0]


class OctaMemoryModel:
    """Mathematical execution framework representing the H_xNdNiO_3 material system.

    Models the evolution of quantum matter coupled tightly to an octahedral physical geometry
    register through CPTP mappings, delayed protonic interactions, and backreaction sources.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initializes the structural material register state and operators.

        Args:
            config (Dict[str, Any]): Dictionary containing configuration variables.
        """
        reg_conf = config.get("initial_register", {})
        self.k_0 = MaterialRegister(
            theta_tilt=float(reg_conf.get("theta_tilt", 0.1)),
            theta_rot=float(reg_conf.get("theta_rot", 0.05)),
            delta_V_oct=float(reg_conf.get("delta_V_oct", 0.0)),
            delta_phi=float(reg_conf.get("delta_phi", 0.02)),
            epsilon_0=float(reg_conf.get("epsilon_0", 1.0))
        )
        self.rho: float = float(config.get("initial_rho", 1.0))  # Proxy for density matrix track
        self.g_oct: float = float(config.get("g_oct_stiffness", 2.5))  # Graphistic response scaling
        self.delay: int = int(config.get("protonic_delay_steps", 2))  # Latency steps (d_elay)
        self.delay_buffer: List[float] = [0.0] * self.delay

    def step(self, V_t: float, delta_0: float) -> Dict[str, float]:
        """Evaluates one discrete step delta_t of the matter-geometry system.

        Applies the delay history buffer, updates backreactions, alters the curvature register,
        and applies a Completely Positive Trace-Preserving (CPTP) proxy update map on rho.

        Args:
            V_t (float): Externally applied time-dependent driving potential voltage.
            delta_0 (float): Recoverability loss proxy value inside the functional space.

        Returns:
            Dict[str, float]: Dictionary containing computed metrics at current execution frame.
        """
        # Step 1: Handle non-Markovian feedback delay buffer logic (J_eff calculation)
        raw_source = delta_0 * self.g_oct
        self.delay_buffer.append(raw_source)
        j_eff = self.delay_buffer.pop(0)

        # Step 2: Compute Backreaction source vector gradient surrogate
        # J_0 = Grad_{k_0}(Delta_0). Simulating gradient interaction via linear projection.
        j_0 = j_eff * sum(self.k_0.to_vector())

        # Step 3: Compute evolution of geometry register towards equilibrium: G_oct * delta_k0 = -J_0
        delta_k = -j_0 / (self.g_oct + 1e-9)
        self.k_0.theta_tilt += delta_k * 0.1
        self.k_0.theta_rot += delta_k * 0.05
        self.k_0.delta_V_oct += delta_k * 0.2

        # Step 4: Apply CPTP Proxy Map to Matter State (rho updates bounded between 0.0 and 1.0)
        # Structural deformation limits overall quantum phase coherence space
        structural_distortion = sum(abs(x) for x in self.k_0.to_vector()[:3])
        interaction_hamiltonian = 0.5 * V_t - 0.2 * structural_distortion
        
        self.rho = max(0.0, min(1.0, self.rho - 0.05 * interaction_hamiltonian + 0.01 * j_eff))

        return {
            "rho": self.rho,
            "distortion": structural_distortion,
            "raw_source": raw_source,
            "j_eff": j_eff,
            "j_0": j_0
        }

    def calculate_capacity(self, epsilon: float) -> float:
        """Calculates Kolmogorov-Tikhomirov capacity based on indistinguishable equivalence classes.

        Calculates C_atom(epsilon) = log(N_epsilon).

        Args:
            epsilon (float): Resolution bound metrics parameter.

        Returns:
            float: Evaluated atomic information capacity value.
        """
        if epsilon <= 0:
            epsilon = 1e-4
        # Equivalent classes are inversely proportional to resolution boundary grid spacing
        n_epsilon = max(1, int(1.0 / (epsilon * (1.0 + abs(self.rho)))))
        return math.log(n_epsilon)

    def get_state(self) -> Dict[str, Any]:
        """Fetches complete structured inner representations of variables.

        Returns:
            Dict[str, Any]: State snapshot mapping dictionary.
        """
        return {
            "rho": self.rho,
            "register": asdict(self.k_0),
            "buffer": list(self.delay_buffer)
        }


# =============================================================================
# VIEW LAYER (MVP PATTERN)
# =============================================================================
class BaseView(ABC):
    """Abstract Base View defining interface mechanisms for presentation interactions."""

    @abstractmethod
    def show_message(self, key: str, **kwargs: Any) -> None:
        """Renders localized messages to output pipelines."""
        pass

    @abstractmethod
    def render_results(self, data: Dict[str, Any]) -> None:
        """Outputs statistical metric summaries compiled across simulation targets."""
        pass


class CLIView(BaseView):
    """Command Line Interface implementation handling display operations and localization."""

    def __init__(self, lang: str = "en") -> None:
        """Initializes language configurations fallback vectors.

        Args:
            lang (str): Language string selector ('en', 'es', 'fr', 'de').
        """
        self.lang = lang if lang in I18N_DICT else "en"
        self.translations = I18N_DICT[self.lang]

    def show_message(self, key: str, **kwargs: Any) -> None:
        """Formats and prints key lookup dictionaries values to standard output stream.

        Args:
            key (str): Key matching targeted phrase string.
            **kwargs (Any): Dynamic interpolations formatting targets.
        """
        template = self.translations.get(key, I18N_DICT["en"].get(key, f"Missing [{key}]"))
        print(template.format(**kwargs))

    def render_results(self, data: Dict[str, Any]) -> None:
        """Displays formatted final states matrix summaries block structures.

        Args:
            data (Dict[str, Any]): Compiled presentation dataset blocks.
        """
        print("\n" + "="*50)
        print(f" FINAL REPORT METRICS SUMMARY [Language: {self.lang.upper()}]")
        print("="*50)
        for k, v in data.items():
            if isinstance(v, dict):
                print(f"- {k}:")
                for sub_k, sub_v in v.items():
                    print(f"  * {sub_k}: {sub_v}")
            else:
                print(f"- {k}: {v}")
        print("="*50 + "\n")


# =============================================================================
# PRESENTER LAYER (MVP PATTERN)
# =============================================================================
class SimulationPresenter:
    """Coordinates and executes simulation workloads linking Models to Views cleanly."""

    def __init__(self, config: Dict[str, Any], view: BaseView) -> None:
        """Binds structured dependencies engines configuration parameters.

        Args:
            config (Dict[str, Any]): Parsing dictionary containing runtime metrics parameters.
            view (BaseView): View engine subclass complying with base interface blueprints.
        """
        self.config = config
        self.view = view
        self.model = OctaMemoryModel(config)

    def run_simulation(self) -> None:
        """Orchestrates structured test frameworks addressing document goals."""
        self.view.show_message("welcome")

        # Goal 1 & 2: Structural Update Loop Coupling Dynamics Exploration
        self.view.show_message("running_goal", goal="1 & 2", desc="Octahedral Register Construction & Geometric Coupling")
        total_steps = self.config.get("simulation_steps", 5)
        voltage_profile = self.config.get("voltage_profile", [1.0] * total_steps)
        recoverability_loss = self.config.get("recoverability_loss_profile", [0.2] * total_steps)

        step_axis: List[int] = []
        history_voltages: List[float] = []
        history_rhos: List[float] = []
        history_distortions: List[float] = []
        history_raw_sources: List[float] = []
        history_eff_sources: List[float] = []

        for i in range(total_steps):
            v_t = voltage_profile[i] if i < len(voltage_profile) else 0.5
            delta_0 = recoverability_loss[i] if i < len(recoverability_loss) else 0.1
            
            metrics = self.model.step(v_t, delta_0)
            step_axis.append(i + 1)
            history_voltages.append(v_t)
            history_rhos.append(metrics["rho"])
            history_distortions.append(metrics["distortion"])
            history_raw_sources.append(metrics["raw_source"])
            history_eff_sources.append(metrics["j_eff"])

            self.view.show_message("sim_step", step=i+1, v=v_t, rho=metrics["rho"], dist=metrics["distortion"])

        # Goal 4: Entropic Capacity Analysis Frameworks Execution
        self.view.show_message("running_goal", goal="4", desc="Capacity calculation under Geometry Registers")
        epsilon = float(self.config.get("epsilon_bound", 0.05))
        capacity = self.model.calculate_capacity(epsilon)
        self.view.show_message("capacity_res", eps=epsilon, cap=capacity)

        # Goal 5: Structural Null-Test Preservation Analysis
        self.view.show_message("running_goal", goal="5", desc="Null-Test Preservation Verification")
        null_model = OctaMemoryModel(self.config)
        null_metrics = null_model.step(V_t=1.0, delta_0=0.0)

        if math.isclose(null_metrics["j_eff"], 0.0, abs_tol=1e-7) and math.isclose(null_metrics["j_0"], 0.0, abs_tol=1e-7):
            self.view.show_message("null_test_pass")
        else:
            self.view.show_message("null_test_fail")

        # Finish up and output final summaries metrics tables
        final_state = self.model.get_state()
        final_state["final_capacity_estimation"] = capacity
        self.view.render_results(final_state)
        self.view.show_message("done")

        # Reporting 
        target_dir = self.config.get("output_directory", "reports")
        plotly_view = PlotlyHtmlView(output_dir=target_dir)

        # Renderizar los HTMLs pasándole las listas 
        # acumuladas durante el bucle
        p1 = plotly_view.generate_goals_1_2_chart(step_axis, history_voltages, 
                        history_rhos, history_distortions)
        p2 = plotly_view.generate_goal_3_chart(step_axis, 
                        history_raw_sources, history_eff_sources)

        # Para la capacidad (Goal 4) se puede muestrear rápidamente 
        # un barrido de epsilons:
        eps_axis: List[float] = self.config.get("goal_4_epsilon_sweep", 
                        [0.1, 0.05, 0.02, 0.01, 0.005])

        # 2. Evaluamos la capacidad dinámica del modelo para cada resolución configurada
        cap_axis: List[float] = [self.model.calculate_capacity(e) 
                        for e in eps_axis]
        p3 = plotly_view.generate_goal_4_chart(eps_axis, cap_axis)
        
        print(f"Interactive reports compiled successfully inside ./{plotly_view.output_dir}/ directory!")
        eps_sweep = self.config.get("goal_4_epsilon_sweep", [0.1, 0.05, 0.02, 0.01])
        capacity_results = {e: self.model.calculate_capacity(e) for e in eps_sweep}
        md_logger = MarkdownReportView(output_dir=target_dir)
        md_file_created = md_logger.write_summary_report(
            config=self.config,
            steps=step_axis,
            voltages=history_voltages,
            rhos=history_rhos,
            distortions=history_distortions,
            capacity_sweep=capacity_results,
            final_state=final_state
        )

        print(f"Tabular summary written successfully to: {md_file_created}")


# =============================================================================
# RUNTIME PARSER ENTRY POINT
# =============================================================================
def main() -> None:
    """Processes command line parameters options block arguments, building environments."""
    parser = argparse.ArgumentParser(
        description="CLI Suite for Octahedral gTRQC Hydrogenated Nickelate Memory Proof of Concept."
    )
    parser.add_argument(
        "-l", "--lang", type=str, default="en", choices=["en", "es", "fr", "de"],
        help="Specify localized execution dialog targeting engine interface languages."
    )
    parser.add_argument(
        "-c", "--config", type=str, default=None,
        help="Optional external path specifying target YAML parameters datasets location."
    )
    parser.add_argument(
        "-o", "--output", type=str, default=None,
        help="Target directory where interactive HTML chart reports will be saved."
    )

    args = parser.parse_args()
    view = CLIView(lang=args.lang)

    # Establish baseline defaults parameters fallback values dictionary mappings
    default_config: Dict[str, Any] = {
        "output_directory": "reports",
        "simulation_steps": 6,
        "g_oct_stiffness": 3.0,
        "protonic_delay_steps": 2,
        "epsilon_bound": 0.02,
        "initial_rho": 1.0,
        "initial_register": {
            "theta_tilt": 0.12,
            "theta_rot": 0.06,
            "delta_V_oct": 0.0,
            "delta_phi": 0.03,
            "epsilon_0": 1.0
        },
        "voltage_profile": [1.0, 1.5, 1.2, 0.8, 0.4, 0.0],
        "recoverability_loss_profile": [0.1, 0.2, 0.3, 0.2, 0.1, 0.0]
    }

    if args.config and os.path.exists(args.config):
        view.show_message("loading_config", path=args.config)
        with open(args.config, "r", encoding="utf-8") as file_stream:
            user_config = yaml.safe_load(file_stream)
            if user_config and isinstance(user_config, dict):
                default_config.update(user_config)

    # Initialize Presenter and run the suite simulation engine workloads
    presenter = SimulationPresenter(config=default_config, view=view)
    presenter.run_simulation()


if __name__ == "__main__":
    main()

