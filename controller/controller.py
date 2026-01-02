import os
import time
import threading
from kubernetes import client, config, watch

NAMESPACE = os.getenv("NAMESPACE", "chaos-genome")
# number of restarts to trigger epigenetic change
STRESS_THRESHOLD = int(os.getenv("STRESS_THRESHOLD", "1"))
# demethylation stuff
LAST_STRESS_TIME = time.time()
STABILITY_WINDOW = 20 # seconds

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

def demethylate_organism(apps_v1, resource_type, name, current_level):
    new_level = max(0, int(current_level) - 1)
    if new_level == int(current_level):
        return

    print(f"🌿 Stability detected in {resource_type}/{name}. Demethylating to level {new_level}...")

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
                        "resources": {
                            "requests": {"cpu": f"{100 * new_level if new_level > 0 else 10}m"}
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
       
def monitor_cell_stress(v1, apps_v1):
    global LAST_STRESS_TIME

    print("Watching for environmental stress (restarts)...")
    w = watch.Watch()
    
    for event in w.stream(v1.list_namespaced_pod, NAMESPACE):        
        if event['type'] == "DELETED":
            LAST_STRESS_TIME = time.time()

            pod = event['object']
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

def monitor_cell_lifespan(v1, apps_v1):
    print("Monitoring cell lifespans for demethylation...")
    global LAST_STRESS_TIME
    while True:
        time.sleep(10)
        time_since_stress = time.time() - LAST_STRESS_TIME

        if time_since_stress > STABILITY_WINDOW:
            try:
                pod = v1.list_namespaced_pod(NAMESPACE, label_selector="app=cell", limit=1)
                if not pod.items:
                    continue
                labels = pod.items[0].metadata.labels
                
                if labels.get("strategy") == "clonal":
                    deployment = apps_v1.read_namespaced_deployment("clonal-organism", NAMESPACE)
                    current_mark = int(deployment.spaec.template.metadata.annotations.get(
                        "epigenetic-emark.science/methylation-level",
                        "0"
                    ))
                    
                    if current_mark > 0:
                        demethylate_organism(apps_v1, "Deployment", "clonal-organism", current_mark)
                        LAST_STRESS_TIME = time.time()
                elif labels.get("lineage"):
                    stateful_sets = apps_v1.list_namespaced_stateful_set(NAMESPACE)
                    demethylation_occurred = False

                    for s_set in stateful_sets.items:
                        if s_set.metadata.name.startswith("organism-"):
                            current_mark = int(s_set.spec.template.metadata.annotations.get(
                                "epigenetic-mark.science/methylation-level",
                                "0"
                            ))

                            if current_mark > 0:
                                demethylate_organism(
                                    apps_v1,
                                    "Population",
                                    s_set.metadata.name,
                                    current_mark
                                )
                                
                                LAST_STRESS_TIME = time.time()
            except Exception as e:
                print(f"ERROR - monitoring cell lifespan: {e}")

def main():
    v1, apps_v1 = get_k8s_client()

    lifespan_monitor = threading.Thread(
        target=monitor_cell_lifespan,
        args=(v1, apps_v1,),
        daemon=True
    )
    lifespan_monitor.start()
    
    monitor_cell_stress(v1, apps_v1)

if __name__ == "__main__":
    main()
