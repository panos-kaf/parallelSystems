import matplotlib.pyplot as plt
import numpy as np
import re
import os
import sys

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
        print("Error: Could not parse configuration.")
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
        print("Error: Could not parse timing data.")
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

def generate_plots(config, results, output_dir='plots'):
    """Generate execution time and speedup plots."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    num_tasks = [r['num_tasks'] for r in results]
    times = [r['time'] for r in results]
    
    # Calculate speedup relative to single task
    baseline_time = times[0]
    speedups = [baseline_time / t for t in times]
    
    # --- Plot 1: Execution Time ---
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    
    title = f"K-Means MPI Execution Time\n({config['numObjs']} objects, {config['numCoords']} coords, {config['numClusters']} clusters, {config['dataset_size']} MB)"
    fig1.suptitle(title, fontsize=14, fontweight='bold')
    
    x_pos = np.arange(len(num_tasks))
    width = 0.6
    
    bars1 = ax1.bar(x_pos, times, width, color='#5DADE2', edgecolor='#2874A6', linewidth=1.5)
    
    # Add baseline reference line
    ax1.axhline(baseline_time, color='#95A5A6', linestyle='--', linewidth=2, 
                label=f'Baseline (1 task): {baseline_time:.4f}s', alpha=0.8)
    
    ax1.set_ylabel('Execution Time (seconds)', fontweight='bold', fontsize=12)
    ax1.set_xlabel('Number of MPI Tasks', fontweight='bold', fontsize=12)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(num_tasks)
    ax1.legend(fontsize=11)
    ax1.grid(axis='y', linestyle='--', alpha=0.4)
    
    # Add values on top of bars
    for i, (bar, time) in enumerate(zip(bars1, times)):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + baseline_time*0.02,
                f'{time:.4f}s', ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    plt.tight_layout()
    
    # Save execution time plot
    filename1 = os.path.join(output_dir, 'mpi_kmeans_execution_time.svg')
    plt.savefig(filename1, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {filename1}")
    
    plt.close()
    
    # --- Plot 2: Speedup ---
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    
    title = f"K-Means MPI Speedup\n({config['numObjs']} objects, {config['numCoords']} coords, {config['numClusters']} clusters, {config['dataset_size']} MB)"
    fig2.suptitle(title, fontsize=14, fontweight='bold')
    
    bars2 = ax2.bar(x_pos, speedups, width, color='#58D68D', edgecolor='#28B463', linewidth=1.5, 
                    label='Speedup')

    ax2.set_ylabel('Speedup (relative to 1 task)', fontweight='bold', fontsize=12)
    ax2.set_xlabel('Number of MPI Tasks', fontweight='bold', fontsize=12)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(num_tasks)
    ax2.legend(fontsize=11)
    ax2.grid(axis='y', linestyle='--', alpha=0.4)
    
    # Add speedup values on bars
    for i, (bar, speedup) in enumerate(zip(bars2, speedups)):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(speedups)*0.02,
                f'{speedup:.2f}x', ha='center', va='bottom', 
                fontweight='bold', fontsize=10)
    
    plt.tight_layout()
    
    # Save speedup plot
    filename2 = os.path.join(output_dir, 'mpi_kmeans_speedup.svg')
    plt.savefig(filename2, dpi=300, bbox_inches='tight')
    print(f"Saved plot to {filename2}")
    
    plt.close()
    
    # Print summary statistics
    print("\n=== Performance Summary ===")
    print(f"Configuration: {config['numObjs']} objects, {config['numCoords']} coords, {config['numClusters']} clusters")
    print(f"\nNumber of Tasks | Time (s) | Speedup")
    print("-" * 45)
    for i, r in enumerate(results):
        print(f"{r['num_tasks']:15d} | {r['time']:8.4f} | {speedups[i]:7.2f}x")

def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_mpi_results.py <results_file> [output_dir]")
        print("Example: python plot_mpi_results.py results/run_mpi_kmeans.out plots")
        return
    
    file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'plots'
    
    result = parse_mpi_results(file_path)
    if result is None:
        return
    
    config, results = result
    generate_plots(config, results, output_dir)

if __name__ == "__main__":
    main()