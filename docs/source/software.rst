Software Architecture & Engineering Blueprints
==============================================

The execution engine is structured using a strict **Model-View-Presenter (MVP)** decoupling paradigm built on Python 3.12. This modular layout ensures that physical processing kernels remain completely isolated from standard terminal presentation views or persistence logging layers.

UML Class Diagram
-----------------
The relationships, inherited structures, and operational boundaries of the software components are mapped out below:

.. mermaid::

   classDiagram
      class OctaMemoryModel {
          +float rho
          +float g_oct
          +int delay_steps
          +dict register_state
          +step(V_t, delta_0) dict
          +calculate_capacity(epsilon) float
          +get_state() dict
      }
      class BaseView {
          <<interface>>
          +show_message(msg_id, **kwargs)* void
          +render_results(results_dict)* void
      }
      class CLIView {
          +str lang
          +dict i18n_dict
          +show_message(msg_id, **kwargs) void
          +render_results(results_dict) void
      }
      class SimulationPresenter {
          +dict config
          +OctaMemoryModel model
          +BaseView view
          +run_simulation() void
      }
      class PlotlyHtmlView {
          +str output_dir
          +generate_goals_1_2_chart() str
          +generate_goal_3_chart() str
          +generate_goal_4_chart() str
      }
      class MarkdownReportView {
          +str output_dir
          +write_summary_report() str
      }

      BaseView <|.. CLIView
      SimulationPresenter --> OctaMemoryModel : orchestrates
      SimulationPresenter --> BaseView : updates
      SimulationPresenter ..> PlotlyHtmlView : instantiates for HTML generation
      SimulationPresenter ..> MarkdownReportView : instantiates for log files

Execution Sequence Flow
-----------------------
The timeline interaction model for a discrete operational simulation window maps onto the following execution trace:

.. mermaid::

   sequenceDiagram
      autonumber
      participant M as Main (CLI Entry)
      participant P as SimulationPresenter
      participant Mod as OctaMemoryModel
      participant V as CLIView
      
      M->>P: run_simulation()
      loop Over Configured Simulation Timeline Steps (1 to N)
          P->>Mod: step(V_t, delta_0)
          activate Mod
          Mod->>Mod: Compute local geometric distortion mechanics
          Mod->>Mod: Process history buffers for Protonic Latency (J_eff)
          Mod->>Mod: Adjust Quantum Coherence Index (rho)
          Mod-->>P: Step Metrics Payload Dictionary
          deactivate Mod
          P->>V: show_message("sim_step", index, V_t, rho, distortion)
          V-->>P: Terminal feedback rendering
      end
      P->>Mod: calculate_capacity(epsilon)
      Mod-->>P: Computed C_atom value
      P->>V: render_results(final_state)

Data Pipelines and Closed-Loop Feedback
---------------------------------------
The transformation matrix routing for data tracking during model updates follows this logical flow:

.. mermaid::

   graph TD
      A[Input Parameters: Voltage V_t & Recoverability loss delta_0] --> B(Lattice Elastic Response Module)
      B --> C{Is History Index >= delay_steps?}
      C -- Yes --> D[Incorporate Protonic Retardation Feedback Loop]
      C -- No --> E[Assign Pure Instantaneous J_eff Vector]
      D --> F[Execute Distortion Field Matrix Updates]
      E --> F
      F --> G[Recompute Coherence State Variable rho_t]
      G --> H[Export Metrics Payloads & Buffer History Arrays]
