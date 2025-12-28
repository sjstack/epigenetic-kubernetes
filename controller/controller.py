import time
from kubernetes import client, config, watch

# Load K8s config (In-cluster if deployed, local if testing)
try:
    config.load_incluster_config()
except:
    config.load_kube_config()

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

NAMESPACE = "chaos-genome"
STRESS_THRESHOLD = 1 # number of restarts to trigger epigenetic change

def methylate_organism(pod_name, current_level):
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
   apps_v1.patch_namespaced_deployment("clonal-organism", NAMESPACE, body)

def monitor_cells():
    print("Watching for environmental stress (restarts)...")
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, NAMESPACE):
        pod = event['object']
        status = pod.status

        if event['type'] == "DELETED":
            deployment = apps_v1.read_namespaced_deployment("clonal-organism", NAMESPACE)
            current_mark = deployment.spec.template.metadata.annotations.get(
                "epigenetic-mark.science/methylation-level",
                "0"
            )

            methylate_organism("Colony", current_mark)

if __name__ == "__main__":
    monitor_cells()
