#!/bin/bash

## Give the Job a descriptive name
#PBS -N run_kmeans_reduction

## Output and error files
#PBS -o results/run_kmeans_reduction.out
#PBS -e results/run_kmeans_reduction.err

## How many machines should we get? 
#PBS -l nodes=sandman:ppn=64
##PBS -l nodes=1:ppn=8

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start 
## Run make in the src folder (modify properly)

cd /home/parallel/parlab04/2025-2026/a2/kmeans

for nthreads in 1 2 4 8 16 32 64
do
    export OMP_NUM_THREADS=$nthreads
    export GOMP_CPU_AFFINITY="0-63"
#./kmeans_omp_reduction -s 256 -n 16 -c 32 -l 10
    ./kmeans_omp_reduction -s 256 -n 1 -c 4 -l 10
done
