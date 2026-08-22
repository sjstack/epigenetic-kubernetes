# ADR 0003: Disposition of `sjstack/containerize_this_shiiii`

## Status
Accepted

## Context
Branch commits `979436d`, `5329a5c`, `4c58bb4` added controller Dockerfiles, a Flask mock apiserver, and compose. The mock apiserver was unauthenticated on 6443 with an unpinned Python 3.14 base and root containers.

## Decision
Do not merge the Flask mock-apiserver. Reimplement the intent as:

- Hardened non-root image (`deploy/docker/Dockerfile`, UID 65532)
- Standard kubeconfig / in-cluster auth for any future live operator
- `make stack-up` via `deploy/docker/docker-compose.yaml`
- Image/security context covered by unit tests and the operator Helm chart
