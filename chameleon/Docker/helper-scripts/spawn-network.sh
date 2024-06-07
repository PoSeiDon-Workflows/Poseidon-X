#!/bin/bash

interface=$1
subnet=$2
gateway=$3
range=$4


docker network create \
  -d ipvlan \
  --subnet=$subnet \
  --gateway=$gateway \
  --ip-range=$4 \
  -o parent=$interface \
  -o ipvlan_mode=l2 \
  "poseidon_net"

