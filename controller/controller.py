import os
import time
from kubernetes import client, config, watch

NAMESPACE = os.getenv("NAMESPACE", "chaos-genome")
ORGANISM_TYPE = os.getenv("ORGANISM_TYPE", "StatefulSet")
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

def methylate_organism(apps_v1, pod_name, current_level):
   new_level = int(current_level) + 1
   print(f"🧬 Stress detected in {pod_name}. Methylating to level {new_level}...")

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

   if ORGANISM_TYPE.lower() == "deployment":
       apps_v1.patch_namespaced_deployment("clonal-organism", NAMESPACE, body)
   elif ORGANISM_TYPE.lower() == "statefulset":
       apps_v1.patch_namespaced_stateful_set("organism", NAMESPACE, body)

def monitor_cells(v1, apps_v1):
    print("Watching for environmental stress (restarts)...")
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, NAMESPACE):
        pod = event['object']
        status = pod.status

        if event['type'] == "DELETED":
            if ORGANISM_TYPE.lower == "deployment":
                deployment = apps_v1.read_namespaced_deployment("clonal-organism", NAMESPACE)
                if deployment.status.updated_replics == deployment.spec.replicas:
                    current_mark = deployment.spec.template.metadata.annotations.get(
                        "epigenetic-mark.science/methylation-level",
                        "0"
                    )
                    methylate_organism(apps_v1, "Colony", current_mark)
            elif ORGANISM_TYPE.lower == "statefulset":
                deployment = apps_v1.read_namespaced_deployment("organism", NAMESPACE)
                current_mark = deployment.spec.template.metadata.annotations.get(
                    "epigenetic-mark.science/methylation-level",
                    "0"
                )
                methylate_organism(apps_v1, "Colony", current_mark)

def main():
    v1, apps_v1 = get_k8s_client()
    monitor_cells(v1, apps_v1)

if __name__ == "__main__":
    main()
