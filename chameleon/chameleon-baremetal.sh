#!/usr/bin/env bash

######################
### EDIT /etc/hosts ##
######################

echo "192.168.104.100 poseidon-submit" | sudo tee -a /etc/hosts
echo "192.168.104.200 poseidon-data" | sudo tee -a /etc/hosts


######################
### ADD KEYS        ##
######################

sudo mkdir /home/poseidon/.ssh
sudo chmod -R 700 /home/poseidon/.ssh
echo "ssh-rsa ....." | sudo tee -a /home/poseidon/.ssh/authorized_keys
sudo chown -R poseidon:poseidon /home/poseidon/.ssh

