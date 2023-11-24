import os
import json
import logging
import subprocess
from typing import Tuple, Dict, Any, Optional


class ConsoleException(Exception):
    """Exception raised when terraform command fails.

    Attributes:
        message -- explanation of the error
        details -- details of the error
    """

    def __init__(self, message, details=""):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message} - Details: {self.details}'


class TerraformPlan:
    """
    Represents a Terraform plan
    https://developer.hashicorp.com/terraform/internals/json-format
    """
    def __init__(self, plan_dict: dict):
        self.plan = plan_dict

    @property
    def format_version(self) -> str:
        return self.plan.get('format_version', '')

    @property
    def terraform_version(self) -> str:
        return self.plan.get('terraform_version', '')

    @property
    def timestamp(self) -> str:
        return self.plan.get('timestamp', '')

    def count_resources_by_action(self, action: str) -> int:
        return sum(action in resource['change']['actions'] for resource in self.plan.get('resource_changes', []))

    def count_resources_except_noop_and_read(self) -> int:
        excluded_actions = {'no-op', 'read'}
        return sum(any(action not in excluded_actions for action in resource['change']['actions'])
                   for resource in self.plan.get('resource_changes', []))

    def count_total_resources(self) -> int:
        return len(self.plan.get('resource_changes', []))

    def count_resources(self) -> dict:
        action_counts = {
            "no-op": self.count_resources_by_action("no-op"),
            "create": self.count_resources_by_action("create"),
            "read": self.count_resources_by_action("read"),
            "update": self.count_resources_by_action("update"),
            "delete": self.count_resources_by_action("delete"),
            "delete, create": self.count_resources_by_action("delete, create"),
            "create, delete": self.count_resources_by_action("create, delete"),
        }
        return action_counts

    def has_changes(self) -> bool:
        return any(self.count_resources().values())

    def get_changes_breakdown(self) -> str:
        changes = self.count_resources()
        breakdown = []
        for action, count in changes.items():
            if count > 0:
                breakdown.append(f"{action}={count}")
        return ', '.join(breakdown)


def init_and_plan(directory: str, terraform_cmd: str = 'terraform', display_colors: bool = False,
                  env_variables: Optional[Dict[str, str]] = None) -> Tuple[bool, TerraformPlan]:
    """
    Runs 'terraform init', 'terraform plan' and 'terraform show' in the specified directory.
    Returns a boolean indicating whether there was a difference and the JSON output of 'terraform show'.
    """
    logger = logging.getLogger(__name__)
    color_flag = [] if display_colors else ['-no-color']

    # Default environment variables
    if env_variables is None:
        env_variables = {}

    # Update environment variables
    os.environ.update(env_variables)

    try:
        # Change to the specified directory
        os.chdir(directory)

        # Run `terraform init`
        logger.info(f"Running `{terraform_cmd} init` in directory: {directory}")
        result = subprocess.run([terraform_cmd, 'init', '-input=false'] + color_flag, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"`{terraform_cmd} init` failed with output:\n{result.stderr}")
            raise ConsoleException(f"`{terraform_cmd} init` failed", str(result.stderr))

        # Run `terraform plan -out=tfplan`
        logger.info(f"Running `{terraform_cmd} plan -out=tfplan` in directory: {directory}")
        result = subprocess.run([terraform_cmd, 'plan', '-out=tfplan', '-input=false'] + color_flag, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"`{terraform_cmd} plan` failed with output:\n{result.stderr}")
            raise ConsoleException(f"'{terraform_cmd} plan' failed", str(result.stderr))

        # Run `terraform show -json tfplan`
        logger.info(f"Running `{terraform_cmd} show -json tfplan` in directory: {directory}")
        result = subprocess.run([terraform_cmd, 'show', '-json', 'tfplan'] + color_flag, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"`{terraform_cmd} show` failed with output:\n{result.stderr}")
            raise ConsoleException(f"`{terraform_cmd} show` failed", str(result.stderr))

        # Parse the JSON output
        plan = json.loads(result.stdout)
        terraform_plan = TerraformPlan(plan)

        # Check if the plan format is supported
        if terraform_plan.format_version != '1.2':
            logger.error(f"Unsupported Terraform plan format version: {plan['format_version']}")
            raise Exception(f"Unsupported Terraform plan format version: {plan['format_version']}")

        # Check if there's a difference
        difference = terraform_plan.count_resources_except_noop_and_read() > 0

        logger.info(f"Difference in `{terraform_cmd} plan`: {difference}")

        return difference, TerraformPlan(plan)

    except Exception as e:
        logger.error(f"Error running terraform commands in directory {directory}: {str(e)}")
        raise

