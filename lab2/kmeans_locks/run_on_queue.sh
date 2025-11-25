#!/bin/bash

## Give the Job a descriptive name
#PBS -N run_${ARG_BIN}

## Output and error files
##PBS -o results/${ARG_BIN}.out
##PBS -e results/${ARG_BIN}.err

## How many machines should we get? 
#PBS -l nodes=1:ppn=64

##How long should the job run for?
#PBS -l walltime=02:00:00

## Start 
## Run make in the src folder (modify properly)

cd /home/parallel/parlab04/lab/lab2/kmeans_locks

export OMP_PROC_BIND=true

for nthreads in 1 2 4 8 16 32 64
    do
        echo "--- nthreads = ${nthreads} ---"
        bin="${ARG_BIN}"
        echo "Running: $bin"
        export OMP_NUM_THREADS=$nthreads
        ./$bin -s 32 -n 16 -c 32 -l 10 
    done
