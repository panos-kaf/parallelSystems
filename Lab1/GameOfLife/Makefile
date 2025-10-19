all: omp_gol

omp_gol: Game_Of_Life.c
	gcc -O3 -fopenmp -o omp_gol Game_Of_Life.c

clean: 
	rm omp_gol
