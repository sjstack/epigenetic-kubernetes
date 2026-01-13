import os
import time
import json

from kubernetes import client, config, watch

class EpigeneticController:
    def __init__(self):
        self.v1, self.apps_v1 = self.load_kubernetes_config()

        self.namespace = os.getenv("NAMESPACE", "epigenetik")
        self.stress_threshold = int(os.getenv("STRESS_THRESHOLD", "1"))
        self.stability_window = int(os.getenv("STABILITY_WINDOW", "10"))
        self.target_attribute = os.getenv(
            "TARGET_ATTRIBUTE",
            "spec.template.spec.containers[0].resources.requests.cpu"
        )
        self.mutation_type = os.getenvv("MUTATION_TYPE", "add")
        self.mutation_value = int(os.getenv("MUTATION_VALUE", "100"))

        self.demethylated_pods = set()
        self.last_event_time = {}
        #self.history = {}

        self.resource_type = self.get_resource_type_at_startup()
        if self.resource_type == "Deployment":
            self.read_namespaced_obj = self.apps_v1.read_namespaced_deployment
            self.patch_namespaced_obj = self.apps_v1.patch_namespaced_deployment
        elif self.resource_type == "StatefulSet":
            self.read_namespaced_obj = self.apps_v1.read_namespaced_stateful_set
            self.patch_namespaced_obj = self.apps_v1.patch_namespaced_stateful_set

        print(f"🦠 Epigenetic Controller initialized for namespace: {self.namespace}")


    def load_kubernetes_config(self):
        if os.getenv("MOCK_K8S") == "true":
            print("Using Mock K8s Client")
            from controller.mocks.k8s_client import MockCoreV1Api, MockAppsV1Api
            return MockCoreV1Api(), MockAppsV1Api()

        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        return client.CoreV1Api(), client.AppsV1Api()


    def get_resource_type_at_startup(self):
        while True:
            try:
                self.apps_v1.read_namespaced_deployment("clonal-organism", self.namespace)
                print("✅ Detected Strategy: CLONAL (Resource: Deployment)")
                return "Deployment"
            except client.exceptions.ApiException:
                pass

            try:
                self.apps_v1.read_namespaced_stateful_set("organism-0", self.namespace)
                print("✅ Detected Strategy: TRANSGENERATIONAL (Resource: StatefulSet)")
                return "StatefulSet"
            except client.exceptions.ApiException:
                pass

            time.sleep(5)


    def get_obj_methylation_level(self, name):
        obj = self.read_namespaced_obj(name, self.namespace)
        obj_methylation_level = obj.spec.template.metadata.annotations.get(
            "epigenetic-mark.science/methylation-level",
            "0"
        )
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


    def get_nested_value(self, obj_dict, path):
        key = path.replace("]", "").split(".")
        keys = [int(k) if "[" in k else k for k in keys if k]
        pass


    def methylate2(self, name):
        obj = self.read_namespaced_obj(name, self.namespace)

        history_json = obj.metadata.annotations.get(
            "epigenetic-mark.science/mutation-history", "[]"
        )
        history_stack = json.loads(history_json)

        obj_dict = self.api_client.sanitize_for_serialization(obj)
        current_value = self.get_nestsed_value(obj_dict, self.target_attribute)

        #still need to add this function
        new_value = self.calculate_next_value(current_value)
        stack_entry = {
            "level": len(history_stack)+1,
            "previous_value": current_value,
            "timestamp": time.time()
        }
        history_stack.append(stack_entry)

        print(f"🧬 Methylating {name}: {current_value} -> {new_value}")
        self.apply_mutation(name, new_value, history_stack)


    def methylate(self, name):
        current_level = self.get_obj_methylation_level(name)
        new_level = current_level+1

        print(f"🧬 Stress detected in {name}. Methylating to level {new_level}...")
        self.patch_kubernetes_obj(name, new_level)


    def demethylate2(self, name):
        obj = self.read_namespaced_obj(name, self.namespace)
        history_json = obj.metadata.annotations.get(
            "epigenetic-mark.science/mutation-history", "[]"
        )
        history_stack = json.loads(history_json)

        if not history_stack:
            return False

        last_entry = history_stack.pop()
        restore_value = last_entry["previous_value"]
        print(f"🌿 Demethylating {name}: Restoring {restore_value}")
        self.apply_mutation(name, restore_value, history_stack)

        return True


    def demethylate(self, name):
        current_level = self.get_obj_methylation_level(name)
        if current_level < 1:
            return False
        new_level = current_level-1

        print(f"🌿 Stability detected in {name}. Demethylating to level {new_level}...")
        self.patch_kubernetes_obj(name, new_level)
        return True
        
    
    def handle_stress_event(self, pod):
        labels = pod.metadata.labels
        pod_mark = int(pod.metadata.annotations.get(
            "epigenetic-mark.science/methylation-level",
            "0"
        ))

        if self.resource_type == "Deployment":
            name = "clonal-organism"
            current_mark = self.get_obj_methylation_level(name)

            if pod_mark == current_mark:
                print(f"💀 Stress: Member of current generation ({pod_mark}) died.")
                self.methylate(name)
                self.last_event_time[name] = time.time()
            else:
                print(f"♻️  Cleanup: Old generation member ({pod_mark}) from demethylation.")

        elif self.resource_type == "StatefulSet":
            # suddenly this looks same as above, so should probably consolidate this logic
            parent_name = "-".join(pod.metadata.name.split("-")[:-1])
            current_mark = self.get_obj_methylation_level(parent_name)

            if parent_name in self.demethylated_pods:
                self.demethylated_pods.discard(parent_name)
                print(f"♻️  Cleanup: Old lineage member ({parent_name}) from demethylation.")
            else:
                print(f"💀 Stress: Lineage member {parent_name} died.")
                self.methylate(parent_name)
                self.last_event_time[parent_name] = time.time()


    def check_pods_stability(self):
        current_time = time.time()

        try:
            if self.resource_type == "Deployment":
                name = "clonal-organism"
                stability_dur = current_time - self.last_event_time.get(name, current_time)

                if stability_dur > self.stability_window:
                    self.demethylate(name)
                    self.last_event_time[name] = current_time

            elif self.resource_type == "StatefulSet":
                stateful_sets = self.apps_v1.list_namespaced_stateful_set(self.namespace)
                
                for s_set in stateful_sets.items:
                    name = s_set.metadata.name

                    if name.startswith("organism-"):
                        stability_dur = current_time - self.last_event_time.get(name, current_time)

                        if stability_dur > self.stability_window:
                            if self.demethylate(name):
                                self.demethylated_pods.add(name)
                                self.last_event_time[name] = current_time

        except Exception as e:
            print(f"⚠️ Error in stability check: {e}")


    def run(self):
        w = watch.Watch()
        print("👁️  Controller active. Watching for stress events...")

        for event in w.stream(self.v1.list_namespaced_pod, self.namespace):
            if event:
                if event['type'] == "DELETED":
                    self.handle_stress_event(event['object'])
                else:
                    self.check_pods_stability()    


if __name__=="__main__":
    controller = EpigeneticController()
    controller.run()
