#!/usr/bin/env python3
import os
import sys
import threading
import time
import readline  # For better input handling

# Set environment to mock mode
os.environ["MOCK_K8S"] = "true"

# Add current directory to path so we can import controller
sys.path.append(os.getcwd())

try:
    from controller.epigenetic_controller import EpigeneticController
    from controller.mocks.k8s_client import mock_db
except ImportError as e:
    print(f"Error importing controller: {e}")
    sys.exit(1)

def run_controller(ctrl):
    ctrl.run()

def print_help():
    print("\nAvailable commands:")
    print("  list              - List all pods")
    print("  kill <pod_name>   - Kill (delete) a pod to trigger stress")
    print("  status            - Show organism methylation level")
    print("  help              - Show this help")
    print("  exit              - Exit the program")

def main():
    strategy = os.getenv("ORGANISM_STRATEGY", "transgenerational")
    print(f"🚀 Starting Epigenetic Controller in DEV MODE (Mock K8s)...")
    print(f"🧬 Strategy: {strategy.upper()}")

    # Start heartbeat to keep the controller loop active/checking stability
    mock_db.start_heartbeat(interval=5)
    print("💓 Mock Heartbeat started (every 5s)")

    ctrl = EpigeneticController()

    # Run controller in background thread
    t = threading.Thread(target=run_controller, args=(ctrl,), daemon=True)
    t.start()

    # Give it a second to initialize
    time.sleep(1)

    print("\n✅ Controller is running in background.")
    print_help()

    while True:
        try:
            # Use a prompt that stands out
            cmd_input = input("\n(dev-mode) > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if not cmd_input:
            continue

        parts = cmd_input.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == "exit" or cmd == "quit":
            break
        elif cmd == "help":
            print_help()
        elif cmd == "list":
            pods = mock_db.list_pods("chaos-genome").items
            print(f"\nFound {len(pods)} pods in 'chaos-genome':")
            for p in pods:
                print(f" - {p.metadata.name} (Labels: {p.metadata.labels})")
        elif cmd == "kill":
            if not args:
                print("Usage: kill <pod_name>")
                continue
            pod_name = args[0]
            if mock_db.delete_pod(pod_name, "chaos-genome"):
                print(f"💥 Pod '{pod_name}' deleted.")
            else:
                print(f"❌ Pod '{pod_name}' not found.")
        elif cmd == "status":
            strategy = os.getenv("ORGANISM_STRATEGY", "transgenerational")
            if strategy == "clonal":
                deploy = mock_db.get_deployment("clonal-organism", "chaos-genome")
                if deploy:
                    level = deploy.spec.template.metadata.annotations.get("epigenetic-mark.science/methylation-level", "0")
                    print(f"🧬 Clonal Organism (Deployment) Methylation Level: {level}")
                else:
                    print("⚠️  Deployment 'clonal-organism' not found.")
            else:
                # Transgenerational (StatefulSet)
                ss = mock_db.get_statefulset("organism-0", "chaos-genome")
                if ss:
                    level = ss.spec.template.metadata.annotations.get("epigenetic-mark.science/methylation-level", "0")
                    print(f"🧬 Organism-0 (StatefulSet) Methylation Level: {level}")
                else:
                    print("⚠️  StatefulSet 'organism-0' not found.")
        else:
            print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
