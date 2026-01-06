import json
import queue
import threading
import copy
import logging
import time
from unittest.mock import MagicMock
from kubernetes.client import V1Pod, V1PodList, V1Deployment, V1StatefulSet, V1StatefulSetList, V1ObjectMeta, V1PodSpec, V1Container, V1ResourceRequirements, V1PodTemplateSpec, V1DeploymentSpec, V1StatefulSetSpec, V1LabelSelector

logger = logging.getLogger(__name__)

class MockResponse:
    def __init__(self, event_queue):
        self.event_queue = event_queue

    def __iter__(self):
        return self

    def __next__(self):
        # Should not be called by watch.stream unless it iterates directly, but watch.stream uses iter_lines
        raise NotImplementedError("Use iter_lines for watch stream")

    def stream(self, amt=None, decode_content=False):
        # watch.iter_resp_lines calls resp.stream(amt=None, decode_content=False)
        # It expects a generator yielding segments (bytes or str)
        while True:
            item = self.event_queue.get()
            if item is None:
                break
            # Yield as bytes, followed by newline
            yield json.dumps(item).encode('utf-8') + b'\n'

    def close(self):
        pass

    def release_conn(self):
        pass

class MockK8sDB:
    def __init__(self):
        self.reset()

    def reset(self):
        self.event_queue = queue.Queue()
        self.pods = {} # (name, ns) -> V1Pod
        self.deployments = {} # (name, ns) -> V1Deployment
        self.statefulsets = {} # (name, ns) -> V1StatefulSet

        # Seed initial data
        self._seed_data()

    def _seed_data(self):
        # Default seed: Clonal Organism Deployment
        ns = "chaos-genome"
        name = "clonal-organism"

        deploy = V1Deployment(
            metadata=V1ObjectMeta(name=name, namespace=ns),
            spec=V1DeploymentSpec(
                selector=V1LabelSelector(match_labels={"app": "cell", "strategy": "clonal"}),
                template=V1PodTemplateSpec(
                    metadata=V1ObjectMeta(
                        labels={"app": "cell", "strategy": "clonal"},
                        annotations={"epigenetic-mark.science/methylation-level": "0"}
                    ),
                    spec=V1PodSpec(
                        containers=[
                            V1Container(
                                name="cell-process",
                                resources=V1ResourceRequirements(
                                    requests={"cpu": "10m"}
                                )
                            )
                        ]
                    )
                )
            )
        )
        self.deployments[(name, ns)] = deploy

        # Create a pod for this deployment
        pod_name = f"{name}-pod-1"
        pod = V1Pod(
            metadata=V1ObjectMeta(
                name=pod_name,
                namespace=ns,
                labels={"app": "cell", "strategy": "clonal"},
                annotations={"epigenetic-mark.science/methylation-level": "0"}
            ),
            spec=deploy.spec.template.spec,
            status=MagicMock()
        )
        self.pods[(pod_name, ns)] = pod

        # Default seed: StatefulSet
        ss_name = "organism-0"
        ss = V1StatefulSet(
             metadata=V1ObjectMeta(name=ss_name, namespace=ns),
             spec=V1StatefulSetSpec(
                service_name="organism",
                selector=MagicMock(),
                template=V1PodTemplateSpec(
                    metadata=V1ObjectMeta(
                        labels={"app": "cell", "lineage": "organism-0"},
                        annotations={"epigenetic-mark.science/methylation-level": "0"}
                    ),
                     spec=V1PodSpec(
                        containers=[
                            V1Container(
                                name="cell-process",
                                resources=V1ResourceRequirements(
                                    requests={"cpu": "10m"}
                                )
                            )
                        ]
                    )
                )
             )
        )
        self.statefulsets[(ss_name, ns)] = ss

        # Create a pod for this statefulset
        ss_pod_name = f"{ss_name}-0"
        ss_pod = V1Pod(
            metadata=V1ObjectMeta(
                name=ss_pod_name,
                namespace=ns,
                labels={"app": "cell", "lineage": "organism-0"},
                annotations={"epigenetic-mark.science/methylation-level": "0"}
            ),
            spec=ss.spec.template.spec,
             status=MagicMock()
        )
        self.pods[(ss_pod_name, ns)] = ss_pod

    def trigger_event(self, event_type, obj):
        # Convert object to dict for JSON serialization, but watch.stream decodes it back to object using unmarshal
        # However, kubernetes client `ApiClient.sanitize_for_serialization` can turn object to dict.
        from kubernetes.client import ApiClient
        api = ApiClient()
        obj_dict = api.sanitize_for_serialization(obj)

        # Ensure resourceVersion exists in metadata for Watch compatibility
        if 'metadata' not in obj_dict:
            obj_dict['metadata'] = {}

        if 'resourceVersion' not in obj_dict['metadata'] or obj_dict['metadata']['resourceVersion'] is None:
             obj_dict['metadata']['resourceVersion'] = "1"

        event = {
            "type": event_type,
            "object": obj_dict
        }
        self.event_queue.put(event)

    def get_pod(self, name, namespace):
        return self.pods.get((name, namespace))

    def list_pods(self, namespace, label_selector=None, limit=None):
        items = []
        for (name, ns), pod in self.pods.items():
            if ns == namespace:
                # Basic label selector implementation
                if label_selector:
                    try:
                        k, v = label_selector.split("=")
                        if pod.metadata.labels.get(k) != v:
                            continue
                    except ValueError:
                        # Ignore complex selectors for now or handle simple key existence
                        pass
                items.append(pod)

        if limit:
            items = items[:int(limit)]

        return V1PodList(items=items, metadata=MagicMock())

    def delete_pod(self, name, namespace):
        key = (name, namespace)
        if key in self.pods:
            pod = self.pods.pop(key)
            self.trigger_event("DELETED", pod)

            # Simulate Controller behavior: Recreate pod if it belongs to a Deployment/StatefulSet
            # We use a timer to simulate delay
            threading.Timer(0.1, self._recreate_pod, args=(pod,)).start()
            return True
        return False

    def _recreate_pod(self, old_pod):
        # Determine owner
        labels = old_pod.metadata.labels or {}
        ns = old_pod.metadata.namespace

        new_pod = None

        if labels.get("strategy") == "clonal":
            # Assume Deployment "clonal-organism"
            deploy = self.get_deployment("clonal-organism", ns)
            if deploy:
                # Create new pod from deployment template
                new_name = f"clonal-organism-pod-{int(time.time()*1000)}"
                new_pod = V1Pod(
                    metadata=V1ObjectMeta(
                        name=new_name,
                        namespace=ns,
                        labels=deploy.spec.template.metadata.labels,
                        annotations=deploy.spec.template.metadata.annotations
                    ),
                    spec=deploy.spec.template.spec,
                    status=MagicMock()
                )

        elif labels.get("lineage"):
            # Assume StatefulSet
            ss_name = labels.get("lineage")
            ss = self.get_statefulset(ss_name, ns)
            if ss:
                # Recreate pod with same name (StatefulSet behavior)
                new_name = old_pod.metadata.name
                new_pod = V1Pod(
                    metadata=V1ObjectMeta(
                        name=new_name,
                        namespace=ns,
                        labels=ss.spec.template.metadata.labels,
                        annotations=ss.spec.template.metadata.annotations
                    ),
                    spec=ss.spec.template.spec,
                    status=MagicMock()
                )

        if new_pod:
            self.pods[(new_pod.metadata.name, ns)] = new_pod
            self.trigger_event("ADDED", new_pod)

    def get_deployment(self, name, namespace):
        return self.deployments.get((name, namespace))

    def update_deployment(self, name, namespace, body):
        key = (name, namespace)
        if key in self.deployments:
            # Apply patch
            # This is a deep merge.
            deploy = self.deployments[key]
            # Simple implementation for the specific fields we care about
            if 'spec' in body and 'template' in body['spec']:
                tmpl = body['spec']['template']
                if 'metadata' in tmpl and 'annotations' in tmpl['metadata']:
                    # annotations might be None
                    if deploy.spec.template.metadata.annotations is None:
                         deploy.spec.template.metadata.annotations = {}

                    deploy.spec.template.metadata.annotations.update(
                        tmpl['metadata']['annotations']
                    )
                if 'spec' in tmpl and 'containers' in tmpl['spec']:
                    # Assuming first container
                    c_patch = tmpl['spec']['containers'][0]
                    c_orig = deploy.spec.template.spec.containers[0]
                    if 'resources' in c_patch:
                         c_orig.resources.requests.update(c_patch['resources']['requests'])

            # Simulate rolling update: recreate pods
            # Find pods for this deployment
            to_delete = []
            for (pname, pns), pod in self.pods.items():
                if pns == namespace and pod.metadata.labels.get("strategy") == "clonal":
                     to_delete.append(pname)

            # In real K8s, old pods terminate, new pods start.
            # Here we just update the existing pods "in place" or replace them to simulate update
            for pname in to_delete:
                # Update pod spec to match deployment
                pod = self.pods[(pname, namespace)]
                pod.metadata.annotations.update(deploy.spec.template.metadata.annotations)
                pod.spec.containers[0].resources.requests.update(
                     deploy.spec.template.spec.containers[0].resources.requests
                )

            return deploy
        return None

    def get_statefulset(self, name, namespace):
        return self.statefulsets.get((name, namespace))

    def list_statefulsets(self, namespace):
        items = [s for (n, ns), s in self.statefulsets.items() if ns == namespace]
        return V1StatefulSetList(items=items, metadata=MagicMock())

    def update_statefulset(self, name, namespace, body):
        key = (name, namespace)
        if key in self.statefulsets:
             ss = self.statefulsets[key]
             # Similar patching logic
             if 'spec' in body and 'template' in body['spec']:
                tmpl = body['spec']['template']
                if 'metadata' in tmpl and 'annotations' in tmpl['metadata']:
                    ss.spec.template.metadata.annotations.update(
                        tmpl['metadata']['annotations']
                    )
                if 'spec' in tmpl and 'containers' in tmpl['spec']:
                    c_patch = tmpl['spec']['containers'][0]
                    c_orig = ss.spec.template.spec.containers[0]
                    if 'resources' in c_patch:
                         c_orig.resources.requests.update(c_patch['resources']['requests'])

             # Update associated pods
             to_delete = []
             for (pname, pns), pod in self.pods.items():
                if pns == namespace and pod.metadata.labels.get("lineage") == name:
                    to_delete.append(pname)

             for pname in to_delete:
                pod = self.pods[(pname, namespace)]
                pod.metadata.annotations.update(ss.spec.template.metadata.annotations)
                pod.spec.containers[0].resources.requests.update(
                     ss.spec.template.spec.containers[0].resources.requests
                )

             return ss
        return None

# Singleton instance
mock_db = MockK8sDB()

class MockCoreV1Api:
    def __init__(self):
        self.db = mock_db

    def list_namespaced_pod(self, namespace, **kwargs):
        """
        :return: V1PodList
        """
        if kwargs.get('watch'):
            return MockResponse(self.db.event_queue)
        else:
            return self.db.list_pods(namespace, kwargs.get('label_selector'), kwargs.get('limit'))

class MockAppsV1Api:
    def __init__(self):
        self.db = mock_db

    def read_namespaced_deployment(self, name, namespace):
        res = self.db.get_deployment(name, namespace)
        if not res:
            from kubernetes.client.exceptions import ApiException
            raise ApiException(status=404, reason="Not Found")
        return res

    def patch_namespaced_deployment(self, name, namespace, body):
        return self.db.update_deployment(name, namespace, body)

    def read_namespaced_stateful_set(self, name, namespace):
        res = self.db.get_statefulset(name, namespace)
        if not res:
            from kubernetes.client.exceptions import ApiException
            raise ApiException(status=404, reason="Not Found")
        return res

    def patch_namespaced_stateful_set(self, name, namespace, body):
        return self.db.update_statefulset(name, namespace, body)

    def list_namespaced_stateful_set(self, namespace):
        return self.db.list_statefulsets(namespace)

# Helper to simulate chaos
def simulate_pod_deletion(pod_name, namespace="chaos-genome"):
    mock_db.delete_pod(pod_name, namespace)
