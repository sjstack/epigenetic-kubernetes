
import os
import threading
import time
import pytest
from unittest.mock import MagicMock
from controller.mocks.k8s_client import mock_db

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("MOCK_K8S", "true")
    monkeypatch.setenv("ORGANISM_STRATEGY", "clonal")
    monkeypatch.setenv("NAMESPACE", "epigenetik")
    monkeypatch.setenv("STRESS_THRESHOLD", "1")
    monkeypatch.setenv("STABILITY_WINDOW", "2") # Short window for testing

@pytest.fixture(autouse=True)
def reset_mock_db(mock_env):
    mock_db.reset()

def test_epigenetic_controller_mock(mock_env, reset_mock_db):
    # Reload controller module to pick up env vars and mock injection
    import importlib
    import controller.epigenetic_controller
    importlib.reload(controller.epigenetic_controller)
    from controller.epigenetic_controller import EpigeneticController

    # Initialize controller
    ctrl = EpigeneticController()

    # Start controller run loop in a thread
    run_thread = threading.Thread(target=ctrl.run, daemon=True)
    run_thread.start()

    # Give it a moment to start up and detect resource type
    time.sleep(2)

    # Verify resource type detection (mock seeds Clonal Organism / Deployment)
    assert ctrl.resource_type == "Deployment"

    # --- STRESS PHASE ---
    print("\n--- Triggering Stress (Pod Deletion) ---")
    pod_name = "clonal-organism-pod-1"
    assert mock_db.get_pod(pod_name, "epigenetik") is not None

    mock_db.delete_pod(pod_name, "epigenetik")

    # Wait for reaction (methylation)
    time.sleep(1)

    # Verify methylation
    deploy = mock_db.get_deployment("clonal-organism", "epigenetik")
    level = deploy.spec.template.metadata.annotations.get("epigenetic-mark.science/methylation-level")
    print(f"Methylation Level after stress: {level}")
    assert level == "1"

    # Verify new pod created by mock controller has the new level
    # We need to find the new pod.
    pods = mock_db.list_pods("epigenetik").items
    new_pod = None
    for p in pods:
        if p.metadata.name != pod_name and p.metadata.labels.get("strategy") == "clonal":
            new_pod = p
            break

    assert new_pod is not None
    print(f"New pod created: {new_pod.metadata.name}")
    assert new_pod.metadata.annotations.get("epigenetic-mark.science/methylation-level") == "1"

    # --- STABILITY PHASE ---
    print("\n--- Waiting for Stability (Demethylation) ---")
    # STABILITY_WINDOW is 2s.
    # We need to wait > 2s.
    # The MockK8sDB recreating the pod triggered an ADDED event.
    # That ADDED event (triggered shortly after delete) should have been processed.
    # The `check_pods_stability` is called on non-DELETED events.
    # But it checks `stability_dur > stability_window`.
    # We need to ensure `check_pods_stability` is called *after* the window passes.

    # If no more events happen, `w.stream` blocks.
    # We need to trigger a dummy event or rely on `run` loop.
    # But `run` loop blocks on `stream`.

    # So we must trigger an event to wake it up after the window.
    # In a real cluster, there is background noise, or we can assume something happens.
    # Or maybe the controller should have a timeout on stream?
    # `w.stream` has `timeout_seconds`.
    # If I set timeout, the loop breaks or yields nothing?

    # For this test, I will manually trigger an event after sleeping.
    # Actually, we can now use the heartbeat or just trigger it.
    # The heartbeat is not started by default in the test unless we call it.
    # We will stick to manual trigger for deterministic testing, but we can verify heartbeat works too.
    # But manual trigger is fine.
    time.sleep(3)

    # Trigger a dummy event to wake up the controller loop
    # We can just update the deployment or something, or add a dummy pod.
    print("Triggering dummy event to wake up controller...")
    dummy_pod = MagicMock()
    dummy_pod.metadata.name = "dummy"
    dummy_pod.metadata.namespace = "epigenetik"
    dummy_pod.metadata.labels = {}

    # Use real trigger_event which sanitizes
    # mock_db.trigger_event("MODIFIED", dummy_pod) # Or ADDED
    # Wait, dummy_pod is MagicMock, sanitize might fail or produce empty dict.
    # Let's use a real V1Pod or just ensure MagicMock has to_dict?
    # The mock client implementation of trigger_event calls api.sanitize_for_serialization(obj).
    # If obj is MagicMock, it might return {}.
    # Previous tests passed with MagicMock?
    # Ah, I added "ensure metadata exists" logic.
    # Let's check if the previous test run actually worked or if I just assumed.
    # It passed.

    # But to be safe and consistent with heartbeat logic:
    from kubernetes.client import V1Pod, V1ObjectMeta
    dummy_pod_obj = V1Pod(
        metadata=V1ObjectMeta(
            name="dummy",
            namespace="epigenetik",
            resource_version="1"
        )
    )
    mock_db.trigger_event("MODIFIED", dummy_pod_obj)

    time.sleep(1)

    # Verify Demethylation
    deploy = mock_db.get_deployment("clonal-organism", "epigenetik")
    level = deploy.spec.template.metadata.annotations.get("epigenetic-mark.science/methylation-level")
    print(f"Methylation Level after stability: {level}")
    assert level == "0"
