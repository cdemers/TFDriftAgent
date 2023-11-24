# _TFDriftAgent_

## Overview

_TFDriftAgent_ is a Python-based application designed to monitor and report 
drift in _Terraform_ deployments. It utilizes _Terraform_ for infrastructure 
management and _git_ for version control, integrating with Prometheus for 
metrics reporting. The app dynamically schedules drift checks at specified 
intervals and reports on any discrepancies between the intended state (as 
defined in the _Terraform_ code) and the actual state of the infrastructure.

## Features

- Drift Detection: Automatically detects drift in _Terraform_ deployments.
- Git Integration: Clones and checks repositories for the latest _Terraform_ states.
- _Terraform_ Integration: Uses _Terraform_ to compare the actual state with the expected state.
- Metrics Reporting: Integrates with _Prometheus_ to report drift metrics.
- Configurable Scheduling: Allows scheduling of drift checks at configurable intervals.
- Logging and Error Handling: Robust logging and error handling for troubleshooting.

## Prerequisites

- _Python_ 3.x
- _Terraform_
- _git_
- _Prometheus_, or any other metrics reporting tool capable of using the _Prometheus_ scrape point format, for example _Datadog_.

## Installation

- Clone the repository: `git clone git@github.com:cdemers/TFDriftAgent.git`
- Navigate to the cloned directory: `cd TFDriftAgent/src`
- Install dependencies: `pip install -r requirements.txt` (You might want to use a virtual environment)

## Configuration

- Create a `config.yaml` file in the src root directory, or set the `APP_CONFIG` environment variable to the path of the configuration file.
- Specify the infrastructure deployments, Git repository details, scheduling intervals, and Prometheus configuration.
- Example:

```yaml
infrastructure_deployments:
  - name: "example_deployment"
    enabled: true
    git:
      repo_url: "https://example.com/repo.git"
      branch: "main"
      ssh_key: "/path/to/ssh/key"
    drift_check_interval: 30 # in minutes
    ...
server:
  host: "localhost"
  port: 5000
```

## Usage

- Run the application: `python agent.py`
- Use command-line arguments to specify the config file and log level:
  - -c, --config (env. var APP_CONFIG) to specify the configuration file path. Defaults to `config.yaml` in the src root directory.
  - -l, --loglevel (env. var APP_LOGLEVEL) to set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

## API

- The application hosts a RESTful API for real-time monitoring and control.
- Access the API at http://[host]:[port] as defined in the configuration.

## Prometheus Integration

- The app exposes various metrics for _Prometheus_ scraping.
- Metrics include drift detected changes, successful/error drift checks, and check durations.

## Logging

The application logs important events and errors, aiding in troubleshooting and monitoring.

## Contributing

Contributions to improve _TFDriftAgent_ are welcome. Please follow the standard _git_ workflow for contributions.

## Pending Features

These features are planned for future releases:

- [ ] Support authentication for the _Prometheus_ scrape point.
- [ ] Logs sanitization for sensitive data.
- [ ] Complete exception handling.
- [ ] Complete signal handling.
- [ ] Remove the _GitPython_ workaround once the issue is resolved upstream.
- [ ] Add minimal unit and integration tests.

## License

This project is licensed under the [MIT License](https://opensource.org/license/mit/). See the LICENSE file in the project root for more information.

