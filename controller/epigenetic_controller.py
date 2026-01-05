import os
import time

from kubernetes import client, config, watch

class EpigeneticController:
    def __init__(self):
        self.v1, self.apps_v1 = self.load_kubernetes_config()

        self.namespace = os.getenv("NAMESPACE", "chaos-genome")
        self.stress_threshold = int(os.getenv("STRESS_THRESHOLD", "1"))
        self.stability_window = int(os.getenv("STABILITY_WINDOW", "10"))

        self.last_event_time = time.time()

        self.resource_type = self.get_resource_type_at_startup()
        if self.resource_type == "Deployment":
            self.read_namespaced_obj = self.apps_v1.read_namespaced_deployment
            self.patch_namespaced_obj = self.apps_v1.patch_namespaced_deployment
        elif self.resource_type == "StatefulSet":
            self.read_namespaced_obj = self.apps_v1.read_namespaced_stateful_set
            self.patch_namespaced_obj = self.apps_v1.patch_namespaced_stateful_set

        print(f"🦠 Epigenetic Controller initialized for namespace: {self.namespace}")


    def load_kubernetes_config(self):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        return client.CoreV1Api(), client.AppsV1Api()


    def get_resource_type_at_startup(self):
        while True:
            try:
                self.apps_v1.read_namespaced_deployment("clonal-organism", self.namespace)
                #print something here
                return "Deployment"
            except client.exceptions.ApiException:
                pass

            try:
                self.apps_v1.read_namespaced_stateful_set("organism-0", self.namespace)
                #print something here
                return "StatefulSet"
            except client.exceptions.ApiException:
                pass

            time.sleep(5)


    def get_obj_methylation_level(self, name):
        obj = self.read_namespaced_obj(name, self.namespace)
        obj_methylation_level = obj.spec.template.metadata.annotations.get(
            "epigenetic-mark.science/methylation-level",
            "0"
        }
        return int(obj_methylation_level)
            

    def patch_kubernetes_obj(self, name, new_level):
        cpu_request_from_level = f"{100*new_level}m" if new_level > 0 else "10m"

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
                                "requests": {"cpu": cpu_request_from_level}
                            }
                        }]
                    }
                }
            }
        }

        self.patch_namespaced_obj(name, self.namespace, body)


    def methylate(self, name):
        current_level = get_obj_methylation_level(name)
        new_level = current_level+1

        print(f"🧬 Stress detected in {name}. Methylating to level {new_level}...")
        self.patch_kubernetes_obj(name, new_level)


    def demethylate(self, name):
        current_level = get_obj_methylation_level(name)
        return False if current_level < 1
        new_level = current_level-1

        print(f"🌿 Stability detected in {name}. Demethylating to level {new_level}...")
        self.patch_kubernetes_obj(name, new_level)
        return True
        
    
    def handle_stress_event(self, pod):
        self.last_event_time = time.time()

        labels = pod.metadata.labels
        pod_mark = int(pod.metadata.annotations.get(
            "epigenetic-mark.science/methylation-level",
            "0"
        )}

        if self.resource_type == "Deployment":
            name = "clonal-organism"
            current_mark = self.get_obj_methylation_level(name)

            if pod_mark == current_mark:
                print(f"💀 Stress: Member of current generation ({pod_mark}) died.")
                self.methylate(name)
            else:
                print(f"♻️  Cleanup: Old generation member ({pod_mark}), skipping Methylation.")
        elif self.resource_type == "StatefulSet":
            parent_name = "-".join(pod.metadata.name.split("-")[:-1])
            self.methylate(parent_name)


    def check_pods_stability(self):
        current_time = time.time()
        if current_time - self.last_event_time > self.stability_window:
            try:
                if self.resource_type == "Deployment":
                    name = "clonal-organism"
                    self.demethylate(name)
                elif self.resource_type == "StatefulSet":
                    stateful_sets = self.apps_v1.list_namespaced_stateful_set(self.namespace)
                    demethylation_occurred = False

                    for s_set in stateful_sets.items:
                        if s_set.metadata.name.startswith("organism-"):
                            demthylation_occurred = self.demethylate(s_set.metatdata.name)

                    if demethylation_occurred:
                        self.last_stress_time = current_time
            except Exception as e:
                print(f"⚠️ Error in stability check: {e}")


    def run(self):
        w = watch.Watch()
        print("👁️  Controller active. Watching for stress events...")

        for even in w.stream(self.v1.list_namespaced_pod, self.namespace, timeout_seconds=10):
            if event:
                if event['type'] = "DELETED":
                    self.handle_stress_event(event['object'])
            else:
                self.check_pods_stability()    


if __name__=="__main__":
    controller = EpigeneticController()
    controller.run()
