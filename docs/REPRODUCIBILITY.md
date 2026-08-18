# Reproducibility

Every run stores `seed`, `checkpoint.json`, `ledger.json`, `world.json`, and `digest.txt`.

```bash
epik run-cross ColxCvi --seed 1 --out artifacts/cross
epik digest artifacts/cross
epik replay artifacts/cross
```

Identical seed and inputs must yield identical digests locally and in a Job runner. Consumers attached to the outbound API must not change the digest. A recorded ExposureTape must replay byte-identically.

Release gates: `epik release-gates`. Independent review and a clean-clone reproduction are required before treating results as publication-grade.
