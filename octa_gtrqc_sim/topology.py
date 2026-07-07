"""Graph-topology primitives for the octahedral gTRQC proof of concept."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np


Edge = Tuple[int, int]


@dataclass(frozen=True)
class GraphTopology:
    """Discrete graph topology used by reduced proof-of-concept engines.

    The current proof of concept does not evolve one quantum subsystem per graph
    node in every engine. This topology object therefore serves two distinct
    roles:

    1. It provides an explicit and reviewable topology configuration surface.
    2. It exposes derived graph invariants that reduced engines can use as
       topology-dependent scaling factors or hidden-sector coupling patterns.

    Attributes:
        name: Stable topology identifier.
        node_count: Number of graph vertices.
        edges: Undirected edge list with zero-based node indices.
    """

    name: str
    node_count: int
    edges: Tuple[Edge, ...]

    def adjacency_matrix(self) -> np.ndarray:
        """Build the symmetric adjacency matrix.

        Returns:
            Symmetric adjacency matrix with shape ``(node_count, node_count)``.
        """
        adjacency = np.zeros((self.node_count, self.node_count), dtype=float)
        for left, right in self.edges:
            adjacency[left, right] = 1.0
            adjacency[right, left] = 1.0
        return adjacency

    def degree_sequence(self) -> List[int]:
        """Return the degree sequence of the graph.

        Returns:
            Degree of each node.
        """
        adjacency = self.adjacency_matrix()
        return [int(value) for value in np.sum(adjacency, axis=1)]

    def average_degree(self) -> float:
        """Return the average graph degree.

        Returns:
            Average degree over all nodes.
        """
        return float(sum(self.degree_sequence()) / self.node_count)

    def edge_density(self) -> float:
        """Return the undirected edge density.

        Returns:
            Ratio between actual and possible undirected edges.
        """
        max_edges = self.node_count * (self.node_count - 1) / 2.0
        return float(len(self.edges) / max_edges) if max_edges > 0 else 0.0

    def spectral_radius(self) -> float:
        """Return the spectral radius of the adjacency matrix.

        Returns:
            Largest absolute eigenvalue of the adjacency matrix.
        """
        eigenvalues = np.linalg.eigvals(self.adjacency_matrix())
        return float(np.max(np.abs(eigenvalues)))

    def topology_scale(self, reference_average_degree: float = 4.0) -> float:
        """Return a reduced-model scaling factor relative to the OCTA benchmark.

        The OCTA-inspired six-node benchmark has average degree four. Reduced
        engines use this factor when they do not carry the full graph structure
        explicitly.

        Args:
            reference_average_degree: Reference degree used for normalization.

        Returns:
            Dimensionless topology scale.
        """
        if reference_average_degree <= 0.0:
            return 1.0
        return self.average_degree() / reference_average_degree


def _cycle_edges(node_count: int) -> List[Edge]:
    return [(index, (index + 1) % node_count) for index in range(node_count)]


def _chain_edges(node_count: int) -> List[Edge]:
    return [(index, index + 1) for index in range(node_count - 1)]


def _star_edges(node_count: int) -> List[Edge]:
    return [(0, index) for index in range(1, node_count)]


def _complete_edges(node_count: int) -> List[Edge]:
    return [(left, right) for left in range(node_count) for right in range(left + 1, node_count)]


def _octa_edges() -> List[Edge]:
    """Return the six-node octahedral graph edge list.

    The octahedral graph is ``K_6`` with three opposite-vertex pairs removed.

    Returns:
        Edge list for the six-node octahedral benchmark.
    """
    opposite_pairs = {(0, 1), (2, 3), (4, 5)}
    edges: List[Edge] = []
    for left in range(6):
        for right in range(left + 1, 6):
            if (left, right) not in opposite_pairs:
                edges.append((left, right))
    return edges


TOPOLOGY_LIBRARY: Dict[str, GraphTopology] = {
    "octa": GraphTopology("octa", 6, tuple(_octa_edges())),
    "ring_6": GraphTopology("ring_6", 6, tuple(_cycle_edges(6))),
    "chain_6": GraphTopology("chain_6", 6, tuple(_chain_edges(6))),
    "star_6": GraphTopology("star_6", 6, tuple(_star_edges(6))),
    "complete_6": GraphTopology("complete_6", 6, tuple(_complete_edges(6))),
}


def available_topologies() -> Sequence[str]:
    """Return the available built-in topology names.

    Returns:
        Ordered tuple of topology identifiers.
    """
    return tuple(TOPOLOGY_LIBRARY.keys())


def get_topology(name: str) -> GraphTopology:
    """Resolve a built-in topology by name.

    Args:
        name: Topology identifier.

    Returns:
        Resolved graph topology.

    Raises:
        ValueError: If the topology name is not recognized.
    """
    try:
        return TOPOLOGY_LIBRARY[name]
    except KeyError as exc:
        valid_names = ", ".join(available_topologies())
        raise ValueError(f"Unknown topology '{name}'. Available options: {valid_names}.") from exc
