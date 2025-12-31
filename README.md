# Experiment: The Chaos Genome (Epigenetics in Kubernetes)

## Hypothesis
An organism (Kubernetes Deployment) that can dynamically alter its phenotype (Resource Limits) via epigenetic markers (Annotations) in response to environmental trauma (Chaos Mesh) will exhibit higher long-term "fitness" (stability) than a static organism.

## Scientific Context
In biological epigenetics, stressors cause **DNA methylation**, which modifies gene expression without changing the DNA sequence. 
* **The DNA:** Your `manifests/organism.yaml` manifest.
* **The Epigenetic Mark:** The `epigenetic-mark.science/methylation-level` annotation.
* **The Phenotype:** The resulting CPU/Memory allocation of the pod.

## Project Structure
- `manifests/`: YAML definitions for the environment, organism, and stressors.
- `controller/`: The Python-based "Epigenetic Engine" that monitors stress and applies markers.
- `setup.sh`: Automated infrastructure deployment for DigitalOcean.

---

## Provision Infrastructure
The `setup.sh` script handles both production (DOKS) and development (k3s on a single droplet) environments.

### For Development (k3s on Droplet)
1. Find your SSH key fingerprint from DigitalOcean: `doctl compute ssh-key list`.
2. Export the required variables and source the script:
   ```bash
   export EPIK_ENV=dev
   export DO_SSH_KEY="your_ssh_key_fingerprint"
   source setup.sh
   ```

### For Production (DOKS)
```bash
export EPIK_ENV=prod
source setup.sh
```

*Note: Sourcing the script ensures the `KUBECONFIG` environment variable is correctly set in your current session.*

---

## Deploy the Clonal Organism
Create the initial population of pods in the "ecological niche" (namespace):
```bash
kubectl apply -f manifests/organism.yaml
```
**Verify Birth:**
```bash
kubectl get pods -n chaos-genome -l app=cell
```

---

## Prepare the Epigenetic Engine
2. **Install Requirements:**
   ```bash
   pip install -r controller/requirements.txt
   ```
3. **Start Monitoring:**
   ```bash
   python controller/controller.py
   ```
   The engine will now watch for pod restarts in the `chaos-genome` namespace.

---

## Unit Testing

To run the unit tests for the controller:

1.  **Install Test Requirements:**
    ```bash
    pip install -r controller/test_requirements.txt -r controller/requirements.txt
    ```

2.  **Run Tests:**
    ```bash
    python -m pytest controller/tests/
    ```

---

## Inject Environmental Stress
Start the recurring "pod-kill" events using the Chaos Mesh `Schedule` manifest:
```bash
kubectl apply -f manifests/chaos-experiment.yaml
```

---

## Observations & Analysis
* **Monitor Adaptation:** Watch the controller output. When a pod is killed, you should see: `🧬 Stress detected in [pod-name]. Methylating to level X...`.
* **Verify Phenotype Change:** Check if the Deployment's CPU requests are increasing:
  ```bash
  kubectl describe deployment clonal-organism -n chaos-genome
  ```
* **Metric of Success:** Does the system become more resilient as CPU requests (phenotype) increase, or does it hit the cluster's carrying capacity?

---

## Cleanup
To tear down the resources:

# For Development
```bash
doctl compute droplet delete chaos-genome-dev
```

# For Production
```bash
doctl k8s cluster delete chaos-genome-cluster
```
