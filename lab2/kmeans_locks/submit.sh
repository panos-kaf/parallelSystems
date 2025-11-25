#!/bin/bash

binaries=(
    kmeans_omp_naive
    kmeans_omp_nosync_lock
    kmeans_omp_pthread_mutex_lock
    kmeans_omp_pthread_spin_lock
    kmeans_omp_array_lock
    kmeans_omp_clh_lock
    kmeans_omp_tas_lock
    kmeans_omp_ttas_lock
    kmeans_omp_critical
)

for bin in "${binaries[@]}"; do
    echo "Submitting job for: $bin"
    qsub -q serial \
         -N run_$bin \
         -o results/${bin}.out \
         -e results/${bin}.err \
         run_on_queue.sh \
         -v ARG_BIN=$bin 
done
