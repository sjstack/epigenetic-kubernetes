# ADR 0002: Disposition of `sjstack/add_stack_methylation_history`

## Status
Accepted

## Context
Branch commits `9d25f35`, `bab6be9`, `01ef969` added an unfinished LIFO `mutation-history` stack with unwired methods.

## Decision
Do not merge the branch. Salvage two intentions:

1. Full transition provenance → append-only event ledger (`src/epik/engine/`).
2. Generic target-path mutation → PhenotypeAdapter (`src/epik/integration/adapter.py`) mapping outputs onto `target_attribute` (e.g. `spec.replicas`).
