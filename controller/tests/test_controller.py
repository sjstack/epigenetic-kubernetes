import pytest
from unittest.mock import MagicMock, call
from controller.controller import methylate_organism, monitor_cells, get_k8s_client

NAMESPACE = "chaos-genome"

@pytest.fixture
def mock_k8s_client():
    v1 = MagicMock()
    apps_v1 = MagicMock()
    return v1, apps_v1

def test_methylate_organism(mock_k8s_client):
    _, apps_v1 = mock_k8s_client
    pod_name = "test-pod"
    current_level = "1"
    new_level = 2

    methylate_organism(apps_v1, pod_name, current_level)

    expected_body = {
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
                            "requests": {"cpu": f"{100 * new_level}m"}
                        }
                    }]
                }
            }
        }
    }

    apps_v1.patch_namespaced_deployment.assert_called_once_with(
        "clonal-organism", NAMESPACE, expected_body
    )

def test_monitor_cells_deleted_event(mock_k8s_client, mocker):
    v1, apps_v1 = mock_k8s_client

    # Mock watch.Watch
    mock_watch = mocker.patch('kubernetes.watch.Watch')
    mock_stream = mock_watch.return_value.stream

    # Mock Pod object
    mock_pod = MagicMock()
    mock_pod.status = MagicMock()

    # Simulate a DELETED event
    event = {'type': 'DELETED', 'object': mock_pod}
    mock_stream.return_value = [event]

    # Mock deployment reading
    mock_deployment = MagicMock()
    mock_deployment.spec.template.metadata.annotations.get.return_value = "1"
    apps_v1.read_namespaced_deployment.return_value = mock_deployment

    # Mock methylate_organism to verify it's called
    mock_methylate = mocker.patch('controller.controller.methylate_organism')

    monitor_cells(v1, apps_v1)

    # Verify methylate_organism was called correctly
    mock_methylate.assert_called_once_with(apps_v1, "Colony", "1")

def test_monitor_cells_non_deleted_event(mock_k8s_client, mocker):
    v1, apps_v1 = mock_k8s_client

    # Mock watch.Watch
    mock_watch = mocker.patch('kubernetes.watch.Watch')
    mock_stream = mock_watch.return_value.stream

    # Mock Pod object
    mock_pod = MagicMock()
    mock_pod.status = MagicMock()

    # Simulate a MODIFIED event (should be ignored)
    event = {'type': 'MODIFIED', 'object': mock_pod}
    mock_stream.return_value = [event]

    # Mock methylate_organism
    mock_methylate = mocker.patch('controller.controller.methylate_organism')

    monitor_cells(v1, apps_v1)

    # Verify methylate_organism was NOT called
    mock_methylate.assert_not_called()
