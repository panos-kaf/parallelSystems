#!/bin/bash

## Give the Job a descriptive name
#PBS -N run_omp_gameoflife

## Output and error files
#PBS -o run_omp_gameoflife.out
#PBS -e run_omp_gameoflife.err

## How many machines should we get? 
#PBS -l nodes=1:ppn=8

##How long should the job run for?
#PBS -l walltime=00:45:00

## Start 
## Run make in the src folder (modify properly)

module load openmp
cd /home/parallel/parlab04/2025-2026/a1
for i in 1 2 4 6 8
do
#export OMP_NUM_THREADS=$i
echo "Threads: $i"
for j in 64 1024 4096
   do
      ./omp_gol $j 1000 $i 
   done
done

