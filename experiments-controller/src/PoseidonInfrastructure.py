import os
import logging
from paramiko import SSHClient, AutoAddPolicy

class PoseidonInfrastructure:
    submit_node = None
    data_node =  None
    normal_router = None
    lossy_router = None
    chameleon_nodes = None
    logger = None

    def __init__(self, infra_config):
        self.logger = logging.getLogger("poseidon")
        try:
            self.submit_node = {"ip_address": infra_config["submit_node"]["ip_address"]}
            self.data_node = {"ip_address": infra_config["data_node"]["ip_address"]}
            #self.normal_router = {
            #    "ip_address_fabric": infra_config["normal_router"]["ip_address_fabric"],
            #    "ip_address_chameleon": infra_config["normal_router"]["ip_address_chameleon"],
            #}
            self.lossy_router = {
                "ip_address": infra_config["lossy_router"]["ip_address"],
                "fabric_interface": infra_config["lossy_router"]["fabric_interface"],
                "chameleon_interface": infra_config["lossy_router"]["chameleon_interface"],
                "username": infra_config["lossy_router"]["username"],
                "key_filename": infra_config["lossy_router"]["key_filename"],
                "ssh_client": None
            }
            self.chameleon_nodes = {}
            for chi_node in infra_config["chameleon_nodes"]:
                self.chameleon_nodes[chi_node] = {
                    "cores": infra_config["chameleon_nodes"][chi_node]["cores"],
                    "ram": infra_config["chameleon_nodes"][chi_node]["ram"],
                    "ip_address": infra_config["chameleon_nodes"][chi_node]["ip_address"],
                    "username": infra_config["chameleon_nodes"][chi_node]["username"],
                    "key_filename": infra_config["chameleon_nodes"][chi_node]["key_filename"],
                    "ssh_client": None
                }
        except Exception as e:
            self.logger.error(e)
            raise ValueError
    
    def update_lossy_router(self, anomaly_type):
        """
        The anomaly_type is expected to look like the following example
        example: anomaly_type=loss_0.1
        """
        try:
            fabric_interface = self.lossy_router["fabric_interface"]
            chameleon_interface = self.lossy_router["chameleon_interface"]
            
            commands = []
            commands.append(f"sudo tc qdisc del dev {fabric_interface} root")
            commands.append(f"sudo tc qdisc del dev {chameleon_interface} root")
            
            if not anomaly_type.startswith("loss"):
                self.logger.info(f"Anomaly type '{anomaly_type}' is not in supported network anomalies. Will clear router rules")
            else:
                anomaly_type_and_magnitute = anomaly_type.split("_")
            
                if anomaly_type_and_magnitute[0] == "loss":
                    magnitute = float(anomaly_type_and_magnitute[1])
                    commands.append(f"sudo tc qdisc add dev {fabric_interface} root netem loss {magnitute}%")
                    commands.append(f"sudo tc qdisc add dev {chameleon_interface} root netem loss {magnitute}%")

            self.lossy_router = self.connect_ssh_client(self.lossy_router)
            for cmd in commands:
                self.execute_command(self.lossy_router, cmd)
            self.lossy_router = self.close_ssh_client(self.lossy_router)
        except Exception as e:
            self.logger.warning(e)
            
    def connect_ssh_client_chi_node(self, chi_node):
        try:
            node_info = self.chameleon_nodes[chi_node]
            node_info = self.connect_ssh_client(node_info)
            self.chameleon_nodes[chi_node] = node_info
        except Exception as e:
            self.logger.error(e)

    def connect_ssh_client(self, node_info):
        try:
            client = SSHClient()
            client.load_system_host_keys()
            client.load_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
            client.set_missing_host_key_policy(AutoAddPolicy())
            client.connect(
                node_info["ip_address"],
                username=node_info["username"],
                key_filename=os.path.expanduser(node_info["key_filename"])
            )
            node_info["ssh_client"] = client
            return node_info
        except Exception as e:
            self.logger.error(e)
            raise ValueError
    
    def close_ssh_client_chi_node(self, chi_node):
        try:
            node_info = self.chameleon_nodes[chi_node]
            node_info = self.close_ssh_client(node_info) 
            self.chameleon_nodes[chi_node] = node_info
        except Exception as e:
            self.logger.warning(e)

    def close_ssh_client(self, node_info):
        try:
            node_info["ssh_client"].close()
            node_info["ssh_client"] = None
            return node_info
        except Exception as e:
            self.logger.warning(e)

    def execute_command_chi_node(self, chi_node, cmd):
        try:
            node_info = self.chameleon_nodes[chi_node]
            self.execute_command(node_info, cmd)
        except Exception as e:
            self.logger.warning(e)

    def execute_command(self, node_info, cmd):
        try:
            client = node_info["ssh_client"]
            stdin, stdout, stderr = client.exec_command(cmd)
            stdin.close()
            stdout.close()
            stderr.close()
        except Exception as e:
            self.logger.error(e)
            raise ValueError

    def get_submit_ip(self):
        return self.submit_node["ip_address"]

    def get_data_ip(self):
        return self.submit_node["ip_address"]

    def get_normal_router_ips(self):
        return self.normal_router

    def get_lossy_router_ips(self):
        return self.lossy_router

    def get_chameleon_nodes(self):
        return self.chameleon_nodes

