import gc
import logging
import os
import shutil
import tempfile
from urllib.parse import urlparse
from git import Repo, Git
from git.exc import GitCommandError


def shallow_clone_repo(git_url, target_dir=None, branch='main',
                       http_username=None, http_password=None, ssh_private_key_path=None) -> str:
    """
    Clone a git repository with the given URL to the target directory.
    Supports HTTP with username/password and SSH with private key.
    Performs a shallow clone with a depth of 1.
    """
    logger = logging.getLogger(__name__)

    # Parse repo name for use in subfolder cloning
    path = urlparse(git_url).path
    repo_name = os.path.basename(path).replace('.git', '')

    # Create a temporary directory if target_dir is not provided
    if target_dir is None:
        target_dir = tempfile.mkdtemp()

    # Append the repo name to the target directory
    target_dir = os.path.join(target_dir, repo_name)

    logger.debug(f"Will attempt to clone {git_url} into {target_dir}")

    # Now create folder `target_dir` if it doesn't exist
    # if not os.path.exists(target_dir):
    #     # this will also create all intermediate-level directories as required
    #     logger.debug(f"Creating fresh and empty directory: {target_dir}")
    #     os.makedirs(target_dir, exist_ok=True)

    try:
        if git_url.startswith("http") and http_username and http_password:
            # for http(s) repositories, use basic auth
            g = Git(target_dir)
            logger.info(f"Cloning http(s) repository {git_url} into {target_dir}")
            repo = g.clone('--depth', '1', '--branch', branch, '--config',
                           f'http.{git_url}.extraheader="AUTHORIZATION: Basic $(echo -n "{http_username}:{http_password}" | openssl base64 -A)"', git_url)

            logger.debug(f"Successfully cloned {git_url} into {target_dir}")

        elif git_url.startswith("git") and ssh_private_key_path:
            # for ssh repositories, use ssh private key
            logger.info(f"Cloning ssh repository {git_url} into {target_dir}")
            os.environ['GIT_SSH_COMMAND'] = f'ssh -i {ssh_private_key_path}'
            Repo.clone_from(git_url, target_dir, branch=branch, depth=1)

        else:
            # try cloning without credentials
            logger.info(f"Cloning repository {git_url} without inline credentials into {target_dir}")
            # @todo add support for environment variables being passed to the git command.
            Repo.clone_from(git_url, target_dir, branch=branch, depth=1)

        logger.info(f"Successfully cloned {git_url} into {target_dir}")

        # Return the path of the cloned repository
        return target_dir

    except GitCommandError as e:
        logger.error(f"Failed to clone {git_url}. Reason: {str(e)}")
        raise
