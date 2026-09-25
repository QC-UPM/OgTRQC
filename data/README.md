# Numeric inputs and provenance

- `figure_inputs.json`: reviewed time points, observations, predictions, pointwise interval, curvature inputs and synthetic transfer/hidden-twin arrays. Used by the seven-figure exporter. No executable notebook code is embedded.
- `generator_reference.npz`: independent numeric fixture (occupancy, generator matrix, structural amplitudes and potential) exported from the reviewed external generator. Used by regression tests without loading its source.
- `reference_scalars.json`: compact holdout, uncertainty and constant-D regression targets from the reviewed computational record.
- `provenance.json`: hashes and filenames identifying the external manuscript, response, PDF and original notebooks. The documents themselves are not stored here.
- `manifest.json`: hashes of the fixed numeric inputs and compact `validation/reference/` exports. Generation fails on mismatch; it does not silently rebaseline changed inputs.

The experimental 87 × 12 matrix is packaged in `octa_gtrqc_sim/proton/data/fig2h.json`, with a separate numeric-matrix checksum verified by the dataset loader. Recorded native tables and their per-study manifests are in `validation/native/`.

The default build redraws recorded evidence. Explicit native recalculation goes to `generated/native/`; compare it with the retained reference exports before intentionally changing reviewed inputs. Synthetic transfer and hidden-twin arrays are retained outputs, not a new run of those protocols.
