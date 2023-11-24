import os
import logging
import argparse
import shutil
import signal
import sys
import time
import traceback

import yaml

import restful_api
import app_state
from src.tools.scrubber import SensitiveDataFilter
from tools import git, terraform, colors
from configuration import load_config, AppConfig, Deployment
from apscheduler.schedulers.background import BackgroundScheduler
from prometheus_client import Gauge


def signal_handler(sig, frame):
    print("Signal received, shutting down...")
    scheduler.shutdown()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

scheduler = BackgroundScheduler()
state = app_state.ApplicationState()

state.set_gauge("drift_monitor_agent_drift_detected_changes", Gauge('drift_monitor_agent_drift_detected_changes',
                                                                    'Number of drift detected changes',
                                                                    labelnames=['name']))
state.set_gauge("drift_monitor_agent_drift_check_success", Gauge('drift_monitor_agent_drift_check_success',
                                                                 'Number of successful drift checks',
                                                                 labelnames=['name']))
state.set_gauge("drift_monitor_agent_drift_check_error", Gauge('drift_monitor_agent_drift_check_error',
                                                               'Number of error drift checks',
                                                               labelnames=['name']))
state.set_gauge("drift_monitor_agent_drift_check_duration", Gauge('drift_monitor_agent_drift_check_duration',
                                                                  'Duration of drift checks',
                                                                  labelnames=['name', 'phase']))


def load_jobs(config: AppConfig):
    deployments = config.infrastructure_deployments

    # Clear all existing jobs
    scheduler.remove_all_jobs()

    # Add new jobs
    for deployment in deployments:
        logging.info(f"Adding job for deployment \"{deployment.name}\"")
        deployment.active_apscheduler_job = scheduler.add_job(infrastructure_deployment_drift_check,
                                                              'interval', minutes=deployment.drift_check_interval,
                                                              args=[deployment, state], id=deployment.name)


def reload_config(args: argparse.Namespace) -> AppConfig | None:
    logger = logging.getLogger(__name__)

    # Load the configuration file
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        logger.critical(f"Configuration file {args.config} not found.")
        exit(1)
    except yaml.YAMLError as e:
        logger.critical(f"Error parsing configuration file: {e}")
        exit(1)

    return config


def reload_deployments(args: argparse.Namespace):
    deployments = reload_config(args)  # Reload deployments from config
    load_jobs(deployments)


debug__previous_directory = None


def infrastructure_deployment_drift_check(deployment: Deployment, state: app_state.ApplicationState):
    global_start_time: float
    local_start_time: float

    logger = logging.getLogger(__name__)

    if not deployment.enabled:
        logger.info(f"Skipping deployment \"{deployment.name}\" because it is disabled")
        return

    global_start_time = time.time()

    local_start_time = time.time()
    try:
        logger.info(f"Processing deployment \"{deployment.name}\"")
        directory = git.shallow_clone_repo(deployment.git['repo_url'], branch=deployment.git['branch'],
                                           ssh_private_key_path=deployment.git['ssh_key'])
    except Exception as e:
        state.set_deployment_state(deployment.name, state=app_state.DeploymentState(deployment.name, success=False))

        state.get_gauge("drift_monitor_agent_drift_check_success").labels(deployment.name).set(0)
        state.get_gauge("drift_monitor_agent_drift_check_error").labels(deployment.name).set(1)
        state.get_gauge("drift_monitor_agent_drift_check_duration").labels(deployment.name, "git_clone").set(
            time.time() - local_start_time)

        logging.error(f"Error cloning repository {deployment.git['repo_url']}: {e}")
        traceback.print_exception(e)
        return

    state.get_gauge("drift_monitor_agent_drift_check_duration").labels(deployment.name, "git_clone").set(
        time.time() - local_start_time)

    local_start_time = time.time()
    try:
        target_dir = os.path.join(directory, deployment.source_root)

        is_different, plan = terraform.init_and_plan(target_dir, env_variables=deployment.env_vars,
                                                     display_colors=True)

        deployment_state = app_state.DeploymentState(deployment.name, is_different, plan=plan)
        state.set_deployment_state(deployment.name, state=deployment_state)

        logging.debug(f"Deployment plan drift resources count for \"{deployment.name}\": {plan.count_resources_except_noop_and_read()}")
        state.get_gauge("drift_monitor_agent_drift_detected_changes").labels(deployment.name).set(plan.count_resources_except_noop_and_read())
        state.get_gauge("drift_monitor_agent_drift_check_success").labels(deployment.name).set(1)
        state.get_gauge("drift_monitor_agent_drift_check_error").labels(deployment.name).set(0)
        state.get_gauge("drift_monitor_agent_drift_check_duration").labels(deployment.name, "total").set(
            time.time() - global_start_time)

        if is_different:
            logger.warning("The plan shows differences between what is defined in the Terraform code and actual infrastructure.")
            logger.warning(f"Breakdown by types of the changes that would be applied: {plan.get_changes_breakdown()}")

    except terraform.ConsoleException as e:
        state.set_deployment_state(deployment.name, state=app_state.DeploymentState(deployment.name, success=False))
        state.get_gauge("drift_monitor_agent_drift_check_success").labels(deployment.name).set(0)
        state.get_gauge("drift_monitor_agent_drift_check_error").labels(deployment.name).set(1)
        state.get_gauge("drift_monitor_agent_drift_check_duration").labels(deployment.name, "total").set(
            time.time() - global_start_time)
        logging.error(e)
        print(colors.ansi_to_html(str(e)))
        return

    except Exception as e:
        state.set_deployment_state(deployment.name, state=app_state.DeploymentState(deployment.name, success=False))
        state.get_gauge("drift_monitor_agent_drift_check_success").labels(deployment.name).set(0)
        state.get_gauge("drift_monitor_agent_drift_check_error").labels(deployment.name).set(1)
        state.get_gauge("drift_monitor_agent_drift_check_duration").labels(deployment.name, "total").set(
            time.time() - global_start_time)
        logging.error(e)
        return

    finally:
        # # Delete the temporary directory with a twist
        #
        # There is a bug with the GitPython library that makes it so that if you delete the directory that was operated
        # on last usign the library, a git clone for example, if once you are finished with this repository clone you
        # erase it (which you will likely need to do to), then when you try to use the library to clone another
        # repository (or the same), it will fail with an error `[Errno 2] No such file or directory`.
        # The only workaround I found was to delete the previous repository only once you have cloned a new one. As
        # such, we have to keep track of the previous directory and delete it on the next pass.
        try:
            if deployment_state.bug_workaround_previous_folder is not None:
                logger.info(f"Deleting temporary directory: {deployment_state.bug_workaround_previous_folder}")
                shutil.rmtree(deployment_state.bug_workaround_previous_folder)
            deployment_state.bug_workaround_previous_folder = directory
        except NameError:
            pass

    state.get_gauge("drift_monitor_agent_drift_check_duration").labels(deployment.name, "terraform_plan").set(
        time.time() - local_start_time)

    state.get_gauge("drift_monitor_agent_drift_check_duration").labels(deployment.name, "total").set(
        time.time() - global_start_time)


def main():
    parser = argparse.ArgumentParser(description="TFDriftAgent")
    parser.add_argument('-c', '--config',
                        type=str,
                        default=os.environ.get('APP_CONFIG', 'config.yaml'),
                        help='Path to the configuration file')
    parser.add_argument('-l', '--loglevel',
                        type=str,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default=os.environ.get('APP_LOGLEVEL', 'INFO'),
                        help='Set the logging level')

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=args.loglevel)
    logger = logging.getLogger(__name__)
    logger.addFilter(SensitiveDataFilter())
    logger.debug(f"Logging level set to {args.loglevel}")
    logger.info("Starting TFDriftAgent")

    # Load the configuration file
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        logger.critical(f"Configuration file {args.config} not found.")
        return
    except yaml.YAMLError as e:
        logger.critical(f"Error parsing configuration file: {e}")
        return

    try:
        load_jobs(config)
        scheduler.start()

        api = restful_api.API(state)
        api.run(host=config.server.host, port=config.server.port)

    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Keyboard interrupt received, exiting...")
        return


if __name__ == "__main__":
    main()
