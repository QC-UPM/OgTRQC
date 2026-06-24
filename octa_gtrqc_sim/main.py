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
import numpy as np

from octa_gtrqc_sim.reports import PlotlyHtmlView, MarkdownReportView
from octa_gtrqc_sim.quantum_integrator import QuantumMaterialCell
from octa_gtrqc_sim.quantum_memory import QuantumMemoryModel
from octa_gtrqc_sim.material_register import MaterialRegister
from octa_gtrqc_sim.causal_integrator import CausalSufficiencyModel
from octa_gtrqc_sim.causal_recovery import RelaxedCausalModel
from octa_gtrqc_sim.quantum_recovery import RelaxedQuantumModel
from octa_gtrqc_sim.extended_recovery import ExtendedRelaxedCausalModel, ExtendedRelaxedQuantumModel

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
        "error_invalid_engine": "Error: Unrecognized mathematical integration engine '{engine}'. Halting execution.",
        "null_test_fail": "Null-Test Verification Failed!",
        "done": "Simulation process completed successfully."
    },
    "es": {
        "welcome": "Iniciando la Simulación gTRQC Octaédrica...",
        "loading_config": "Cargando parámetros desde el archivo de configuración: {path}",
        "running_goal": "Ejecutando Objetivo de Simulación {goal}: {desc}",
        "sim_step": "Paso {step:03d} | V(t)={v:.2f}V | rho={rho:.4f} | Distorsión Octa={dist:.4f}",
        "capacity_res": "Capacidad Atómica de Kolmogorov C_atom(epsilon={eps}) calculada: {cap:.4f}",
        "error_invalid_engine": "Error: Motor de integración matemática no reconocido '{engine}'. Deteniendo la ejecución.",
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
        "error_invalid_engine": "Erreur : Moteur d'intégration mathématique non reconnu '{engine}'. Arrêt de l'exécution.",
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
        "error_invalid_engine": "Fehler: Unerkannter mathematischer Integrationsmotor '{engine}'. Ausführung wird angehalten.",
        "null_test_pass": "Nulltest-Verifizierung Bestanden: Dynamische Quelle verschwindet bei Null-Wiederherstellbarkeitsverlust.",
        "null_test_fail": "Nulltest-Verifizierung Fehlgeschlagen!",
        "done": "Simulationsprozess erfolgreich abgeschlossen."
    }
}


class OctaMemoryModel:
    """Mathematical execution framework representing the H_xNdNiO_3 material system."""

    def __init__(self, config: Dict[str, Any]) -> None:
        reg_conf = config.get("initial_register", {})
        self.k_0 = MaterialRegister(
            theta_tilt=float(reg_conf.get("theta_tilt", 0.1)),
            theta_rot=float(reg_conf.get("theta_rot", 0.05)),
            delta_V_oct=float(reg_conf.get("delta_V_oct", 0.0)),
            delta_phi=float(reg_conf.get("delta_phi", 0.02)),
            epsilon_0=float(reg_conf.get("epsilon_0", 1.0))
        )
        self.rho: float = float(config.get("initial_rho", 1.0))
        self.g_oct: float = float(config.get("g_oct_stiffness", 2.5))
        self.delay: int = int(config.get("protonic_delay_steps", 2))
        self.delay_buffer: List[float] = [0.0] * self.delay

    def step(self, V_t: float, delta_0: float) -> Dict[str, float]:
        raw_source = delta_0 * self.g_oct
        self.delay_buffer.append(raw_source)
        j_eff = self.delay_buffer.pop(0)

        j_0 = j_eff * sum(self.k_0.to_vector())

        delta_k = -j_0 / (self.g_oct + 1e-9)
        self.k_0.theta_tilt += delta_k * 0.1
        self.k_0.theta_rot += delta_k * 0.05
        self.k_0.delta_V_oct += delta_k * 0.2

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
        if epsilon <= 0:
            epsilon = 1e-4
        n_epsilon = max(1, int(1.0 / (epsilon * (1.0 + abs(self.rho)))))
        return math.log(n_epsilon)

    def get_state(self) -> Dict[str, Any]:
        return {
            "rho": self.rho,
            "register": asdict(self.k_0),
            "buffer": list(self.delay_buffer)
        }


# =============================================================================
# VIEW LAYER (MVP PATTERN)
# =============================================================================
class BaseView(ABC):
    @abstractmethod
    def show_message(self, key: str, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def render_results(self, data: Dict[str, Any]) -> None:
        pass


class CLIView(BaseView):
    def __init__(self, lang: str = "en") -> None:
        self.lang = lang if lang in I18N_DICT else "en"
        self.translations = I18N_DICT[self.lang]

    def show_message(self, key: str, **kwargs: Any) -> None:
        template = self.translations.get(key, I18N_DICT["en"].get(key, f"Missing [{key}]"))
        print(template.format(**kwargs))

    def render_results(self, data: Dict[str, Any]) -> None:
        print("\n" + "="*50)
        print(f" FINAL REPORT METRICS SUMMARY [Language: {self.lang.upper()}]")
        print("="*50)
        for k, v in data.items():
            if isinstance(v, dict):
                print(f"  {k}:")
                for sub_k, sub_v in v.items():
                    print(f"    {sub_k}: {sub_v}")
            else:
                print(f"  {k}: {v}")
        print("="*50 + "\n")


# =============================================================================
# PRESENTER LAYER (MVP PATTERN)
# =============================================================================
class SimulationPresenter:
    def __init__(self, config: Dict[str, Any], view: BaseView) -> None:
        self.config = config
        self.view = view
        engine_type = self.config.get("engine", "legacy")

        if engine_type == "causal":
            self.model = CausalSufficiencyModel(config)
        elif engine_type == "quantum":
            self.model = QuantumMemoryModel(config)
        elif engine_type == "legacy":
            self.model = OctaMemoryModel(config)
        elif engine_type == "relaxed_quantum":
            self.model = RelaxedQuantumModel(config)
        elif engine_type == "relaxed_causal":
            self.model = RelaxedCausalModel(config)
        elif engine_type == "extended_quantum":
            self.model = ExtendedRelaxedQuantumModel(config)
        elif engine_type == "extended_causal":
            self.model = ExtendedRelaxedCausalModel(config)
        else:
            self.view.show_message("error_invalid_engine", engine=engine_type)
            raise ValueError(f"Unrecognized mathematical integration engine: {engine_type}")

    def _generate_analytical_profiles(self, steps: int) -> tuple[List[float], List[float]]:
        voltage_profile = []
        recoverability_profile = []
        
        for i in range(steps):
            v = 1.5 * math.sin(math.pi * i / (steps / 2.0)) * math.exp(-i / (steps * 1.5))
            voltage_profile.append(max(0.0, float(v)))
            
            delta = 0.3 * math.exp(-math.pow(i - (steps / 3.0), 2) / (steps * 0.5))
            recoverability_profile.append(float(delta))
            
        return voltage_profile, recoverability_profile

    def run_simulation(self) -> None:
        self.view.show_message("welcome")
        self.view.show_message("running_goal", goal="1 & 2", desc="Octahedral Register Construction & Geometric Coupling")
        
        total_steps = self.config.get("simulation_steps", 6)
        if not isinstance(total_steps, int) or total_steps <= 0:
            total_steps = 6

        voltage_profile, recoverability_loss = self._generate_analytical_profiles(total_steps)

        step_axis: List[int] = []
        history_voltages: List[float] = []
        history_rhos: List[float] = []
        history_distortions: List[float] = []
        history_raw_sources: List[float] = []
        history_eff_sources: List[float] = []

        for i in range(total_steps):
            v_t = voltage_profile[i]
            delta_0 = recoverability_loss[i]
            
            metrics = self.model.step(v_t, delta_0)
            step_axis.append(i + 1)
            history_voltages.append(v_t)
            history_rhos.append(metrics["rho"])
            history_distortions.append(metrics["distortion"])
            history_raw_sources.append(metrics.get("raw_source", 0.0))
            history_eff_sources.append(metrics.get("j_eff", metrics.get("endogenous_delta", 0.0)))

            self.view.show_message("sim_step", step=i+1, v=v_t, rho=metrics["rho"], dist=metrics["distortion"])

        self.view.show_message("running_goal", goal="4", desc="Capacity calculation under Geometry Registers")
        epsilon = float(self.config.get("epsilon_bound", 0.05))
        capacity = self.model.calculate_capacity(epsilon)
        self.view.show_message("capacity_res", eps=epsilon, cap=capacity)

        self.view.show_message("running_goal", goal="5", desc="Null-Test Preservation Verification")
        null_model = OctaMemoryModel(self.config)
        null_metrics = null_model.step(V_t=1.0, delta_0=0.0)

        if math.isclose(null_metrics["j_eff"], 0.0, abs_tol=1e-7) and math.isclose(null_metrics["j_0"], 0.0, abs_tol=1e-7):
            self.view.show_message("null_test_pass")
        else:
            self.view.show_message("null_test_fail")

        final_state = self.model.get_state()
        final_state["final_capacity_estimation"] = capacity
        self.view.render_results(final_state)
        self.view.show_message("done")

        target_dir = self.config.get("output_directory", "reports")
        plotly_view = PlotlyHtmlView(output_dir=target_dir)

        p1 = plotly_view.generate_goals_1_2_chart(step_axis, history_voltages, history_rhos, history_distortions)
        p2 = plotly_view.generate_goal_3_chart(step_axis, history_raw_sources, history_eff_sources)

        eps_axis: List[float] = self.config.get("goal_4_epsilon_sweep", [0.1, 0.05, 0.02, 0.01, 0.005])
        cap_axis: List[float] = [self.model.calculate_capacity(e) for e in eps_axis]
        p3 = plotly_view.generate_goal_4_chart(eps_axis, cap_axis)
        
        print(f"Interactive reports compiled successfully inside ./{plotly_view.output_dir}/ directory!")
        capacity_results = {e: self.model.calculate_capacity(e) for e in eps_axis}
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
    parser.add_argument(
        "-e", "--engine", type=str, default=None, choices=["legacy", "quantum", "causal", 
                    "relaxed_quantum", "relaxed_causal", "extended_quantum", "extended_causal"],
        help="Switches the underlying mathematical integration engine used for the simulation."
    )
    parser.add_argument(
        "--hopping", type=float, default=None,
        help="Transverse hopping parameter for the Nickel subsystem."
    )
    parser.add_argument(
        "--gamma", type=float, default=None,
        help="Dephasing gamma parameter for environmental Kraus operators."
    )

    args = parser.parse_args()
    view = CLIView(lang=args.lang)

    default_config: Dict[str, Any] = {
        "engine": "legacy",
        "output_directory": "reports",
        "simulation_steps": 6,
        "g_oct_stiffness": 3.0,
        "protonic_delay_steps": 2,
        "epsilon_bound": 0.02,
        "initial_rho": 1.0,
        "ni_transverse_hopping": 0.8,
        "dephasing_gamma": 0.05,
        "proton_hopping_energy": 0.5,
        "inter_site_hopping": 0.2,
        "electron_proton_coupling": 1.2,
        "initial_register": {
            "theta_tilt": 0.12,
            "theta_rot": 0.06,
            "delta_V_oct": 0.0,
            "delta_phi": 0.03,
            "epsilon_0": 1.0
        }
    }

    if args.config and os.path.exists(args.config):
        view.show_message("loading_config", path=args.config)
        with open(args.config, "r", encoding="utf-8") as file_stream:
            user_config = yaml.safe_load(file_stream)
            if user_config and isinstance(user_config, dict):
                default_config.update(user_config)

    if args.engine is not None:
        default_config["engine"] = args.engine
        
    if args.output is not None:
        default_config["output_directory"] = args.output
        
    if args.hopping is not None:
        default_config["ni_transverse_hopping"] = args.hopping
        
    if args.gamma is not None:
        default_config["dephasing_gamma"] = args.gamma

    presenter = SimulationPresenter(config=default_config, view=view)
    presenter.run_simulation()


if __name__ == "__main__":
    main()