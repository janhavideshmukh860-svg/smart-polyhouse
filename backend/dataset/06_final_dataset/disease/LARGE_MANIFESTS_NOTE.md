# Note on large disease manifests

`disease_canonical_manifest.csv` (16.5 MB) and `disease_train_manifest.csv` (11.8 MB)
are not stored in this repository because they exceed the 10 MB per-file limit.

They are restored into the final distribution archive
(`smart_polyhouse_complete_final.zip`) from the original dataset checkpoint, and are
only required for **training** the disease model. Validation/test manifests and the
class mapping (used by the API at runtime for `/api/v1/disease/classes`) are present.
