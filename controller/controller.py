import os
import time
from kubernetes import client, config, watch

NAMESPACE = os.getenv("NAMESPACE", "chaos-genome")
# number of restarts to trigger epigenetic change
STRESS_THRESHOLD = int(os.getenv("STRESS_THRESHOLD", "1"))

def get_k8s_client():
    # Load K8s config (In-cluster if deployed, local if testing)
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()

    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    return v1, apps_v1

def methylate_organism(apps_v1, resource_type, name, current_level):
   new_level = int(current_level) + 1
   print(f"🧬 Stress detected in {resource_type}/{name}. Methylating to level {new_level}...")

   # Update the Deployment's template so new pods inherit the 'resistance'
   body = {
       "spec": {
           "template": {
               "metadata": {
                   "annotations": {
                       "epigenetic-mark.science/methylation-level": str(new_level)
                   }
               },
               "spec": {
                   "containers": [{
                       "name": "cell-process",
                       # The "Phenotype" change: Increasing resources/resilience
                       "resources": {
                           "requests": {"cpu":  f"{100 * new_level}m"}
                       }
                   }]
               }
           }
       }
   }

   if resource_type == "Deployment":
       apps_v1.patch_namespaced_deployment(name, NAMESPACE, body)
   else:
       apps_v1.patch_namespaced_stateful_set(name, NAMESPACE, body)

def monitor_cells(v1, apps_v1):
    print("Watching for environmental stress (restarts)...")
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, NAMESPACE):
        pod = event['object']
        
        if event['type'] == "DELETED":
            labels = pod.metadata.labels

            if labels.get("strategy") == "clonal":
                deployment = apps_v1.read_namespaced_deployment("clonal-organism", NAMESPACE)
                pod_mark = pod.metadata.annotations.get(
                    "epigenetic-mark.science/methylation-level",
                    "0"
                )
                current_mark = deployment.spec.template.metadata.annotations.get(
                    "epigenetic-mark.science/methylation-level",
                    "0"
                )
                if pod_mark == current_mark:
                    print(f"💀 Stress: Member of current generation ({pod_mark}) died.")
                    methylate_organism(apps_v1, "Colony", "clonal-organism", current_mark)
                else:
                    print(f"♻️  Cleanup: Old generation member ({pod_mark}), skipping Methylation.")
            elif labels.get("lineage"):
                parent_name = "-".join(pod.metadata.name.split("-")[:-1])
                stateful_set = apps_v1.read_namespaced_stateful_set(parent_name, NAMESPACE)
                current_mark = stateful_set.spec.template.metadata.annotations.get(
                    "epigenetic-mark.science/methylation-level",
                    "0"
                )
                methylate_organism(apps_v1, "Population", parent_name, current_mark)

def main():
    v1, apps_v1 = get_k8s_client()
    monitor_cells(v1, apps_v1)

if __name__ == "__main__":
    main()
