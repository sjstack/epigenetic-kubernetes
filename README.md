# Epigenetic Kubernetes (epik)

**A coarse-grained, allele-resolved model of Arabidopsis reproductive epigenetics implemented through Kubernetes**, aligned with the [Gehring Lab](https://www.gehringplantlab.org/research).

V1 asks whether a compact mechanistic model can reproduce parent-of-origin methylation and expression in the Arabidopsis seed (embryo `1m:1p`, endosperm `2m:1p`, and maternal seed coat) across reciprocal Col-0 / Ler / Cvi crosses, and whether those same primitives can later be reused as a software architecture without rewriting the biology.

The legacy CPU-scaling controller is frozen under `legacy/` and `controller/`. It is not the scientific core.

## Research questions

1. Can the model recover allele-specific methylation and expression against the correct dosage nulls?
2. Can nearby TE state distinguish conserved imprinting, variable imprinting (`HDG3`), and DMRs with no imprinting consequence?
3. Can maternal DME, paternal ROS1, FIS-PRC2, and maternal-versus-paternal Pol IV be told apart?
4. Can endosperm region, DAP, and cell-cycle phase explain expression heterogeneity?
5. In a **separate** protocol, can the ROS1 sensor circuit reproduce euchromatic scars versus heterochromatic recovery?

See [docs/biology/MODEL_SPEC.md](docs/biology/MODEL_SPEC.md), [docs/biology/CLAIMS.md](docs/biology/CLAIMS.md), and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Install

Python 3.11+:

```bash
pip install -e ".[dev]"
make test
make legacy-demo
```

## Scientific CLI

```bash
epik validate-profile
epik init-cross --cross ColxCvi --out artifacts/init.json
epik run-cross ColxCvi --to-dap 7 --seed 1 --out artifacts/cross
epik call-imprinting artifacts/cross
epik run-scenario drm2-off
epik run-protocol ros1-homeostasis --out artifacts/ros1
epik export artifacts/cross
epik adapt artifacts/cross --target spec.replicas
```

Toy engine (no biology):

```bash
epik simulate --seed 1 --steps 10 --out artifacts/toy
epik replay artifacts/toy
epik digest artifacts/toy
```

## Architecture

Kubernetes orchestrates `SimulationRun` jobs. The biological engine is deterministic, Kubernetes-agnostic, and replayable from a seeded event ledger. External applications consume a read-only outbound API. Environmental inputs enter only as a schema-validated [ExposureTape](docs/ARCHITECTURE.md).

```text
telemetry -> ExposureTape -> engine -> ledger/artifacts -> outbound API -> consumers / PhenotypeAdapter
```

Consumers cannot write engine state. Attaching them does not change digests.

## Repository map

| Path | Role |
| :--- | :--- |
| `src/epik/engine/` | Logical time, RNG streams, reducer, ledger, digests |
| `src/epik/model/` | Profiles, crosses, methylomes, invariants |
| `src/epik/mechanisms/` | Maintenance, RdDM, DME/ROS1, seed, expression |
| `src/epik/operator/` | CRDs, reconciler, artifact jobs |
| `src/epik/integration/` | ExposureTape + PhenotypeAdapter |
| `profiles/arabidopsis-gehring-v1/` | Calibrated Arabidopsis profile |
| `controller/` | Frozen v0 CPU-analogy operator |
| `docs/biology/` | Evidence-labeled model contract |

## Legacy controller

`make legacy-demo` runs deterministic clonal and transgenerational mock cycles. Default `STABILITY_WINDOW` is **10** seconds. Helm `count` is lowercase. See [legacy/RELEASE.md](legacy/RELEASE.md).

## License

MIT. Copyright (c) 2026 Scott J. Stackley
