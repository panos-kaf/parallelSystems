import matplotlib.pyplot as plt
import numpy as np
import re
import os
import sys

def parse_openmp_results(filename):
    """Parse OpenMP k-means results file."""
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        return None
    
    with open(filename, 'r') as f:
        content = f.read()
    
    # Extract configuration from first line
    config_match = re.search(r'dataset_size = ([\d.]+) MB\s+numObjs = (\d+)\s+numCoords = (\d+)\s+numClusters = (\d+)', content)
    if not config_match:
        print("Error: Could not parse configuration from OpenMP file.")
        return None
    
    dataset_size = config_match.group(1)
    num_objs = config_match.group(2)
    num_coords = config_match.group(3)
    num_clusters = config_match.group(4)
    
    config = {
        'dataset_size': dataset_size,
        'numObjs': num_objs,
        'numCoords': num_coords,
        'numClusters': num_clusters
    }
    
    # Extract all results
    pattern = r'number of threads: (\d+)\).*?per loop =\s+([\d.]+)s'
    matches = re.findall(pattern, content, re.DOTALL)
    
    if not matches:
        print("Error: Could not parse timing data from OpenMP file.")
        return None
    
    results = []
    for num_threads, time_per_loop in matches:
        results.append({
            'num_threads': int(num_threads),
            'time': float(time_per_loop)
        })
    
    # Sort by number of threads
    results.sort(key=lambda x: x['num_threads'])
    
    return config, results

def parse_mpi_results(filename):
    """Parse MPI k-means results file."""
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        return None
    
    with open(filename, 'r') as f:
        content = f.read()
    
    # Extract configuration from first line
    config_match = re.search(r'dataset_size = ([\d.]+) MB\s+numObjs = (\d+)\s+numCoords = (\d+)\s+numClusters = (\d+)', content)
    if not config_match:
        print("Error: Could not parse configuration from MPI file.")
        return None
    
    dataset_size = config_match.group(1)
    num_objs = config_match.group(2)
    num_coords = config_match.group(3)
    num_clusters = config_match.group(4)
    
    config = {
        'dataset_size': dataset_size,
        'numObjs': num_objs,
        'numCoords': num_coords,
        'numClusters': num_clusters
    }
    
    # Extract all results
    pattern = r'Num MPI Tasks: (\d+).*?per loop =\s+([\d.]+)s'
    matches = re.findall(pattern, content, re.DOTALL)
    
    if not matches:
        print("Error: Could not parse timing data from MPI file.")
        return None
    
    results = []
    for num_tasks, time_per_loop in matches:
        results.append({
            'num_tasks': int(num_tasks),
            'time': float(time_per_loop)
        })
    
    # Sort by number of tasks
    results.sort(key=lambda x: x['num_tasks'])
    
    return config, results

def generate_comparison_plot(openmp_config, openmp_results, mpi_config, mpi_results, output_dir='plots'):
    """Generate comparison speedup plot for OpenMP and MPI."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Extract data
    openmp_threads = [r['num_threads'] for r in openmp_results]
    openmp_times = [r['time'] for r in openmp_results]
    openmp_baseline = openmp_times[0]
    openmp_speedups = [openmp_baseline / t for t in openmp_times]
    
    mpi_tasks = [r['num_tasks'] for r in mpi_results]
    mpi_times = [r['time'] for r in mpi_results]
    mpi_baseline = mpi_times[0]
    mpi_speedups = [mpi_baseline / t for t in mpi_times]
    
    # --- Create Comparison Speedup Plot ---
    fig, ax = plt.subplots(figsize=(12, 7))
    
    title = f"K-Means Speedup Comparison: OpenMP vs MPI\n({openmp_config['numObjs']} objects, {openmp_config['numCoords']} coords, {openmp_config['numClusters']} clusters, {openmp_config['dataset_size']} MB)"
    fig.suptitle(title, fontsize=14, fontweight='bold')
    
    # Prepare data for grouped bar plot
    all_workers = sorted(set(openmp_threads + mpi_tasks))
    x_pos = np.arange(len(all_workers))
    width = 0.35
    
    # Create arrays for speedups, filling with None where data doesn't exist
    openmp_speedup_array = []
    mpi_speedup_array = []
    
    for workers in all_workers:
        openmp_idx = next((i for i, r in enumerate(openmp_results) if r['num_threads'] == workers), None)
        mpi_idx = next((i for i, r in enumerate(mpi_results) if r['num_tasks'] == workers), None)
        
        openmp_speedup_array.append(openmp_speedups[openmp_idx] if openmp_idx is not None else 0)
        mpi_speedup_array.append(mpi_speedups[mpi_idx] if mpi_idx is not None else 0)
    
    # Plot grouped bars
    bars1 = ax.bar(x_pos - width/2, openmp_speedup_array, width, 
                   color='#E74C3C', edgecolor='#A93226', linewidth=1.5, label='OpenMP')
    bars2 = ax.bar(x_pos + width/2, mpi_speedup_array, width,
                   color='#3498DB', edgecolor='#1F618D', linewidth=1.5, label='MPI')
    
    # Add ideal speedup line for reference
    ideal_speedup = all_workers
    ax.plot(x_pos, ideal_speedup, linestyle='--', color='#95A5A6', linewidth=2, 
            marker='', label='Ideal Speedup', alpha=0.7)
    
    ax.set_xlabel('Number of Workers (Threads/Tasks)', fontweight='bold', fontsize=12)
    ax.set_ylabel('Speedup (relative to 1 worker)', fontweight='bold', fontsize=12)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([str(w) for w in all_workers])
    ax.grid(True, axis='y', linestyle='--', alpha=0.4)
    ax.legend(fontsize=11, loc='upper left')
    
    # Annotate bars with speedup values
    for bar, speedup in zip(bars1, openmp_speedup_array):
        if speedup > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(openmp_speedup_array + mpi_speedup_array)*0.02,
                   f'{speedup:.2f}x', ha='center', va='bottom', fontsize=9, color='#A93226', fontweight='bold')
    
    for bar, speedup in zip(bars2, mpi_speedup_array):
        if speedup > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(openmp_speedup_array + mpi_speedup_array)*0.02,
                   f'{speedup:.2f}x', ha='center', va='bottom', fontsize=9, color='#1F618D', fontweight='bold')
    
    plt.tight_layout()
    
    # Save plot
    filename = os.path.join(output_dir, 'kmeans_speedup_comparison.svg')
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved comparison plot to {filename}")
    
    plt.close()
    
    # --- Create Execution Time Comparison Plot ---
    fig2, ax2 = plt.subplots(figsize=(12, 7))
    
    title2 = f"K-Means Execution Time Comparison: OpenMP vs MPI\n({openmp_config['numObjs']} objects, {openmp_config['numCoords']} coords, {openmp_config['numClusters']} clusters, {openmp_config['dataset_size']} MB)"
    fig2.suptitle(title2, fontsize=14, fontweight='bold')
    
    # Create arrays for execution times
    openmp_time_array = []
    mpi_time_array = []
    
    for workers in all_workers:
        openmp_idx = next((i for i, r in enumerate(openmp_results) if r['num_threads'] == workers), None)
        mpi_idx = next((i for i, r in enumerate(mpi_results) if r['num_tasks'] == workers), None)
        
        openmp_time_array.append(openmp_times[openmp_idx] if openmp_idx is not None else 0)
        mpi_time_array.append(mpi_times[mpi_idx] if mpi_idx is not None else 0)
    
    # Plot grouped bars
    bars1_time = ax2.bar(x_pos - width/2, openmp_time_array, width, 
                         color='#E74C3C', edgecolor='#A93226', linewidth=1.5, label='OpenMP')
    bars2_time = ax2.bar(x_pos + width/2, mpi_time_array, width,
                         color='#3498DB', edgecolor='#1F618D', linewidth=1.5, label='MPI')
    
    ax2.set_xlabel('Number of Workers (Threads/Tasks)', fontweight='bold', fontsize=12)
    ax2.set_ylabel('Execution Time (seconds)', fontweight='bold', fontsize=12)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([str(w) for w in all_workers])
    ax2.grid(True, axis='y', linestyle='--', alpha=0.4)
    ax2.legend(fontsize=11, loc='upper right')
    
    # Annotate bars with time values
    for bar, time_val in zip(bars1_time, openmp_time_array):
        if time_val > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(openmp_time_array + mpi_time_array)*0.02,
                    f'{time_val:.4f}s', ha='center', va='bottom', fontsize=9, color='#A93226', fontweight='bold')
    
    for bar, time_val in zip(bars2_time, mpi_time_array):
        if time_val > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(openmp_time_array + mpi_time_array)*0.02,
                    f'{time_val:.4f}s', ha='center', va='bottom', fontsize=9, color='#1F618D', fontweight='bold')
    
    plt.tight_layout()
    
    # Save execution time plot
    filename2 = os.path.join(output_dir, 'kmeans_execution_time_comparison.svg')
    plt.savefig(filename2, dpi=300, bbox_inches='tight')
    print(f"Saved execution time comparison plot to {filename2}")
    
    plt.close()
    
    # --- Print Summary Statistics ---
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON SUMMARY")
    print("="*80)
    print(f"Configuration: {openmp_config['numObjs']} objects, {openmp_config['numCoords']} coords, {openmp_config['numClusters']} clusters\n")
    
    print("OpenMP Results:")
    print("-" * 60)
    print(f"{'Threads':>10} | {'Time (s)':>10} | {'Speedup':>10} | {'Efficiency':>10}")
    print("-" * 60)
    for i, r in enumerate(openmp_results):
        efficiency = openmp_speedups[i] / r['num_threads'] * 100
        print(f"{r['num_threads']:>10} | {r['time']:>10.4f} | {openmp_speedups[i]:>9.2f}x | {efficiency:>9.2f}%")
    
    print("\nMPI Results:")
    print("-" * 60)
    print(f"{'Tasks':>10} | {'Time (s)':>10} | {'Speedup':>10} | {'Efficiency':>10}")
    print("-" * 60)
    for i, r in enumerate(mpi_results):
        efficiency = mpi_speedups[i] / r['num_tasks'] * 100
        print(f"{r['num_tasks']:>10} | {r['time']:>10.4f} | {mpi_speedups[i]:>9.2f}x | {efficiency:>9.2f}%")
    
    # Compare at same worker counts
    print("\nDirect Comparison (at same worker counts):")
    print("-" * 80)
    print(f"{'Workers':>10} | {'OpenMP (s)':>12} | {'MPI (s)':>12} | {'Faster':>15} | {'Difference':>10}")
    print("-" * 80)
    
    for workers in all_workers:
        openmp_time = next((r['time'] for r in openmp_results if r['num_threads'] == workers), None)
        mpi_time = next((r['time'] for r in mpi_results if r['num_tasks'] == workers), None)
        
        if openmp_time is not None and mpi_time is not None:
            if openmp_time < mpi_time:
                faster = "OpenMP"
                diff = ((mpi_time - openmp_time) / mpi_time) * 100
            else:
                faster = "MPI"
                diff = ((openmp_time - mpi_time) / openmp_time) * 100
            
            print(f"{workers:>10} | {openmp_time:>12.4f} | {mpi_time:>12.4f} | {faster:>15} | {diff:>9.2f}%")
    
    print("="*80)

def main():
    if len(sys.argv) < 3:
        print("Usage: python plot_comparison.py <openmp_results_file> <mpi_results_file> [output_dir]")
        print("Example: python plot_comparison.py openmp_old_results/run_kmeans_reduction.out results/run_mpi_kmeans.out plots")
        return
    
    openmp_file = sys.argv[1]
    mpi_file = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else 'plots'
    
    # Parse results
    openmp_result = parse_openmp_results(openmp_file)
    if openmp_result is None:
        return
    openmp_config, openmp_results = openmp_result
    
    mpi_result = parse_mpi_results(mpi_file)
    if mpi_result is None:
        return
    mpi_config, mpi_results = mpi_result
    
    # Verify configurations match
    if (openmp_config['numObjs'] != mpi_config['numObjs'] or 
        openmp_config['numCoords'] != mpi_config['numCoords'] or
        openmp_config['numClusters'] != mpi_config['numClusters']):
        print("Warning: OpenMP and MPI configurations do not match!")
        print(f"OpenMP: {openmp_config}")
        print(f"MPI: {mpi_config}")
    
    # Generate comparison plot
    generate_comparison_plot(openmp_config, openmp_results, mpi_config, mpi_results, output_dir)

if __name__ == "__main__":
    main()
