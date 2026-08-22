from unittest.mock import MagicMock, patch

import pytest
from controller.epigenetic_controller import EpigeneticController

NAMESPACE = "epigenetik"

@pytest.fixture
def mock_k8s_client(mocker):
    # Mock the load_kubernetes_config method to prevent actual K8s config loading
    # and return mocked clients directly.
    mock_v1 = MagicMock()
    mock_apps_v1 = MagicMock()

    mocker.patch.object(
        EpigeneticController,
        'load_kubernetes_config',
        return_value=(mock_v1, mock_apps_v1)
    )

    return mock_v1, mock_apps_v1

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("NAMESPACE", NAMESPACE)
    monkeypatch.setenv("STRESS_THRESHOLD", "1")
    monkeypatch.setenv("STABILITY_WINDOW", "10")
    # Default to Deployment for most tests, can be overridden
    monkeypatch.setenv("MOCK_K8S", "false")

def test_initialization(mock_env, mock_k8s_client, mocker):
    """Test that the controller initializes with correct environment variables and config."""
    # We need to mock get_resource_type_at_startup to avoid infinite loop or waiting
    mocker.patch.object(EpigeneticController, 'get_resource_type_at_startup', return_value="Deployment")

    controller = EpigeneticController()

    assert controller.namespace == NAMESPACE
    assert controller.stress_threshold == 1
    assert controller.stability_window == 10
    assert controller.resource_type == "Deployment"
    assert controller.read_namespaced_obj == controller.apps_v1.read_namespaced_deployment
    assert controller.patch_namespaced_obj == controller.apps_v1.patch_namespaced_deployment

def test_get_resource_type_deployment(mock_env, mock_k8s_client):
    """Test detection of Deployment resource type."""
    mock_v1, mock_apps_v1 = mock_k8s_client

    # Setup mocks so Deployment check succeeds
    mock_apps_v1.read_namespaced_deployment.return_value = MagicMock()

    # Instantiate directly but we want to test get_resource_type_at_startup logic
    # We can't easily init without calling it in __init__, so we'll mock it for init
    # and then call the method manually or use a partial mock.

    # Better approach: partial mock of __init__ is messy.
    # Let's mock the API calls before init.

    with patch.object(EpigeneticController, 'load_kubernetes_config', return_value=(mock_v1, mock_apps_v1)):
         # We need to ensure we don't get stuck in the loop.
         # The code loops until success.
         controller = EpigeneticController()

    # Since we mocked the API to succeed on deployment read, it should set Deployment
    assert controller.resource_type == "Deployment"
    mock_apps_v1.read_namespaced_deployment.assert_called()

def test_get_resource_type_statefulset(mock_env, mock_k8s_client):
    """Test detection of StatefulSet resource type."""
    mock_v1, mock_apps_v1 = mock_k8s_client

    # Deployment raises exception, StatefulSet succeeds
    from kubernetes import client
    mock_apps_v1.read_namespaced_deployment.side_effect = client.exceptions.ApiException
    mock_apps_v1.read_namespaced_stateful_set.return_value = MagicMock()

    with patch.object(EpigeneticController, 'load_kubernetes_config', return_value=(mock_v1, mock_apps_v1)):
         controller = EpigeneticController()

    assert controller.resource_type == "StatefulSet"
    mock_apps_v1.read_namespaced_stateful_set.assert_called()

def test_get_obj_methylation_level(mock_env, mock_k8s_client, mocker):
    """Test retrieving methylation level from object annotations."""
    mocker.patch.object(EpigeneticController, 'get_resource_type_at_startup', return_value="Deployment")
    controller = EpigeneticController()

    mock_obj = MagicMock()
    mock_obj.spec.template.metadata.annotations = {"epigenetic-mark.science/methylation-level": "2"}
    controller.read_namespaced_obj.return_value = mock_obj

    level = controller.get_obj_methylation_level("test-obj")
    assert level == 2
    controller.read_namespaced_obj.assert_called_with("test-obj", NAMESPACE)

def test_get_obj_methylation_level_default(mock_env, mock_k8s_client, mocker):
    """Test default methylation level when annotation is missing."""
    mocker.patch.object(EpigeneticController, 'get_resource_type_at_startup', return_value="Deployment")
    controller = EpigeneticController()

    mock_obj = MagicMock()
    mock_obj.spec.template.metadata.annotations = {} # Empty
    controller.read_namespaced_obj.return_value = mock_obj

    level = controller.get_obj_methylation_level("test-obj")
    assert level == 0

def test_patch_kubernetes_obj(mock_env, mock_k8s_client, mocker):
    """Test patching the kubernetes object with new methylation level."""
    mocker.patch.object(EpigeneticController, 'get_resource_type_at_startup', return_value="Deployment")
    controller = EpigeneticController()

    new_level = 3
    controller.patch_kubernetes_obj("test-obj", new_level)

    expected_body = {
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "epigenetic-mark.science/methylation-level": "3"
                    }
                },
                "spec": {
                    "containers": [{
                        "name": "cell-process",
                        "resources": {
                            "requests": {"cpu": "300m"}
                        }
                    }]
                }
            }
        }
    }
    controller.patch_namespaced_obj.assert_called_with("test-obj", NAMESPACE, expected_body)

def test_methylate(mock_env, mock_k8s_client, mocker):
    """Test methylate method increases level and patches."""
    mocker.patch.object(EpigeneticController, 'get_resource_type_at_startup', return_value="Deployment")
    controller = EpigeneticController()

    mocker.patch.object(controller, 'get_obj_methylation_level', return_value=1)
    mock_patch = mocker.patch.object(controller, 'patch_kubernetes_obj')

    controller.methylate("test-obj")

    mock_patch.assert_called_with("test-obj", 2)

def test_demethylate(mock_env, mock_k8s_client, mocker):
    """Test demethylate method decreases level and patches."""
    mocker.patch.object(EpigeneticController, 'get_resource_type_at_startup', return_value="Deployment")
    controller = EpigeneticController()

    mocker.patch.object(controller, 'get_obj_methylation_level', return_value=2)
    mock_patch = mocker.patch.object(controller, 'patch_kubernetes_obj')

    result = controller.demethylate("test-obj")

    assert result is True
    mock_patch.assert_called_with("test-obj", 1)

def test_demethylate_at_zero(mock_env, mock_k8s_client, mocker):
    """Test demethylate does nothing if level is already 0."""
    mocker.patch.object(EpigeneticController, 'get_resource_type_at_startup', return_value="Deployment")
    controller = EpigeneticController()

    mocker.patch.object(controller, 'get_obj_methylation_level', return_value=0)
    mock_patch = mocker.patch.object(controller, 'patch_kubernetes_obj')

    result = controller.demethylate("test-obj")

    assert result is False
    mock_patch.assert_not_called()

def test_handle_stress_event_deployment_death(mock_env, mock_k8s_client, mocker):
    """Test handling stress event (pod death) for Deployment."""
    mocker.patch.object(EpigeneticController, 'get_resource_type_at_startup', return_value="Deployment")
    controller = EpigeneticController()

    # Mock pod
    mock_pod = MagicMock()
    mock_pod.metadata.name = "clonal-organism-12345"
    mock_pod.metadata.annotations = {"epigenetic-mark.science/methylation-level": "1"}

    # Mock current level matches pod level -> Stress
    mocker.patch.object(controller, 'get_obj_methylation_level', return_value=1)
    mock_methylate = mocker.patch.object(controller, 'methylate')

    controller.handle_stress_event(mock_pod)

    mock_methylate.assert_called_with("clonal-organism")
    assert "clonal-organism" in controller.last_event_time

def test_handle_stress_event_deployment_cleanup(mock_env, mock_k8s_client, mocker):
    """Test handling stress event (pod death) for Deployment where pod is old generation."""
    mocker.patch.object(EpigeneticController, 'get_resource_type_at_startup', return_value="Deployment")
    controller = EpigeneticController()

    # Mock pod
    mock_pod = MagicMock()
    mock_pod.metadata.name = "clonal-organism-12345"
    mock_pod.metadata.annotations = {"epigenetic-mark.science/methylation-level": "0"}

    # Mock current level is different (e.g., 1) -> Cleanup
    mocker.patch.object(controller, 'get_obj_methylation_level', return_value=1)
    mock_methylate = mocker.patch.object(controller, 'methylate')

    controller.handle_stress_event(mock_pod)

    mock_methylate.assert_not_called()

def test_handle_stress_event_statefulset_death(mock_env, mock_k8s_client, mocker):
    """Test handling stress event for StatefulSet."""
    mocker.patch.object(EpigeneticController, 'get_resource_type_at_startup', return_value="StatefulSet")
    controller = EpigeneticController()

    mock_pod = MagicMock()
    mock_pod.metadata.name = "organism-0-xyz" # Assuming standard pod naming or custom?
    # Logic is: parent_name = "-".join(pod.metadata.name.split("-")[:-1])
    # For StatefulSet usually pods are name-0, name-1.
    # But if "organism-0" is the pod name, splitting by "-" might be tricky if not careful.
    # The code says: parent_name = "-".join(pod.metadata.name.split("-")[:-1])
    # If pod is "organism-0", parent is "organism".
    # Wait, code logic:
    # parent_name = "-".join(pod.metadata.name.split("-")[:-1])
    # If pod is "organism-0", split -> ["organism", "0"]. join -> "organism".
    # But usually for StatefulSet, the parent is the StatefulSet name?
    # Actually, if we look at get_resource_type_at_startup for StatefulSet:
    # self.apps_v1.read_namespaced_stateful_set("organism-0", self.namespace)
    # This implies the StatefulSet is named "organism-0"? That's unusual naming for a Set unless it's a specific one.
    # Let's assume the code logic is correct for the deployment setup.

    mock_pod.metadata.name = "organism-0-podhash"
    # If StatefulSet name is "organism-0", then pod might be "organism-0-0" (standard) or "organism-0-xyz" (if controller manages it differently or if it's not standard SS).
    # But let's follow the code's logic.

    # Let's check logic:
    # parent_name = "-".join(pod.metadata.name.split("-")[:-1])
    # If pod="organism-0-123", parent="organism-0".

    mock_pod.metadata.name = "organism-0-123"
    parent_name = "organism-0"

    mocker.patch.object(controller, 'get_obj_methylation_level', return_value=1)
    mock_methylate = mocker.patch.object(controller, 'methylate')

    controller.handle_stress_event(mock_pod)

    mock_methylate.assert_called_with(parent_name)
    assert parent_name in controller.last_event_time

def test_check_pods_stability_deployment(mock_env, mock_k8s_client, mocker):
    """Test stability check for Deployment triggers demethylation."""
    mocker.patch.object(EpigeneticController, 'get_resource_type_at_startup', return_value="Deployment")
    controller = EpigeneticController()

    # Mock last event time to be old
    import time
    controller.last_event_time["clonal-organism"] = time.time() - 20 # > 10s window

    mock_demethylate = mocker.patch.object(controller, 'demethylate')

    controller.check_pods_stability()

    mock_demethylate.assert_called_with("clonal-organism")
    # Verify time updated (approx check)
    assert controller.last_event_time["clonal-organism"] > time.time() - 1

def test_check_pods_stability_deployment_no_action(mock_env, mock_k8s_client, mocker):
    """Test stability check for Deployment does not trigger if window not met."""
    mocker.patch.object(EpigeneticController, 'get_resource_type_at_startup', return_value="Deployment")
    controller = EpigeneticController()

    import time
    controller.last_event_time["clonal-organism"] = time.time() - 5 # < 10s window

    mock_demethylate = mocker.patch.object(controller, 'demethylate')

    controller.check_pods_stability()

    mock_demethylate.assert_not_called()

def test_check_pods_stability_statefulset(mock_env, mock_k8s_client, mocker):
    """Test stability check for StatefulSet triggers demethylation."""
    mocker.patch.object(EpigeneticController, 'get_resource_type_at_startup', return_value="StatefulSet")
    controller = EpigeneticController()

    mock_v1, mock_apps_v1 = mock_k8s_client

    # Mock list of stateful sets
    mock_ss = MagicMock()
    mock_ss.metadata.name = "organism-0"
    mock_apps_v1.list_namespaced_stateful_set.return_value.items = [mock_ss]

    import time
    controller.last_event_time["organism-0"] = time.time() - 20

    mock_demethylate = mocker.patch.object(controller, 'demethylate', return_value=True)

    controller.check_pods_stability()

    mock_demethylate.assert_called_with("organism-0")
    assert "organism-0" in controller.demethylated_pods
