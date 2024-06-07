import logging
import json
import pandas as pd

def load_workflow_list(json_file):
    logger = logging.getLogger("poseidon")
    logger.info("Loading supported workflows list")
    try:
        with open(json_file, 'r') as f:
            workflow_list = json.load(f)
            return workflow_list
    except Exception as e:
        logger.error(e)
        exit(1)


def load_experiments_config(json_file):
    logger = logging.getLogger("poseidon")
    logger.info("Loading experiments config")
    try:
        with open(json_file, 'r') as f:
            experiments_config = json.load(f)
            return experiments_config
    except Exception as e:
        logger.error(e)
        exit(1)


def load_experiments_log(log_file):
    logger = logging.getLogger("poseidon")
    logger.info("Loading experiments log")
    try:
        experiments_log = pd.read_csv(log_file)
        return experiments_log
    except Exception as e:
        logger.error(e)
        exit(1)


def load_experiments_log_cache(experiments_cache):
    logger = logging.getLogger("poseidon")
    logger.info("Loading experiments log cache")
    try:
        experiments_log = []
    except Exception as e:
        logger.error(e)
        exit(1)
