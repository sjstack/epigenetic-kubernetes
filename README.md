# The Chaos Genome: Epigenetic Adaptation in Kubernetes

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg) ![Python](https://img.shields.io/badge/python-3.9+-blue.svg) ![Kubernetes](https://img.shields.io/badge/kubernetes-1.25+-green.svg)

**A scientific simulation that treats Kubernetes workloads as biological organisms.**

This project tests the hypothesis that **epigenetic adaptation**—the dynamic modification of gene expression (resource limits) in response to environmental stress—creates more resilient distributed systems than static configurations.

Also, I want to run experiments for emergent behavior by using the kubernetes framework as a model for epigenetics.

## 🧬 Context

This experiment translates biological mechanisms directly into Cloud Native primitives:

| Biological Concept | Kubernetes Implementation |
| :--- | :--- |
| **The Organism** | A `Deployment` (Clonal) or `StatefulSet` (Lineage). |
| **The Phenotype** | The CPU/Memory requests defined in the Pod spec. |
| **The Epigenetic Mark** | The `epigenetic-mark.science/methylation-level` annotation. |
| **Methylation** | Increasing resource requests in response to "Cell Death" (Pod OOM/Crash). |
| **Demethylation** | Actively shedding resources during stability. |

### Demethylation
In nature, methylation is not a one-way street; it is actively pruned to maintain homeostasis. 
* **In this cluster:** If the organism remains stable (no restarts) for a set `STABILITY_WINDOW`, the controller actively "demethylates" the pod, reducing its resource consumption to prevent "resource hoarding" (over-provisioning).

## 🏛️ Architecture

* **`manifests/`**: Defines the "Environmental Stressors" (Chaos Mesh schedules).
* **`charts/population/`**: A Helm chart defining the organism. Supports two evolutionary strategies:
    * **Clonal:** A standard Deployment. All pods share the same "genetic" memory.
    * **Transgenerational:** A StatefulSet. Each replica tracks its own unique lineage and adaptation history.
* **`controller/epigenetic_controller.py`**: The "Central Nervous System." A class-based Python operator that:
    1.  **Auto-detects** the organism strategy (Clonal vs. Lineage).
    2.  **Monitors** for `DELETED` events (Cell Death).
    3.  **Methylates** (scales up) survivors.
    4.  **Demethylates** (scales down) during peace.
* **`setup.sh`**: Automated lab technician. Provisions a cluster (DigitalOcean or local k3s), installs Chaos Mesh, and deploys the population.

---

## 🚀 Getting Started

### Prerequisites
* [Docker](https://www.docker.com/) & [kubectl](https://kubernetes.io/docs/tasks/tools/)
* [Helm](https://helm.sh/)
* [doctl](https://docs.digitalocean.com/reference/doctl/how-to/install/) (DigitalOcean CLI)
* Python 3.9+

### 1. Provision the Environment
The `setup.sh` script handles the entire lifecycle. You can run in **Development** (k3s on a single Droplet) or **Production** (DOKS Cluster).

**For Development (Recommended):**
```bash
# Set your strategy: "clonal" (Deployment) or "transgenerational" (StatefulSet)
export ORGANISM_STRATEGY="transgenerational" 
export EPIK_ENV="dev"
export DO_SSH_KEY="<your_ssh_fingerprint>"

source setup.sh
```
*The script will provision infrastructure, install Chaos Mesh, and deploy the initial population.*

### 2. Start the Epigenetic Engine
Once the cluster is ready, start the controller locally to begin the simulation.

```bash
# Install dependencies
pip install -r controller/requirements.txt

# Run the controller
python controller/epigenetic_controller.py
```
**Output:**
> `🦠 Epigenetic Controller initialized for namespace: chaos-genome`
> `✅ Detected Strategy: TRANSGENERATIONAL (Resource: StatefulSet)`
> `👁️ Controller active. Watching for stress events...`

### 3. Inject Environmental Stress
Without stress, the organism will remain at baseline (Methylation Level 0). Trigger a recurring "Pod Kill" event to force adaptation:

```bash
kubectl apply -f manifests/chaos-experiment.yaml
```

---

## 🔬 Observation & Analysis

### Monitoring Adaptation (Methylation)
Watch the controller logs. When Chaos Mesh kills a pod, the controller should react:
> `💀 Stress: Member of current generation (0) died.`
> `🧬 Stress detected in organism-0. Methylating to level 1...`

### Monitoring Homeostasis (Demethylation)
If you delete the Chaos Experiment (`kubectl delete -f manifests/chaos-experiment.yaml`) and wait for the `STABILITY_WINDOW` (default: 20s), you will see the demethylation kick in:
> `🌿 Stability detected in organism-0. Demethylating to level 0...`

### Verifying Phenotype
Check the actual resource allocation of the pods to see the physical change:
```bash
kubectl describe pod -n chaos-genome -l app=cell
```
*Look for `Requests: cpu` increasing (e.g., `100m` -> `200m`) or decreasing.*

---

## 🛠️ Development

### Running Tests
The project uses `pytest` with mocks for the Kubernetes API.

```bash
# Install test deps
pip install -r controller/test_requirements.txt

# Run suite
python -m pytest controller/tests/
```

### Configuration
You can tweak the experiment parameters via environment variables when running the controller:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `NAMESPACE` | `chaos-genome` | The K8s namespace for the experiment. |
| `STRESS_THRESHOLD` | `1` | Restarts required to trigger methylation. |
| `STABILITY_WINDOW` | `20` | Seconds of silence before demethylation begins. |

---

## ⚖️ License

This project is open source under the [MIT License](LICENSE).

Copyright (c) 2026 Scott J. Stackley