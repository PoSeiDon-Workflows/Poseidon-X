#!/bin/bash

condor_host=$1
cpu_num=$2
memory_size=$3
volume_details=$4
pool_pass=$5
network_name=$6
network_limit=$7
core_num=$(grep -c ^processor /proc/cpuinfo)

echo "Condor Host: $condor_host"
echo "CPU Num: $cpu_num"
echo "Memory: $memory_size"
echo "Volume: $volume_details"
echo "Pool pass: $pool_pass"
echo "Network limit: $network_limit"
echo "Total cpus available: $core_num"

upper_limit=$(($core_num-10))

for i in $(seq 0 4 $upper_limit)
do
  j=$(($i + 3))
  echo "$i-$j"
  echo "$(hostname)-container-$i-$j"
  
  docker run \
    -e CONDOR_HOST=$condor_host \
    -e NUM_CPUS=$cpu_num \
    -e POOL_PASSWORD=$pool_pass \
    -e NETWORK_LIMIT=$network_limit \
    -v $volume_details \
    -h "$(hostname)-container-$i-$j" \
    --rm \
    --detach \
    --cap-add=NET_ADMIN \
    --cpuset-cpus=$i-$j \
    --cpus=4.0 \
    --memory=$memory_size \
    --net=$network_name \
    --name "$(hostname)-container-$i-$j" \
    papajim/poseidon-execute
done
