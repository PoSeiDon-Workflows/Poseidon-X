import logging
import random
import subprocess
import json
from time import sleep

class DockerParams:
    condor_host = None
    chameleon_route = None
    num_cpus = None
    pool_pass = "p0s31d0n"
    network_limit = None
    volume_details = "/home/poseidon/volume/:/home/poseidon/volume/"
    hostname = None
    cpuset_cpus = None
    cpus = None
    device_read = None
    device_write = None
    memory = None
    network = "poseidon_net"
    name = None
    image = "papajim/poseidon-execute:ubuntu20"
    logger = None
    container_type = "normal"

    def __init__(self, condor_host, hostname, container_type, num_cpus, cpuset_cpus, memory, network_limit):
        self.logger = logging.getLogger("poseidon")
        self.condor_host = condor_host
        self.name = hostname
        self.hostname = hostname
        self.container_type = container_type
        self.num_cpus = num_cpus
        self.network_limit = network_limit
        self.memory = memory
        self.cpus = num_cpus
        self.cpuset_cpus = cpuset_cpus

    def reduce_actual_cpus_by_k(self, k):
        if (self.cpuset_cpus[1]-k) < self.cpuset_cpus[0]:
            self.logger.error("K cannot be larger than condor cores")
            raise ValueError

        self.cpuset_cpus[1] = self.cpuset_cpus[1] - k
        self.cpus = self.cpus - k

    def set_device_read(self, device_read):
        self.device_read = device_read

    def set_device_write(self, device_write):
        self.device_write = device_write

    def set_device_network(self, device_network):
        self.network = device_network

    def set_container_type(self, container_type):
        self.container_type = container_type

    def set_chameleon_route(self, route):
        return
    
    def get_docker_run_cmd(self):
        docker_run_cmd = [
            "docker", 
            "run",
            "--rm",
            "--detach",
            "--cap-add=NET_ADMIN",
            "--privileged",
            f"-e CONDOR_HOST={self.condor_host}", 
            f"-e NUM_CPUS={self.num_cpus}",
            f"-e MEMORY={self.memory * 1024}",
            f"-e POOL_PASSWORD={self.pool_pass}",
            f"-e NETWORK_LIMIT={self.network_limit}",
            f"-e MACHINE_SPECIAL_ID={self.container_type}",
            f"-v {self.volume_details}",
            f"-h {self.hostname}",
            f"--name {self.hostname}",
            f"--net {self.network}",
            f"--cpuset-cpus={self.cpuset_cpus[0]}-{self.cpuset_cpus[1]}",
            f"--cpus={self.cpus}",
            f"--memory={self.memory}gb"
        ]

        if self.device_read:
            docker_run_cmd.append(f"--device-read-bps /dev/sda:{self.device_read}mb")
        
        if self.device_write:
            docker_run_cmd.append(f"--device-write-bps /dev/sda:{self.device_write}mb")

        docker_run_cmd.append(f"{self.image}")
        return " ".join(docker_run_cmd)


class PoseidonWorkerContainer:
    supported_types = [
        "normal", "cpu_2", "cpu_3", "cpu_4", "cpu_5", 
        "cpu_6", "cpu_7", "cpu_8", "cpu_9", "cpu_10",
        "hdd_1", "hdd_2", "hdd_5", "hdd_10",
        "loss_0.01", "loss_0.1", "loss_0.5"
    ]
    name = None
    cpuset = None
    container_type = None
    chameleon_node = None
    docker_params = None
    type_changed = False

    def __init__(self, name, cpuset, container_type, chameleon_node, submit_node, condor_config):
        if not container_type in self.supported_types:
            self.logger.warning(f"Container type '{container_type}' is not in supported types")
            raise ValueError

        self.name = name
        self.cpuset = cpuset
        self.container_type = container_type
        self.chameleon_node = chameleon_node
        self.docker_params = DockerParams(submit_node["ip_address"], self.name, self.container_type, condor_config["cores"], self.cpuset, condor_config["ram"], condor_config["network_limit"])

    def update_container_type(self, container_type):
        if self.type_changed:
            self.logger.warning(f"Container type cannot be changed more than once")
            return
        else:
            self.type_changed = True

        if not container_type in self.supported_types:
            self.logger.warning(f"Container type '{container_type}' is not in supported types")
            raise ValueError
        
        self.container_type = container_type
        self.update_docker_params()

    def update_docker_params(self):
        self.docker_params.set_container_type(self.container_type)
        if self.container_type.startswith("cpu"):
            k = int(self.container_type.split('_')[1])
            self.docker_params.reduce_actual_cpus_by_k(k)
        elif self.container_type.startswith("hdd"):
            write_speed = int(self.container_type.split('_')[1])
            read_speed = 2 * write_speed
            self.docker_params.set_device_read(read_speed)
            self.docker_params.set_device_write(write_speed)
        elif self.container_type.startswith("loss"):
            self.docker_params.set_device_network("poseidon_net_anomalous")
            
    def get_docker_run_cmd(self):
        return self.docker_params.get_docker_run_cmd()

class PoseidonCondorPool:
    infrastructure = None
    workers = None
    logger = None
    
    def __init__(self, infrastructure, condor_config, experiment_type="normal", number_of_anomaly_workers=0):
        self.logger = logging.getLogger("poseidon")
        self.workers = []
        self.infrastructure = infrastructure

        submit_node = self.infrastructure.submit_node
        chameleon_nodes = self.infrastructure.chameleon_nodes

        for chi_node in chameleon_nodes:
            available_cores = chameleon_nodes[chi_node]["cores"]
            available_ram = chameleon_nodes[chi_node]["ram"]
            condor_cores = condor_config["cores"]
            condor_ram = condor_config["ram"]
            total_containers = min(int(available_cores/condor_cores), int(available_ram/condor_ram))

            #self.logger.info(f"{total_containers} container(s) will be spawned on {chi_node} chameleon node")

            for i in range(0, total_containers*condor_cores, condor_cores):
                cpu_i = i
                cpu_j = i+condor_cores-1
                self.workers.append(PoseidonWorkerContainer(f"{chi_node}-container-{cpu_i}-{cpu_j}", [cpu_i, cpu_j], "normal", chi_node, submit_node, condor_config))

        if experiment_type != "normal":
            try:
                for worker in random.sample(self.workers, k=number_of_anomaly_workers):
                    worker.update_container_type(experiment_type)
            except Exception as e:
                raise

    def clear_docker_containers(self):
        chameleon_nodes = self.infrastructure.chameleon_nodes
        cmd = "docker kill $(docker ps -q)"
        for chi_node in chameleon_nodes:
            try:
                self.infrastructure.connect_ssh_client_chi_node(chi_node)
                self.infrastructure.execute_command_chi_node(chi_node, cmd)
                self.infrastructure.close_ssh_client_chi_node(chi_node)
            except Exception as e:
                raise


    def get_workers_with_anomaly(self):
        workers_with_anomaly = []
        for worker in self.workers:
            if worker.container_type != "normal":
                workers_with_anomaly.append(worker)
        return workers_with_anomaly

    def deploy_containers(self):
        chameleon_nodes = self.infrastructure.chameleon_nodes
        for chi_node in chameleon_nodes:
            try:
                self.infrastructure.connect_ssh_client_chi_node(chi_node)
                sleep(2)
            except Exception as e:
                self.logger.error(e)
                raise

        for worker in self.workers:
            try:
                cmd = worker.get_docker_run_cmd()
                self.infrastructure.execute_command_chi_node(worker.chameleon_node, cmd)
                sleep(2)
            except Exception as e:
                self.logger.error(e)
                raise
        
        for chi_node in chameleon_nodes:
            try:
                self.infrastructure.close_ssh_client_chi_node(chi_node)
            except Exception as e:
                self.logger.warning(e)

    def wait_for_containers(self):
        cmd = ["condor_status", "-json"]
        timeout = 120
        all_stable = False
        wait_time = 0

        try:
            while (not all_stable) and (wait_time < timeout):
                self.logger.info("Waiting for condorpool to become stable")
                sleep(20)
                wait_time += 20
                res = subprocess.run(cmd, capture_output=True)
                condor_status_out = json.loads(res.stdout)
                all_stable = True
                for worker in self.workers:
                    found = False
                    for slot in condor_status_out:
                        if worker.name == slot["UtsnameNodename"]:
                            found = True
                            if slot["Activity"] != "Idle":
                                all_stable = False
                    if not found:
                        all_stable = False
                        break
                    elif all_stable == False:
                        break
        except Exception as e:
            self.logger.warning(e)
