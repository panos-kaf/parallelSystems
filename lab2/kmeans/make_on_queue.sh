#!/bin/bash

## Give the Job a descriptive name
#PBS -N make_kmeans_reduction

## Output and error files
#PBS -o results/make_kmeans_reduction.out
#PBS -e results/make_kmeans_reduction.err

## How many machines should we get? 
#PBS -l nodes=sandman:ppn=64
##PBS -l nodes=1:ppn=1

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start 
## Run make in the src folder (modify properly)

cd /home/parallel/parlab04/2025-2026/a2/kmeans
make clean
make
