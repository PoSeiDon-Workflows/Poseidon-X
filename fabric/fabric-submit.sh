#!/usr/bin/env bash

# this script should run as root and has been tested with ubuntu 20.04

apt-get update && apt-get -y upgrade
apt-get install -y linux-headers-$(uname -r)
apt-get install -y build-essential make zlib1g-dev librrd-dev libpcap-dev autoconf automake libarchive-dev iperf3 htop bmon vim wget pkg-config git python-dev python3-pip libtool libpcap-dev
pip install --upgrade pip
pip install paramiko pandas elasticsearch==6.2.0

######################
### EDIT /etc/hosts ##
######################

cat << EOF >> /etc/hosts
192.168.104.100 poseidon-submit
192.168.104.200 poseidon-data
EOF

############################
### INSTALL APACHE2     ####
############################
apt-get install -y apache2
a2enmod userdir

######################
### INSTALL CONDOR ###
######################

wget -qO - https://research.cs.wisc.edu/htcondor/repo/keys/HTCondor-current-Key | sudo apt-key add -
echo "deb [arch=amd64] http://research.cs.wisc.edu/htcondor/repo/ubuntu/current $(lsb_release -cs) main" >> /etc/apt/sources.list

apt-get update && apt-get install -y htcondor

cat << EOF > /etc/condor/config.d/50-main.config
DAEMON_LIST = MASTER, COLLECTOR, NEGOTIATOR, SCHEDD

CONDOR_HOST = 192.168.104.100

USE_SHARED_PORT = TRUE

NETWORK_INTERFACE = 192.168.104.*

# the nodes have shared filesystem
UID_DOMAIN = \$(CONDOR_HOST)
TRUST_UID_DOMAIN = TRUE
FILESYSTEM_DOMAIN = \$(FULL_HOSTNAME)

#--     Authentication settings
SEC_PASSWORD_FILE = /etc/condor/pool_password
SEC_DEFAULT_AUTHENTICATION = REQUIRED
SEC_DEFAULT_AUTHENTICATION_METHODS = FS,PASSWORD
SEC_READ_AUTHENTICATION = OPTIONAL
SEC_CLIENT_AUTHENTICATION = OPTIONAL
SEC_ENABLE_MATCH_PASSWORD_AUTHENTICATION = TRUE
DENY_WRITE = anonymous@*
DENY_ADMINISTRATOR = anonymous@*
DENY_DAEMON = anonymous@*
DENY_NEGOTIATOR = anonymous@*
DENY_CLIENT = anonymous@*

#--     Privacy settings
SEC_DEFAULT_ENCRYPTION = OPTIONAL
SEC_DEFAULT_INTEGRITY = REQUIRED
SEC_READ_INTEGRITY = OPTIONAL
SEC_CLIENT_INTEGRITY = OPTIONAL
SEC_READ_ENCRYPTION = OPTIONAL
SEC_CLIENT_ENCRYPTION = OPTIONAL

#-- With strong security, do not use IP based controls
HOSTALLOW_WRITE = *
ALLOW_NEGOTIATOR = *

EOF

condor_store_cred -f /etc/condor/pool_password -p p0s31d0n

systemctl enable condor
systemctl restart condor

#######################
### INSTALL PEGASUS ###
#######################
wget -O - http://download.pegasus.isi.edu/pegasus/gpg.txt | sudo apt-key add -
echo "deb [arch=amd64] http://download.pegasus.isi.edu/pegasus/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/pegasus.list
apt-get update && apt-get install -y pegasus

##########################
### INSTALL APPTAINER  ###
##########################
cd
export VERSION="1.3.1" && \
    wget https://github.com/apptainer/apptainer/releases/download/v${VERSION}/apptainer_${VERSION}_amd64.deb && \
    apt-get install -y ./apptainer_${VERSION}_amd64.deb && \
    rm apptainer_${VERSION}_amd64.deb

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
usermod -aG docker poseidon

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

###########################################################
### SETUP poseidon USER using the poseidon-data volume ####
###########################################################
cd
useradd -s /bin/bash -d /home/poseidon -m -G docker poseidon

echo "poseidon     ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

mkdir /home/poseidon/.ssh
chmod -R 700 /home/poseidon/.ssh

echo "ssh-rsa ...." >> /home/poseidon/.ssh/authorized_keys

chmod 600 /home/poseidon/.ssh/authorized_keys
chown -R poseidon:poseidon /home/poseidon/.ssh

#### Add http userdir for user poseidon #####
mkdir /home/poseidon/public_html
 
cd
chmod -R 755 /home/poseidon/public_html
chown -R poseidon:poseidon /home/poseidon/public_html
sed -i 's/.*UserDir disabled.*/\tUserDir disabled root\n\tUserDir enabled poseidon/g' /etc/apache2/mods-available/userdir.conf

systemctl restart apache2
