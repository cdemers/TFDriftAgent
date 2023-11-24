import logging
import os
import glob
import shutil


def empty_directory(path: str) -> None:
    # Empty a directory without erasing the directory itself.
    logger = logging.getLogger(__name__)
    logger.debug(f"Emptying directory \"{path}\"")

    files = glob.glob(os.path.join(path, '*'))
    hidden_files = glob.glob(os.path.join(path, '.*'))

    for file in files + hidden_files:
        if os.path.isfile(file):
            logger.debug(f"Deleting file \"{file}\"")
            os.remove(file)
        elif os.path.isdir(file):
            logger.debug(f"Deleting directory \"{file}\"")
            shutil.rmtree(file)
