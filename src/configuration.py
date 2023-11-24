import yaml
from dataclasses import dataclass
from typing import Dict, List, Optional
from apscheduler.job import Job


@dataclass
class ServerConfig:
    host: str
    port: int
    domain: str

@dataclass
class GitConfig:
    repo_url: str
    branch: str
    ssh_key: str


@dataclass
class NotificationConfig:
    slack: Optional[Dict[str, str]] = None
    pagerduty: Optional[Dict[str, str]] = None


@dataclass
class Deployment:
    name: str
    tags: Dict[str, str]
    git: GitConfig
    source_root: str
    env_vars: Dict[str, str]
    enabled: bool
    drift_check_interval: int
    notifications: List[str]
    active_apscheduler_job: Optional[Job] = None


@dataclass
class AppConfig:
    infrastructure_deployments: List[Deployment]
    notification_methods: NotificationConfig
    secrets: Dict[str, str]
    server: ServerConfig


def load_config(file_path: str) -> AppConfig:
    with open(file_path, 'r') as file:
        config_dict = yaml.safe_load(file)

    infrastructure_deployments = []
    for deployment in config_dict.get('infrastructure_deployments', []):
        infrastructure_deployments.append(Deployment(**deployment))

    notification_methods = NotificationConfig(**config_dict.get('notification_methods', {}))

    secrets = config_dict.get('secrets', {})

    server = ServerConfig(**config_dict.get('server', {}))

    return AppConfig(
        infrastructure_deployments=infrastructure_deployments,
        notification_methods=notification_methods,
        secrets=secrets,
        server=server,
    )
