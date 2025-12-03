#!/bin/bash

implementations="x.cgl x.fgl x.lazy x.nb x.opt"
percents=("100 0 0" "80 10 10" "20 40 40" "0 50 50")

cores_1="0"
cores_2="0,1"
cores_4="0,1,2,3"
cores_8="0,1,2,3,4,5,6,7"
cores_16="$(seq -s ',' 0 15)"
cores_32="$(seq -s ',' 0 31)"
cores_64="$(seq -s ',' 0 63)"
cores_128="$(seq -s ',' 0 63),$(seq -s ',' 0 63)"

#run serial
echo "--- SERIAL ---"
for size in 1024 8192
do
    for pcts in "${percents[@]}"
    do
        echo "---  SIZE = ${size} - PERCENTS = ${pcts} ---"
        export MT_CONF=${cores_1}
        ./x.serial "${size}" ${pcts}
        echo -e "\n-------------------------------------------------------------------------------\n"
    done
done

#run all implementations
for nthreads in 1 2 4 8 16 32 64 128
do
    for size in 1024 8192
    do
        for pcts in "${percents[@]}"
        do
            echo -e "\n--- NTHREADS = ${nthreads} - SIZE = ${size} - PERCENTS = ${pcts} ---\n"
            for implementation in ${implementations}
            do
                cores_index="cores_${nthreads}"
                export MT_CONF=${!cores_index}
                echo "${implementation}"
                ./"${implementation}" "${size}" ${pcts}
                echo
            done
            echo -e "-------------------------------------------------------------------------------\n"
        done
    done
done
