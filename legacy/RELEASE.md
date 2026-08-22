# Legacy CPU-analogy freeze (v0)

This directory documents the pre-v1 controller that treated Kubernetes pod death as
cell death and mapped a methylation counter onto CPU requests.

That mapping is **not** part of the scientific core. It is frozen so the original
clonal and transgenerational demos remain reproducible via `make legacy-demo`.

- Controller: `controller/epigenetic_controller.py`
- Mock API: `controller/mocks/k8s_client.py`
- Helm population chart: `charts/population/`
- Characterization tests: `tests/legacy/`

Default `STABILITY_WINDOW` is **10** seconds (code and README agree). Helm values
use lowercase `count`. Clonal pods carry `strategy=clonal`; lineage pods carry
`lineage=organism-N` to match the mock client.
