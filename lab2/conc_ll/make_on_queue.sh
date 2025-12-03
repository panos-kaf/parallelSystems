#!/bin/bash

## Give the Job a descriptive name
#PBS -N make_conc_ll

## Output and error files
#PBS -o results/make.out
#PBS -e results/make.err

## How many machines should we get? 
#PBS -l nodes=sandman:ppn=64

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start 
## Run make in the src folder (modify properly)

cd /home/parallel/parlab04/lab/lab2/conc_ll

mkdir -p results

make clean; make
