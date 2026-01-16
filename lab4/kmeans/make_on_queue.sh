#!/bin/bash

## Give the Job a descriptive name
#PBS -N make_mpi_kmeans

## Output and error files
#PBS -o results/make_mpi_kmeans.out
#PBS -e results/make_mpi_kmeans.err

## How many machines should we get? 
#PBS -l nodes=1:ppn=1

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start 
## Run make in the src folder (modify properly)

module load openmpi/1.8.3
cd /home/parallel/parlab04/lab/lab4
make clean
make

