# Robustness Study Summary

> Historical prototype result. This report is not part of the current paper validation. See [VARIANTS.md](../VARIANTS.md) and [validation/](../validation/).


This report documents a delay-focused sensitivity analysis for the `quantum` engine.
Tested delay steps: 0, 1, 2, 5.

The study varies one factor at a time around the baseline configuration: time step, initial matter-state population, feedback stiffness, dephasing strength, numerical tolerance, geometry initialization, and graph topology.

Topology note: the present study now compares several built-in six-node graph topologies through reduced topology-aware couplings, but topology dependence should still be interpreted cautiously because not every engine carries a full node-resolved graph state.

## Baseline Delay Trend

| Delay steps | Peak distortion | Mean distortion | Final rho |
| :---: | :---: | :---: | :---: |
| 0 | 0.187699 | 0.185133 | 0.096522 |
| 1 | 0.187699 | 0.185133 | 0.096522 |
| 2 | 0.187699 | 0.184491 | 0.096194 |
| 5 | 0.187547 | 0.182569 | 0.095956 |

## Scenario Summary

| Scenario | Topology | Delay steps | Peak distortion | Mean abs source gap | Null test |
| :--- | :---: | :---: | :---: | :---: |
| baseline | octa | 0 | 0.187699 | 0.000000 | pass |
| baseline | octa | 1 | 0.187699 | 0.000000 | pass |
| baseline | octa | 2 | 0.187699 | 0.174975 | pass |
| baseline | octa | 5 | 0.187547 | 0.553438 | pass |
| time_step_low | octa | 0 | 0.183886 | 0.000000 | pass |
| time_step_low | octa | 1 | 0.183886 | 0.000000 | pass |
| time_step_low | octa | 2 | 0.183886 | 0.174975 | pass |
| time_step_low | octa | 5 | 0.183808 | 0.553438 | pass |
| time_step_high | octa | 0 | 0.195110 | 0.000000 | pass |
| time_step_high | octa | 1 | 0.195110 | 0.000000 | pass |
| time_step_high | octa | 2 | 0.195109 | 0.174975 | pass |
| time_step_high | octa | 5 | 0.194819 | 0.553438 | pass |
| initial_population_low | octa | 0 | 0.187699 | 0.000000 | pass |
| initial_population_low | octa | 1 | 0.187699 | 0.000000 | pass |
| initial_population_low | octa | 2 | 0.187699 | 0.174975 | pass |
| initial_population_low | octa | 5 | 0.187547 | 0.553438 | pass |
| initial_population_mid | octa | 0 | 0.187699 | 0.000000 | pass |
| initial_population_mid | octa | 1 | 0.187699 | 0.000000 | pass |
| initial_population_mid | octa | 2 | 0.187699 | 0.174975 | pass |
| initial_population_mid | octa | 5 | 0.187547 | 0.553438 | pass |
| feedback_low | octa | 0 | 0.187699 | 0.000000 | pass |
| feedback_low | octa | 1 | 0.187699 | 0.000000 | pass |
| feedback_low | octa | 2 | 0.187699 | 0.074989 | pass |
| feedback_low | octa | 5 | 0.187547 | 0.237188 | pass |
| feedback_high | octa | 0 | 0.187699 | 0.000000 | pass |
| feedback_high | octa | 1 | 0.187699 | 0.000000 | pass |
| feedback_high | octa | 2 | 0.187699 | 0.224968 | pass |
| feedback_high | octa | 5 | 0.187547 | 0.711564 | pass |
| dephasing_low | octa | 0 | 0.187699 | 0.000000 | pass |
| dephasing_low | octa | 1 | 0.187699 | 0.000000 | pass |
| dephasing_low | octa | 2 | 0.187699 | 0.174975 | pass |
| dephasing_low | octa | 5 | 0.187547 | 0.553438 | pass |
| dephasing_high | octa | 0 | 0.187699 | 0.000000 | pass |
| dephasing_high | octa | 1 | 0.187699 | 0.000000 | pass |
| dephasing_high | octa | 2 | 0.187699 | 0.174975 | pass |
| dephasing_high | octa | 5 | 0.187547 | 0.553438 | pass |
| tolerance_loose | octa | 0 | 0.187699 | 0.000000 | pass |
| tolerance_loose | octa | 1 | 0.187699 | 0.000000 | pass |
| tolerance_loose | octa | 2 | 0.187699 | 0.174975 | pass |
| tolerance_loose | octa | 5 | 0.187547 | 0.553438 | pass |
| tolerance_tight | octa | 0 | 0.187699 | 0.000000 | pass |
| tolerance_tight | octa | 1 | 0.187699 | 0.000000 | pass |
| tolerance_tight | octa | 2 | 0.187699 | 0.174975 | pass |
| tolerance_tight | octa | 5 | 0.187547 | 0.553438 | pass |
| topology_ring | ring_6 | 0 | 0.183886 | 0.000000 | pass |
| topology_ring | ring_6 | 1 | 0.183886 | 0.000000 | pass |
| topology_ring | ring_6 | 2 | 0.183886 | 0.087488 | pass |
| topology_ring | ring_6 | 5 | 0.183808 | 0.276719 | pass |
| topology_chain | chain_6 | 0 | 0.183244 | 0.000000 | pass |
| topology_chain | chain_6 | 1 | 0.183244 | 0.000000 | pass |
| topology_chain | chain_6 | 2 | 0.183244 | 0.072906 | pass |
| topology_chain | chain_6 | 5 | 0.183179 | 0.230599 | pass |
| topology_star | star_6 | 0 | 0.183244 | 0.000000 | pass |
| topology_star | star_6 | 1 | 0.183244 | 0.000000 | pass |
| topology_star | star_6 | 2 | 0.183244 | 0.072906 | pass |
| topology_star | star_6 | 5 | 0.183179 | 0.230599 | pass |
| topology_complete | complete_6 | 0 | 0.189579 | 0.000000 | pass |
| topology_complete | complete_6 | 1 | 0.189579 | 0.000000 | pass |
| topology_complete | complete_6 | 2 | 0.189578 | 0.218719 | pass |
| topology_complete | complete_6 | 5 | 0.189391 | 0.691798 | pass |
| geometry_soft | octa | 0 | 0.097031 | 0.000000 | pass |
| geometry_soft | octa | 1 | 0.097031 | 0.000000 | pass |
| geometry_soft | octa | 2 | 0.097031 | 0.174975 | pass |
| geometry_soft | octa | 5 | 0.096892 | 0.553438 | pass |
| geometry_strong | octa | 0 | 0.278368 | 0.000000 | pass |
| geometry_strong | octa | 1 | 0.278368 | 0.000000 | pass |
| geometry_strong | octa | 2 | 0.278367 | 0.174975 | pass |
| geometry_strong | octa | 5 | 0.278202 | 0.553438 | pass |
