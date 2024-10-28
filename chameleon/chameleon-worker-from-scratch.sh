#!/bin/bash

# this script should run as root and has been tested with ubuntu 20.04

apt-get update && apt-get -y upgrade
apt-get install -y linux-headers-$(uname -r)
apt-get install -y build-essential make zlib1g-dev librrd-dev libpcap-dev autoconf automake libarchive-dev iperf3 htop bmon vim wget pkg-config git python-dev python3-pip libtool
pip install --upgrade pip

##### Turn off hyperthreading #####
echo off > /sys/devices/system/cpu/smt/control

######################
### EDIT /etc/hosts ##
######################

#cat << EOF >> /etc/hosts
#EOF

##########################
### INSTALL SINGULARITY ##
##########################

apt-get update && sudo apt-get install -y build-essential \
    uuid-dev \
    libgpgme-dev \
    squashfs-tools \
    libseccomp-dev \
    wget \
    pkg-config \
    git \
    cryptsetup-bin \
    stress

export VERSION=1.18 OS=linux ARCH=amd64 && \
    wget https://dl.google.com/go/go$VERSION.$OS-$ARCH.tar.gz && \
    sudo tar -C /usr/local -xzvf go$VERSION.$OS-$ARCH.tar.gz && \
    rm go$VERSION.$OS-$ARCH.tar.gz

echo 'export GOPATH=${HOME}/go' >> ~/.bashrc
echo 'export PATH=/usr/local/go/bin:${PATH}:${GOPATH}/bin' >> ~/.bashrc

export GOPATH=${HOME}/go >> ~/.bashrc
export PATH=/usr/local/go/bin:${PATH}:${GOPATH}/bin >> ~/.bashrc

export VERSION=3.8.7 && # adjust this as necessary \
    wget https://github.com/apptainer/singularity/releases/download/v${VERSION}/singularity-${VERSION}.tar.gz && \
    tar -xzf singularity-${VERSION}.tar.gz && \
    rm singularity-${VERSION}.tar.gz && \
    cd singularity-${VERSION}

./mconfig && \
    make -C ./builddir && \
    make -C ./builddir install

##########################
### INSTALL DOCKER      ##
##########################
cd
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io

#groupadd docker
usermod -aG docker condor

systemctl enable docker
systemctl restart docker

apt-get install -y docker-compose-plugin

############################
### INSTALL TSTAT       ####
############################

cd
wget http://www.tstat.polito.it/download/tstat-3.1.1.tar.gz
tar -xzvf tstat-3.1.1.tar.gz
cd tstat-3.1.1
./autogen.sh
./configure --enable-libtstat --enable-zlib
make && make install

############################
### SETUP POSEIDON USER ####
############################

apt-get install -y libpcap-dev

cd
useradd -s /bin/bash -d /home/poseidon -m -G docker poseidon

echo "poseidon     ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

mkdir /home/poseidon/.ssh
chmod -R 700 /home/poseidon/.ssh
echo "ssh-rsa ....." >> /home/poseidon/.ssh/authorized_keys

chmod 600 /home/poseidon/.ssh/authorized_keys
chown -R poseidon:poseidon /home/poseidon/.ssh

echo 'export GOPATH=${HOME}/go' >> /home/poseidon/.bashrc
echo 'export PATH=/usr/local/go/bin:${PATH}:${GOPATH}/bin' >> /home/poseidon/.bashrc


############################
### Pull docker container ##
############################

docker pull papajim/poseidon-execute:ubuntu20


############################
### Enable cgroups v2
############################
sed -i 's/GRUB_CMDLINE_LINUX=""/GRUB_CMDLINE_LINUX="nosmt systemd.unified_cgroup_hierarchy"/g' /etc/default/grub
update-grub

reboot
