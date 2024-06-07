#!/usr/bin/env bash

# this script should run as root

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
useradd -s /bin/bash -d /home/poseidon -m poseidon

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
