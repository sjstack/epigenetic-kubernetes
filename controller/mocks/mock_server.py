import sys
import os

from flask import Flask, request, Response, jsonify
from kubernetes.client import ApiClient

sys.path.append(os.getcwd())

from controller.mocks.k8s_client import mock_db, MockResponse


app = Flask(__name__)
api_client = ApiClient()


@app.route('/api/v1/namespaces/<namespace>/pods', methods=['GET'])
def list_pods(namespace):
    is_watch = request.args.get('watch', '').lower() == 'true'
    
    if is_watch:
        def generate_stream():
            mock_resp = MockResponse(mock_db.event_queue)
            for chunk in mock_resp.stream():
                yield chunk
        return Response(generate_stream(), mimetype='application/json')

    pod_list = mock_db.list_pods(namespace)
    return jsonify(api_client.sanitize_for_serialization(pod_list))


@app.route('/apis/apps/v1/namespaces/<namespace>/deployments/<name>', methods=['GET', 'PATCH'])
def handle_deployment(namespace, name):
    if request.method == 'GET':
        deploy = mock_db.get_deployment(name, namespace)
        if not deploy:
            return jsonify({"code": 404, "message": "Not Found"}), 404
        return jsonify(api_client.sanitize_for_serialization(deploy))

    if request.method == 'PATCH':
        body = request.get_json()
        updated = mock_db.update_deployment(name, namespace, body)
        return jsonify(api_client.sanitize_for_serialization(updated))


@app.route('/apis/apps/v1/namespaces/<namespace>/statefulsets/<name>', methods=['GET', 'PATCH'])
def hadle_statefulset(namespace, name):
    if request.method == 'GET':
        ss = mock_db.get_statefulset(name, namespace)
        if not ss:
            return jsonify({"code": 404, "message": "Not Found"}), 404
        return jsonify(api_client.sanitize_for_serialization(ss))

    if request.method == 'PATCH':
        body = request.get_json()
        updated = mock_db.update_statefulset(name, namespace, body)
        return jsonify(api_client.sanitize_for_serialization(updated))


@app.route('/apis/apps/v1/namespaces/<namespace>/statefulsets', methods=['GET'])
def list_statefulset(namespace):
    ss_list = mock_db.list_statefulsets(namespace)
    return jsonify(api_client.sanitize_for_serialization(ss_list))


@app.route('/debug/kill/<namespace>/<pod_name>', methods=['POST'])
def kill_pod(namespace, pod_name):
    success = mock_db.delete_pod(pod_name, namespace)
    if success:
        return jsonify({"status": "killed", "pod": pod_name})
    return jsonify({"status": "not_found"}), 404


if __name__=='__main__':
    mock_db.start_heartbeat(interval=5)
    app.run(host='0.0.0.0', port=6443, threaded=True)
