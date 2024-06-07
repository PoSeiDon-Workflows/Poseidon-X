#!/usr/bin/env bash


DOCKER_BUILDKIT=1 docker build -t papajim/poseidon-execute:centos8 -f Dockerfile_Centos8 .

DOCKER_BUILDKIT=1 docker build -t papajim/poseidon-execute:ubuntu20 -f Dockerfile_Ubuntu20 .
