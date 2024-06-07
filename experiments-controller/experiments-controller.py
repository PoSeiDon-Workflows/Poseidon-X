#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, f"{os.path.dirname(os.path.abspath(__file__))}/src")

import logging
from argparse import ArgumentParser
from PoseidonExperiments import PoseidonExperiments
from PoseidonStatistics import PoseidonStatistics
from PoseidonHelpers import *

def main():
    workflow_list = None
    experiment_config = None

    logging.basicConfig()
    logger = logging.getLogger("poseidon")
    logger.setLevel(logging.INFO)
    
    parser = ArgumentParser(description="Poseidon Experiments Controler")
    parser.add_argument("-w", "--workflows", metavar="STR", type=str, default="config/workflows.json", help="JSON File With List of Supported Workflows. (Default: config/workflows.json)", required=False)
    parser.add_argument("-c", "--config", metavar="STR", type=str, default="config/experiments-config.json", help="JSON File With Experiment Configuration. (Default: config/experiments-config.json)", required=False)
    parser.add_argument("-l", "--log", metavar="STR", type=str, default="logs/experiments.log", help="Experiments Log File (Default: logs/experiments.log)", required=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False, help="Set logging level to DEBUG. (Default: INFO)", required=False)
    parser.add_argument("-s", "--statistics_only", action="store_true", default=False, help="Generate Statistics Only. This argument will prevent any experiment run. (Default: False)", required=False)


    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    if args.statistics_only:
        statistics = PoseidonStatistics(args.log, args.workflows)
        statistics.generate()
    else:
        workflow_list = load_workflow_list(args.workflows)
        experiments_config = load_experiments_config(args.config) 

        poseidon_experiments = PoseidonExperiments(workflow_list, experiments_config, args.log)
        poseidon_experiments.run()

if __name__ == "__main__":
    main()
