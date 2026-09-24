# Package boundaries

`proton/` is the current paper-aligned API, with independent transport, relaxation and recoverability components and MVP orchestration. Use `poetry run proton-study`.

The Python modules directly in this directory outside `proton/` retain the historical quantum-geometric prototype and its CLI for compatibility. Their physical assumptions and results must not be attributed to the current proton-transport paper. In particular, recoverability-to-geometry feedback is historical, while the paper sets that coupling to zero.

See [the repository variant map](../VARIANTS.md) and [the supplementary material](../supplementary/README.md) for the precise scope and location of each implementation.
