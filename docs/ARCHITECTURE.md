# Architecture

The biological kernel (`epik.engine`, `epik.model`, `epik.mechanisms`) has no Kubernetes imports. A single reducer commits intents. Randomness is hierarchical and keyed. Digests hash canonical state plus ledger.

```text
Intent --sort--> Reducer --> Event ledger
                     |
                     v
                  World state --> artifacts --> OutboundAPI
                                     ^
                                     |
                              ExposureTape (declared inputs only)
```

Kubernetes `SimulationRun` objects launch single-writer Jobs that execute `epik run-cross`. Artifacts are content-addressed files, not etcd documents.

Mechanism agents propose work; a coordinator barrier applies them in canonical order so shuffled arrival cannot change biology.

The PhenotypeAdapter is an out-of-process consumer. It reads `world.json` and writes a sample Deployment spec. It cannot import the reducer.
