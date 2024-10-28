# Poseidon-X (Poseidon Experimental Platform)

This project contains information on how to setup and start experiments using Poseidon's Experimental Platform.
These experiments can be used to collect traces for anomaly analysis using GNNs, LLMs, Active Learning methods, as we have presented in our publications.

for Poseido nand collect data for the analysis with GNNs and other techniques.
The project uses chameleon nodes to execute workflow runs under various conditions and the resources are getting split into finer grained parts using Docker.

## Scripts and files

_chameleon/*_: These scripts are to be executed on the baremetal nodes on Chameleon cloud.

_chameleon/chameleon-baremetal.sh_: This script assumes we are starting from a snapshotted imaged and introduces the passwordless ssh-key for communication between the cluster nodes.

_chameleon/chameleon-worker-from-scratch.sh_: This script installs all the packages required on the worker nodes.

_chameleon/chameleon-worker-gpu-from-scratch.sh_: This script installs all the packages required on the worker nodes, and adds Nvidia Cuda support.

_chameleon/Docker/Execute/*_: These Docker recipes can be used to build Poseidon's Executor Docker container.

_farbric/fabric-submit.sh: This script prepares a submit node that runs on a Fabric VM instance.

_farbric/fabric-data.sh: This script prepares a data node with HTTP that runs on a Fabric VM instance.

_farbric/fabric-router.sh: This script prepares a router node that runs on a Fabric VM instance.

_experiments-controllerl/*_: This folder contains the source code and the config files of Poseidon's Experiment Controller.

_poseidon-chameleon-fabric-setup.ipynb_: This Jupyter Nodebook contains step by step instruction of how to recreate Poseidon X.

Creating An SSH Key
--------------------
To allow the nodes to communicate with each other during the workflow experiments you need to create a passwordless ssh-key

```
ssh-keygen -t rsa -b 4096 -f cluster_key
```

Update the following line in all bash scripts under ```chmeleon/``` and ```fabric/``` with the public key you just created.

```
echo "ssh-rsa ...." >> /home/poseidon/.ssh/authorized_keys
```

Deploying Poseidon-X
--------------------
- Follow the instructions inside the  ```poseidon-chameleon-fabric-setup.ipynb ```
- After creating the submit node install the private cluster key under  ```/home/poseidon/.ssh/ ```
- Copy the ```experiments-controller``` folder into the submit node under ```/home/poseidon/```

Running The Experiments
---------------------------
- ```cd /home/poseidon/experiments-controller```
- Edit config/experiments-config.json
    - Specify ip address for current deployment. (check chameleon submit node ip address to find this)
    - Edit/add all workers ip addresses. (check chameleon worker node ip address to find this)
- Edit config/workflows.json
    - Specify the workflows you have installed and configured in the cluster to run with Poseidon
    - You can find preconfigured workflows and their configs here: https://github.com/PoSeiDon-Workflows/FlowBench-Raw-Workflow-Data
- Invoke experiments controller :
    - (Uses screen) ```screen -S experiments```
    - Run ```./experiments-controller.py```
    - Exit the screen.

- When workflow starts running, ```watch pegasus-status``` to check the progress.

- Generate statistics for a particular workflow once the workflow finishes :
    - Enter the screen ```screen -S experiments```
    - Run ```./experiments-controller.py -s```
