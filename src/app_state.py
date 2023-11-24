import logging
import time
from typing import Dict, Optional, Any
from tools import terraform
from prometheus_client import Gauge


class DeploymentState:
    def __init__(self, name: str, drifted: Optional[bool] = None, timestamp: Optional[float] = None,
                 success: Optional[bool] = True, plan: Optional[terraform.TerraformPlan] = None,
                 metadata: Optional[Dict] = None) -> None:
        self.name = name
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.success = success
        self.drifted = drifted
        self.plan = plan
        self.metadata = metadata if metadata is not None else {}
        self._bug_workaround_previous_folder = None

    @property
    def bug_workaround_previous_folder(self) -> Optional[str]:
        return self._bug_workaround_previous_folder

    @bug_workaround_previous_folder.setter
    def bug_workaround_previous_folder(self, value: str) -> None:
        self._bug_workaround_previous_folder = value

    def __repr__(self) -> str:
        return f"DeploymentState(name={self.name}, timestamp={self.timestamp}, success={self.success}, drifted={self.drifted}, " \
               f"plan={self.plan}, metadata={self.metadata})"


class ApplicationState:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.deployment_states: Dict[str, DeploymentState] = {}
        self.restful_api = None
        self.gauges: Dict[str, Gauge] = {}

    def set_deployment_state(self, name: str, state: DeploymentState) -> None:
        self.logger.debug(f"Setting deployment state for state named \"{name}\"")
        self.deployment_states[name] = state

    def get_deployment_state(self, name: str) -> Optional[DeploymentState]:
        self.logger.debug(f"Getting deployment state for state named \"{name}\"")
        return self.deployment_states.get(name, None)

    def delete_deployment_state(self, name: str) -> None:
        self.logger.debug(f"Deleting deployment state for state named \"{name}\"")
        if name in self.deployment_states:
            self.logger.debug(f"Deployment state named \"{name}\" exists, deleting it")
            del self.deployment_states[name]

    def get_deployment_state_as_item(self, name: str) -> Optional[Dict[str, Any]]:
        self.logger.debug(f"Getting deployment state named \"{name}\"")
        state = self.get_deployment_state(name)
        if state:
            return {
                "name": state.name,
                "timestamp": state.timestamp,
                "success": state.success,
                "drifted": state.drifted,
                "plan": state.plan.get_changes_breakdown() if state.plan else None,
                "metadata": state.metadata,
            }
        return None

    def get_deployment_states_as_items(self) -> []:
        self.logger.debug("Getting all deployment states")
        all_deployment_states = []
        for name, state in self.deployment_states.items():
            all_deployment_states.append({
                "name": name,
                "timestamp": state.timestamp,
                "success": state.success,
                "drifted": state.drifted,
                "plan": state.plan.get_changes_breakdown() if state.plan else None,
                "metadata": state.metadata,
            })
        return all_deployment_states

    def get_gauge(self, name: str) -> Optional[Gauge]:
        self.logger.debug(f"Getting gauge named \"{name}\"")
        return self.gauges.get(name, None)

    def set_gauge(self, name: str, gauge: Gauge) -> None:
        self.logger.debug(f"Setting gauge named \"{name}\"")
        self.gauges[name] = gauge
