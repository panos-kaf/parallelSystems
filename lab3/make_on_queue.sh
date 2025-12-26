#!/bin/bash

## Give the Job a descriptive name
#PBS -N make_kmeans

## Output and error files
#PBS -o results/make_kmeans.out
#PBS -e results/make_kmeans.err

## How many machines should we get? 
#PBS -l nodes=silver1:ppn=40

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start 
## Run make in the src folder (modify properly)

cd /home/parallel/parlab04/lab/lab3
make clean
make
