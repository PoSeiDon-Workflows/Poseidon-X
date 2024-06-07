import logging
import json
import os
import subprocess
from PoseidonInfrastructure import PoseidonInfrastructure
from PoseidonCondorPool import PoseidonCondorPool
from time import time, sleep

class Experiment:
    start_time = None
    end_time = None
    workflow = None
    workflow_dir = None
    workflow_script = None
    infrastructure = None
    condor_pool = None
    experiment_type = None
    number_of_anomaly_workers = None
    logger = None

    def __init__(self, workflow_list, infrastructure, experiment_config):
        self.logger = logging.getLogger("poseidon")
        if not experiment_config["workflow"] in workflow_list:
            self.logger.warning(f"Workflow '{experiment_config['workflow']}' is not in workflow list. Skipping...")
            raise ValueError
        
        self.infrastructure = infrastructure
        self.workflow = experiment_config["workflow"]
        self.workflow_dir = workflow_list[self.workflow]["dir"]
        self.workflow_script = workflow_list[self.workflow]["script"]
        self.experiment_type = experiment_config["type"]
        self.number_of_anomaly_workers = experiment_config["number_of_anomaly_workers"]

        try:
            self.condor_pool = PoseidonCondorPool(self.infrastructure, experiment_config["condor_config"], self.experiment_type, self.number_of_anomaly_workers)
        except Exception as e:
            raise
    
    def __str__(self):
        workers_with_anomaly = self.condor_pool.get_workers_with_anomaly()
        workers_with_anomaly_name = [w.name for w in workers_with_anomaly]

        obj = {
            "workflow": self.workflow,
            "experiment_type": self.experiment_type,
            "number_of_anomaly_workers": self.number_of_anomaly_workers,
            "workers_with_anomaly": workers_with_anomaly_name
        }
        return json.dumps(obj)

    def prepare_condorpool(self):
        self.condor_pool.clear_docker_containers()
        self.condor_pool.deploy_containers()
        self.condor_pool.wait_for_containers()

    def execute_workflow(self):
        self.logger.info("Starting the workflow...")
        try:
            res = subprocess.run(self.workflow_script, shell=True, cwd=self.workflow_dir, capture_output=True)
        except Exception as e:
            self.logger.error(e)
            raise
    
    def wait_for_workflow(self):
        return

    def run(self):
        self.start_time = int(time())
        self.infrastructure.update_lossy_router(self.experiment_type)
        self.prepare_condorpool()
        self.execute_workflow()
        self.end_time = int(time())
        

class PoseidonExperiments:
    workflow_list = None
    infrastructure = None
    experiment_list = None
    start_time = None
    end_time = None
    log_filename = None
    logger = None
    
    def __init__(self, workflow_list, experiments_config, log_filename):
        self.logger = logging.getLogger("poseidon")
        self.workflow_list = workflow_list
        self.log_filename = log_filename
        
        if not os.path.isfile(self.log_filename):
            with open(self.log_filename, "w+") as g:
                g.write("start_time,end_time,workflow,experiment_type,workers_with_anomaly\n")

        self.logger.info("Loading infrastructure setup")
        self.infrastructure = PoseidonInfrastructure(experiments_config["infrastructure"])

        self.logger.info("Loading experiments")
        self.create_experiments(experiments_config["experiments"])

    def create_experiments(self, experiments):
        self.experiment_list = []
        for j in range(len(experiments)):
            self.logger.info(f"Loading experiments configuration {j+1}")
            
            entry = experiments[j]
            self.logger.info(f"Workflow: {entry['workflow']} | Type: {entry['type']} | Runs: {entry['number_of_runs']} | Number of Anomaly Workers: {','.join(map(str, entry['number_of_anomaly_workers']))}")

            condor_config = {
                "cores": int(entry["condor_config"]["cores"]),
		"ram": int(entry["condor_config"]["ram"]),
		"network_limit": int(entry["condor_config"]["network_limit"])
            }

            tmp_exp_list = []
            try:
                if entry["number_of_anomaly_workers"]:
                    for k in entry["number_of_anomaly_workers"]:
                        for i in range(entry["number_of_runs"]):
                            exp_config = {
                                "workflow": entry["workflow"],
                                "type": entry["type"],
                                "number_of_anomaly_workers": int(k),
                                "condor_config": condor_config
                            }

                            exp = Experiment(self.workflow_list, self.infrastructure, exp_config)
                            tmp_exp_list.append(exp)
                else:
                    for i in range(entry["number_of_runs"]):
                        exp_config = {
                            "workflow": entry["workflow"],
                            "type": entry["type"],
                            "number_of_anomaly_workers": 0,
                            "condor_config": condor_config
                        }
                        
                        exp = Experiment(self.workflow_list, self.infrastructure, exp_config)
                        tmp_exp_list.append(exp)
            except Exception as e:
                self.logger.warning(f"Experiment was not added to list of experiments")
                continue

            for exp in tmp_exp_list:
                self.experiment_list.append(exp)
        self.logger.info(f"Total number of loaded experiments is {len(self.experiment_list)}")
        sleep(2)

    def print_experiment_list(self):
        for exp in self.experiment_list:
            print(exp)
    
    def run(self):
        self.start_time = int(time())
        for j in range(len(self.experiment_list)):
            exp = self.experiment_list[j]
            self.logger.info(f"Starting experiment {j+1}")
            
            exp.run() #this is blocking for now
            
            workers_with_anomaly = exp.condor_pool.get_workers_with_anomaly()
            workers_with_anomaly_name = [w.name for w in workers_with_anomaly]
        
            log_line = f"{exp.start_time},{exp.end_time},{exp.workflow},{exp.experiment_type},{' '.join(workers_with_anomaly_name)}\n"
            with open(self.log_filename, "a+") as g:
                g.write(log_line)

            self.logger.info(f"Finished experiment {j+1}")
        self.end_time = int(time())

