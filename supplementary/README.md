# Supplementary material — single-file Overleaf source

Upload **`main.tex` only** to Overleaf and select **pdfLaTeX**. The document is in English and contains all sections, tables, bibliography entries, TikZ diagrams, and PGFPlots figure coordinates. There are no external images, `.bib` files, CSV files, `\input` dependencies, or required subdirectories.

- [main.tex](main.tex): complete editable source.
- [supplementary_material.pdf](supplementary_material.pdf): locally compiled review copy.

The supplement describes the current paper API, original notebook reference, historical prototypes, equations and units, experimental partition, numerical protocols, and recorded verification. It explicitly distinguishes native coverage from analyses retained in full notebook replay. See [VARIANTS.md](../VARIANTS.md) for the repository map.

## Updating within the repository

```bash
# Verify manifests and refresh inline tables, plot coordinates and provenance
poetry run python scripts/update_supplement.py

# Refresh and compile the standalone file with locally installed pdfLaTeX
poetry run python scripts/build_supplement.py

# Compile an edited version without refreshing any embedded evidence
poetry run python scripts/build_supplement.py --no-refresh
```

Python scripts are maintenance conveniences; **Overleaf does not need them**. They replace only named `% BEGIN GENERATED: ...` / `% END GENERATED: ...` blocks and preserve the surrounding narrative. Manual edits inside generated blocks will be replaced on refresh. Overleaf edits can be copied back to `main.tex` before refreshing evidence.

The updater verifies original notebook hashes and native artifact manifests before reading recorded results. It does not rerun experiments. The source/evidence snapshot is embedded as JSON comments in the same `.tex` file. The supplied manuscript is identified by hash; it is not required for compilation or redistributed by this supplement.

The local builder copies `main.tex` into an otherwise empty temporary directory and runs three pdfLaTeX passes, with shell escape disabled. It writes the final PDF here, removes temporary auxiliary files, and places the last compilation log in the system temporary directory. Local compilation requires TeX Live packages for standard LaTeX, TikZ and PGFPlots; Poetry manages only the Python environment.

This is a reviewable software supplement, not a claim that the working-tree implementation has already been released under a public tag or DOI. The prose maintains the scientific scope of the supplied manuscript.
