import os
import time

from kubernetes import client, config, watch

class EpigeneticController:
    def __init__(self):
        self.v1, self.apps_v1 = self.load_kubernetes_config()

        # I need to think about this stuff below,
        # I'm not really even sure if this implementation will work as I hope
        # needs some kind of default assignment
        if True:
            self.read_namespaced_obj = self.apps_v1.read_namespaced_deployment
            self.patch_namespaced_obj = self.apps_v1.patch_namespaced_deployment
        elif True:
            self.read_namespaced_obj = self.apps_v1.read_namespaced_stateful_set
            self.patch_namespaced_obj = self.apps_v1.patch_namespaced_stateful_set
            
        self.namespace
        self.stress_threshold
        self.stability_window

        self.last_stress_time = time.time()


    def load_kubernetes_config(self):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        return client.CoreV1Api(), client.AppsV1Api()


    def get_obj_methylation_level(self, name):
        #if resource_type == "Deployment":
        #    obj = self.apps_v1.read_namespaced_deployment(name, self.namespace)
        #else:
        #    obj = self.apps_v1.read_namespaced_stateful_set(name, self.namespace)
        obj = self.read_namespaced_obj(name, self.namespace)
        obj_methylation_level = obj.spec.template.metadata.annotations.get(
            "epigenetic-mark.science/methylation-level",
            "0"
        }
        return int(obj_methylation_level)
            

    def patch_kubernetes_obj(self, name, new_level):
        print("HERE")


    def methylate(self, name):
        current_level = get_obj_methylation_level(name)
        new_level = current_level+1
        self.patch_kubernetes_obj(name, new_level)
        #print something here


    def demethylate(self, name):
        current_level = get_obj_methylation_level(name)
        # not sure if this return statement will work
        # probably actually should print something before returning
        return if current_level < 1
        new_level = current_level-1
        self.patch_kubernetes_obj(name, new_level)
        #print something here
        
    
    def monitor_stress(self, pod):
        labels = pods.metadata.labels

        if True:
            pod_mark = pod.metadata.annotations.get(
                "epigenetic-mark.science/methylation-level",
                "0"
            )
            parent_name = "clonal-organism"
            current_mark = self.get_deployment_or_statefulset_mark(name, "Deployment")

            if pod_mark == current_mark:
                self.methylate(parent_name)
            else:
                None
        elif True:
            parent_name = "-".join(pod.metadata.name.split("-")[:-1])
            self.methylate(parent_name)


    def monitor_lifespan(self):
        print("HERE")


    def run(self):
        print("THERE")


if __name__=="__main__":
    controller = EpigeneticController()
    controller.run()
