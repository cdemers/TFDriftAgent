from flask import Flask, jsonify, Response
from tools import api
import app_state
from prometheus_client import generate_latest


class API:
    def __init__(self, state: app_state.ApplicationState) -> None:
        self.state = state

        self.app = Flask(__name__)
        self.app.route('/api/deployment_states', methods=['GET'])(self.get_deployment_states)
        self.app.route('/api/deployment_states/<string:name>', methods=['GET'])(self.get_deployment_state)
        self.app.route('/metrics')(self.get_metrics)

    def get_deployment_states(self):
        items = self.state.get_deployment_states_as_items()
        # encapsulate every item in the list with the FormalItem class
        for i in range(len(items)):
            items[i] = api.FormalItem(kind="InfrastructureDeploymentState", name=items[i]["name"], spec=items[i]).get_item()
        return jsonify(api.FormalItemsList(items=items).get_item_list())

    def get_deployment_state(self, name):
        item = self.state.get_deployment_state_as_item(name=name)
        if not item:
            return jsonify({"error": f"State named \"{name}\" not found"}), 404
        return jsonify(api.FormalItem(kind="InfrastructureDeploymentState", name=name, spec=item).get_item())

    def get_metrics(self):
        return Response(generate_latest(), mimetype="text/plain")

    def run(self, host='0.0.0.0', port=8888):
        self.app.run(host=host, port=port)


# drift_monitor_agent_drifted_changes{name="Tenable Nessus Instance in Shared"} 0.0
# drift_monitor_agent_drift_check_success{name="Tenable Nessus Instance in Shared"} 1.0
# drift_monitor_agent_drift_check_error{name="Tenable Nessus Instance in Shared"} 0.0
