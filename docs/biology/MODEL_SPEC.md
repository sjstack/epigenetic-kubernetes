# Model specification (`arabidopsis-gehring-v1`)

This document is the research contract for v1. Every mechanism is labeled with evidence strength and modeling status.

Evidence: **A** causal/core, **B** Arabidopsis-specific, **C** supported association, **H** hypothesis (off by default).
Status: **direct**, **coarse-grained**, or **deferred**.

Machine-readable rows: [mechanisms.json](mechanisms.json). Lifecycle: [SEED_LIFECYCLE.md](SEED_LIFECYCLE.md). Citations: [EVIDENCE.md](EVIDENCE.md). Datasets: [DATASETS.md](DATASETS.md). Allowed claims: [CLAIMS.md](CLAIMS.md).

## Layers

- `angiosperm-core-v1`: ploidy, compartments, switchable pathways, schemas.
- `arabidopsis-gehring-v1`: Col-0, Ler, Cvi (C24 for ROS1), reciprocal crosses, Gehring locus panel.

## Invariants

1. Site counts are bounded (CG ≤ 64, CHG ≤ 64, CHH ≤ 96 per locus copy).
2. Embryo is `1m:1p`. Endosperm is `2m:1p`. Seed coat is maternal diploid `2m`.
3. Endosperm and seed coat are pedigree-terminal.
4. Parent of origin is distinct from accession and ancestry.
5. Endosperm expression is scored against a `2/3` maternal dosage null; embryo against `1/2`.
6. A DMR does not imply imprinting (`DMR_NULL1`).
7. Infrastructure events (pod kill, reconcile retries) are biologically inert.

## Pathways

| Mechanism | Evidence | Status | Citation |
| :--- | :--- | :--- | :--- |
| MET1/VIM CG maintenance | A | direct | [Law & Jacobsen 2010](https://doi.org/10.1038/nrg2719) |
| CMT3–H3K9me2 CHG | A | direct | [Du et al. 2012](https://doi.org/10.1126/science.1221779) |
| CMT2/DDM1 CHH | B | coarse-grained | [Zemach et al. 2013](https://doi.org/10.1016/j.cell.2013.02.001) |
| Canonical RdDM (Pol IV–DRM2) | A | coarse-grained | [Matzke & Mosher 2014](https://doi.org/10.1038/nrg3683) |
| DME central-cell demethylation | A | direct | [Gehring et al. 2006](https://doi.org/10.1016/j.cell.2005.12.034), [Gehring et al. 2009](https://doi.org/10.1126/science.1171609) |
| ROS1 sperm/somatic demethylation | A | direct | [Hemenway & Gehring 2025](https://doi.org/10.1186/s13059-025-03745-w) |
| ROS1 promoter sensor | A | direct | [Williams et al. 2015](https://doi.org/10.1371/journal.pgen.1005142) |
| FIS-PRC2 H3K27me3 | A | direct | [Gehring et al. 2006](https://doi.org/10.1016/j.cell.2005.12.034) |
| Parent-specific Pol IV | A | coarse-grained | [Satyaki & Gehring 2019](https://doi.org/10.1105/tpc.19.00047) |
| HDG3 TE epiallele | A | direct | [Pignatta et al. 2018](https://doi.org/10.1371/journal.pgen.1007469) |
| Endosperm regional/cell-cycle heterogeneity | B | coarse-grained | [Picard et al. 2021](https://doi.org/10.1038/s41477-021-00922-0) |
| DAP 3/5/7 progression | B | coarse-grained | [Martin et al. 2026](https://doi.org/10.1038/s41477-026-02295-8) |
| Noncanonical RdDM | H | deferred | — |
| Adaptive transgenerational memory from arbitrary stress | H | deferred | — |

## Expression rules

Locus-specific, never a global methylation–expression sign:

- `MEA`, `FWA`, `FIS2`: hypomethylation activates (MEGs after maternal DME).
- `PHE1`: maternal H3K27me3 represses (PEG).
- `HDG3`: nearby TE methylation promotes paternal expression; Cvi unmethylated TE is biallelic.
- `ACT7`, `UBQ10`: constitutive biallelic dosage.
- `DMR_NULL1`: accession-variable methylation, null expression effect.

## Observation models

WGBS and RNA-seq are sampled observations, not molecular state. The imprinting caller tests departure from dosage after coverage, mapping-bias, and seed-coat contamination flags.
