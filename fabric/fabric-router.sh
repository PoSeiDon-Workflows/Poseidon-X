#!/usr/bin/env bash

# this script should run as root and has been tested with ubuntu 20.04

#sed -i 's/nameserver/nameserver 2a01:4f9:c010:3f02::1\nnameserver 2a00:1098:2c::1\nnameserver 2a00:1098:2b::1\nnameserver/' /etc/resolv.conf

apt-get update && apt-get -y upgrade
apt-get install -y linux-headers-$(uname -r)
apt-get install -y build-essential make zlib1g-dev librrd-dev libpcap-dev autoconf automake libarchive-dev iperf3 htop bmon vim wget pkg-config git python-dev python3-pip libtool libpcap-dev openvswitch-switch-dpdk
pip install --upgrade pip

######################
### EDIT /etc/hosts ##
######################

#cat << EOF >> /etc/hosts
#EOF

############################
####     TCP TUNING     ####
############################

cat >> /etc/sysctl.conf <<EOL
# enable forwarding
net.ipv4.ip_forward=1
# recommended for hosts with jumbo frames enabled
net.ipv4.tcp_mtu_probing=1
# recommended to enable 'fair queueing'
net.core.default_qdisc = fq
EOL

sysctl --system

#############################################################################
### SETUP poseidon USER with a key that can be used from the submit node ####
#############################################################################
cd
useradd -s /bin/bash -d /home/poseidon -m poseidon

echo "poseidon     ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

mkdir /home/poseidon/.ssh
chmod -R 700 /home/poseidon/.ssh

echo "ssh-rsa ...." >> /home/poseidon/.ssh/authorized_keys

chmod 600 /home/poseidon/.ssh/authorized_keys
chown -R poseidon:poseidon /home/poseidon/.ssh
