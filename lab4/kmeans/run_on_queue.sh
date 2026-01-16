#!/bin/bash

## Give the Job a descriptive name
#PBS -N run_mpi_kmeans

## Output and error files
#PBS -o results/run_mpi_kmeans.out
#PBS -e results/run_mpi_kmeans.err

## How many machines should we get? 
#PBS -l nodes=8:ppn=8

## Start 
## Run make in the src folder (modify properly)

module load openmpi/1.8.3

cd /home/parallel/parlab04/lab/lab4

for num_tasks in 1 2 4 8 16 32 64
do
    echo "Num MPI Tasks: $num_tasks"
    mpirun -np $num_tasks --mca btl tcp,self ./kmeans_mpi -s 256 -n 16 -c 32 -l 10
done
