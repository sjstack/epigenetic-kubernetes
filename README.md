# Experiment: The Chaos Genome (Epigenetics in K8s)

## Hypothesis
An organism (Kubernetes Deployment) that can dynamically alter its phenotype (Resource Limits) via epigenetic markers (Annotations) in response to environmental trauma (Chaos Mesh) will exhibit higher long-term "fitness" (stability) than a static organism.

## Scientific Context
In biological epigenetics, stressors cause **DNA methylation**, which modifies gene expression without changing the DNA sequence. 
* **The DNA:** Your `organism.yaml` manifest.
* **The Epigenetic Mark:** `epigenetic-mark.science/methylation-level` annotation.
* **The Phenotype:** The resulting CPU/Memory allocation of the pod.

## Project Structure
- `manifests/`: YAML definitions for the environment, organism, and stressors.
- `controller/`: The Python-based "Epigenetic Engine" that monitors stress and applies markers.
- `setup.sh`: Automated infrastructure deployment for DigitalOcean.

## Running the Experiment
1. **Provision Infrastructure:**
   ```bash
   chmod +x setup.sh && ./setup.sh