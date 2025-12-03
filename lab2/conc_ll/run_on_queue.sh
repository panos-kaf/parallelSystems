#!/bin/bash

## Give the Job a descriptive name
#PBS -N run_conc_ll

## Output and error files
#PBS -o results/run_conc_ll.out
#PBS -e results/run_conc_ll.err

## How many machines should we get? 
#PBS -l nodes=sandman:ppn=64

##How long should the job run for?
#PBS -l walltime=01:30:00

## Start 
## Run make in the src folder (modify properly)

cd /home/parallel/parlab04/lab/lab2/conc_ll
mkdir -p results

./run_all.sh
