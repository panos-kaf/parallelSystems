#!/usr/bin/env python3
"""
Script to generate performance plots for MPI heat transfer simulations.
Creates:
1. Speedup plots for each table size (x-axis: MPI processes, y-axis: speedup)
2. Bar charts showing total and computation time for 8, 16, 32, 64 MPI processes
"""

import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import re

# Data structures to hold parsed results
serial_data = {}  # {method: {size: time}}
mpi_data = defaultdict(lambda: defaultdict(dict))  # {method: {num_procs: {size: {metrics}}}}

def parse_serial_results(filename):
    """Parse serial execution results."""
    with open(filename, 'r') as f:
        content = f.read()
    
    # Parse Jacobi results
    jacobi_matches = re.findall(r'Jacobi X (\d+) Y \d+ Iter \d+ Time ([\d.]+)', content)
    for size, time in jacobi_matches:
        if 'Jacobi' not in serial_data:
            serial_data['Jacobi'] = {}
        serial_data['Jacobi'][int(size)] = float(time)
    
    # Parse Gauss-Seidel SOR results
    gs_matches = re.findall(r'GaussSeidelSOR X (\d+) Y \d+ Iter \d+ Time ([\d.]+)', content)
    for size, time in gs_matches:
        if 'Gauss-Seidel SOR' not in serial_data:
            serial_data['Gauss-Seidel SOR'] = {}
        serial_data['Gauss-Seidel SOR'][int(size)] = float(time)
    
    # Parse Red-Black SOR results
    rb_matches = re.findall(r'RedBlackSOR X (\d+) Y \d+ Iter \d+ Time ([\d.]+)', content)
    for size, time in rb_matches:
        if 'Red-Black SOR' not in serial_data:
            serial_data['Red-Black SOR'] = {}
        serial_data['Red-Black SOR'][int(size)] = float(time)

def parse_mpi_results(filename, method='Jacobi'):
    """Parse MPI execution results for a given method."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    current_num_procs = None
    
    for line in lines:
        # Check for number of MPI tasks
        num_match = re.match(r'Num MPI Tasks: (\d+)', line)
        if num_match:
            current_num_procs = int(num_match.group(1))
            continue
        
        # Parse Jacobi results
        if method == 'Jacobi':
            jacobi_match = re.match(
                r'Jacobi X (\d+) Y \d+ Px \d+ Py \d+ Iter \d+ '
                r'ComputationTime ([\d.]+) CommunicationTime ([\d.]+) '
                r'ConvergenceTime ([\d.]+) TotalTime ([\d.]+)',
                line
            )
            if jacobi_match and current_num_procs:
                size = int(jacobi_match.group(1))
                comp_time = float(jacobi_match.group(2))
                comm_time = float(jacobi_match.group(3))
                conv_time = float(jacobi_match.group(4))
                total_time = float(jacobi_match.group(5))
                
                mpi_data[method][current_num_procs][size] = {
                    'computation': comp_time,
                    'communication': comm_time,
                    'convergence': conv_time,
                    'total': total_time
                }

def plot_speedup_curves():
    """Generate speedup plots for each table size."""
    sizes = sorted(set(serial_data.get('Jacobi', {}).keys()))
    methods = ['Jacobi', 'Gauss-Seidel SOR', 'Red-Black SOR']
    
    # Filter methods that have data
    available_methods = [m for m in methods if m in serial_data and m in mpi_data]
    
    if not available_methods:
        print("Warning: No complete data available for speedup plots")
        return
    
    # Create a figure with subplots for each size
    fig, axes = plt.subplots(1, len(sizes), figsize=(6*len(sizes), 5))
    if len(sizes) == 1:
        axes = [axes]
    
    fig.suptitle('MPI Heat Transfer Speedup Analysis', fontsize=14, fontweight='bold')
    
    colors = {'Jacobi': '#1f77b4', 'Gauss-Seidel SOR': '#d62728', 'Red-Black SOR': '#2ca02c'}
    markers = {'Jacobi': 'o', 'Gauss-Seidel SOR': 's', 'Red-Black SOR': '^'}
    
    for idx, size in enumerate(sizes):
        ax = axes[idx]
        
        for method in available_methods:
            if size not in serial_data[method]:
                continue
            
            serial_time = serial_data[method][size]
            
            # Get all processor counts for this method and size
            proc_counts = []
            speedups = []
            
            for num_procs in sorted(mpi_data[method].keys()):
                if size in mpi_data[method][num_procs]:
                    total_time = mpi_data[method][num_procs][size]['total']
                    speedup = serial_time / total_time
                    proc_counts.append(num_procs)
                    speedups.append(speedup)
            
            if proc_counts:
                ax.plot(proc_counts, speedups, 
                       marker=markers[method], 
                       color=colors[method],
                       label=method, 
                       linewidth=2.5, 
                       markersize=8)
        
        # Plot ideal speedup line
        if proc_counts:
            max_procs = max(proc_counts)
            ideal_procs = [p for p in proc_counts]
            ideal_speedup = ideal_procs
            ax.plot(ideal_procs, ideal_speedup, 
                   color='#95A5A6', 
                   linestyle='--',
                   label='Ideal', 
                   linewidth=2, 
                   alpha=0.8)
        
        ax.set_xlabel('Number of MPI Processes', fontweight='bold', fontsize=12)
        ax.set_ylabel('Speedup', fontweight='bold', fontsize=12)
        ax.set_title(f'{size}×{size} Table', fontsize=12, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(fontsize=10)
        ax.set_xscale('log', base=2)
        ax.set_yscale('log', base=2)
    
    plt.tight_layout()
    plt.savefig('speedup_plots.svg', dpi=300, bbox_inches='tight')
    print("Saved speedup plots to speedup_plots.svg")
    plt.close()

def plot_time_bars():
    """Generate bar charts for computation and total time (8, 16, 32, 64 processes)."""
    sizes = sorted(set(serial_data.get('Jacobi', {}).keys()))
    methods = ['Jacobi', 'Gauss-Seidel SOR', 'Red-Black SOR']
    proc_counts = [8, 16, 32, 64]
    
    # Filter methods that have data
    available_methods = [m for m in methods if m in mpi_data]
    
    if not available_methods:
        print("Warning: No MPI data available for bar charts")
        return
    
    # Create subplots: one row per size, one column per processor count
    fig, axes = plt.subplots(len(sizes), len(proc_counts), 
                            figsize=(4*len(proc_counts), 4*len(sizes)))
    
    if len(sizes) == 1:
        axes = axes.reshape(1, -1)
    if len(proc_counts) == 1:
        axes = axes.reshape(-1, 1)
    
    fig.suptitle('MPI Heat Transfer Execution Time Analysis', fontsize=14, fontweight='bold', y=0.995)
    
    colors_comp = {'Jacobi': '#5DADE2', 'Gauss-Seidel SOR': '#EC7063', 'Red-Black SOR': '#52BE80'}
    colors_total = {'Jacobi': '#AED6F1', 'Gauss-Seidel SOR': '#F5B7B1', 'Red-Black SOR': '#A9DFBF'}
    edge_colors = {'Jacobi': '#2874A6', 'Gauss-Seidel SOR': '#A93226', 'Red-Black SOR': '#27AE60'}
    
    for size_idx, size in enumerate(sizes):
        # Find max time for this size to set common y-axis scale
        max_time = 0
        for num_procs in proc_counts:
            for method in available_methods:
                if num_procs in mpi_data[method] and size in mpi_data[method][num_procs]:
                    total_time = mpi_data[method][num_procs][size]['total']
                    max_time = max(max_time, total_time)
        
        for proc_idx, num_procs in enumerate(proc_counts):
            ax = axes[size_idx, proc_idx]
            
            # Prepare data for this subplot
            method_names = []
            comp_times = []
            total_times = []
            
            for method in available_methods:
                if num_procs in mpi_data[method] and size in mpi_data[method][num_procs]:
                    method_names.append(method)
                    comp_times.append(mpi_data[method][num_procs][size]['computation'])
                    total_times.append(mpi_data[method][num_procs][size]['total'])
            
            if not method_names:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
                ax.set_xticks([])
                ax.set_yticks([])
                continue
            
            x = np.arange(len(method_names))
            width = 0.35
            
            # Create bars
            bars1 = ax.bar(x - width/2, comp_times, width, 
                          label='Computation Time',
                          color=[colors_comp[m] for m in method_names],
                          edgecolor=[edge_colors[m] for m in method_names],
                          linewidth=1.5)
            bars2 = ax.bar(x + width/2, total_times, width, 
                          label='Total Time',
                          color=[colors_total[m] for m in method_names],
                          edgecolor=[edge_colors[m] for m in method_names],
                          linewidth=1.5)
            
            # Add values on top of bars
            for bar, time in zip(bars1, comp_times):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height + max_time*0.01,
                       f'{time:.2f}s', ha='center', va='bottom', 
                       fontsize=8, fontweight='bold')
            
            for bar, time in zip(bars2, total_times):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height + max_time*0.01,
                       f'{time:.2f}s', ha='center', va='bottom', 
                       fontsize=8, fontweight='bold')
            
            # Formatting
            ax.set_ylabel('Time (seconds)', fontweight='bold', fontsize=10)
            ax.set_title(f'{size}×{size}, {num_procs} procs', fontsize=11, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels([m.replace(' ', '\n') for m in method_names], 
                              fontsize=9, rotation=0)
            ax.set_ylim(0, max_time * 1.15)  # Common y-scale for this size with extra space for labels
            ax.grid(True, linestyle='--', alpha=0.4, axis='y')
            
            # Add legend only to the top-right subplot
            if size_idx == 0 and proc_idx == len(proc_counts) - 1:
                ax.legend(fontsize=9, loc='upper right')
    
    plt.tight_layout()
    plt.savefig('time_bars.svg', dpi=300, bbox_inches='tight')
    print("Saved time bar charts to time_bars.svg")
    plt.close()

def main():
    """Main function to parse data and generate plots."""
    print("Parsing serial results...")
    parse_serial_results('results_serial/serial.out')
    print(f"Found serial data for methods: {list(serial_data.keys())}")
    
    print("\nParsing MPI results...")
    # Parse Jacobi MPI results
    parse_mpi_results('results/run_mpi_jacobi.out', 'Jacobi')
    
    # TODO: Add parsing for other methods when data is available
    # parse_mpi_results('results/run_mpi_gauss_seidel.out', 'Gauss-Seidel SOR')
    # parse_mpi_results('results/run_mpi_red_black.out', 'Red-Black SOR')
    
    print(f"Found MPI data for methods: {list(mpi_data.keys())}")
    
    # Display summary
    for method in mpi_data:
        proc_counts = sorted(mpi_data[method].keys())
        print(f"  {method}: {len(proc_counts)} processor configurations")
    
    print("\nGenerating speedup plots...")
    plot_speedup_curves()
    
    print("\nGenerating time bar charts...")
    plot_time_bars()
    
    # Print summary statistics
    print("\n=== Performance Summary ===")
    for method in sorted(mpi_data.keys()):
        if method in serial_data:
            print(f"\n{method}:")
            for size in sorted(serial_data[method].keys()):
                serial_time = serial_data[method][size]
                print(f"  Table Size {size}×{size}:")
                print(f"    Serial Time: {serial_time:.4f}s")
                
                proc_counts = sorted(mpi_data[method].keys())
                if proc_counts:
                    print(f"    MPI Processes | Total Time | Speedup")
                    print(f"    " + "-" * 42)
                    for num_procs in proc_counts:
                        if size in mpi_data[method][num_procs]:
                            total_time = mpi_data[method][num_procs][size]['total']
                            speedup = serial_time / total_time
                            print(f"    {num_procs:13d} | {total_time:10.4f}s | {speedup:7.2f}x")
    
    print("\nDone!")

if __name__ == '__main__':
    main()
