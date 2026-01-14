import matplotlib.pyplot as plt
import numpy as np
import re
import os

def parse_all_gpu_results(filename):
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        return 0, []

    with open(filename, 'r') as f:
        content = f.read()

    # Extract Sequential Time
    seq_section = re.search(r'Sequential Kmeans.*?t_loop_avg = ([\d.]+) ms', content, re.DOTALL)
    seq_time = float(seq_section.group(1)) if seq_section else 0

    # Split by the separator
    sections = content.split('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

    block_data = []

    for section in sections:
        if 'block_size' not in section:
            continue
        try:
            bs = int(re.search(r'block_size = (\d+)', section).group(1))
            t_loop_avg = float(re.search(r't_loop_avg = ([\d.]+) ms', section).group(1))
            
            block_data.append({'bs': bs, 'time': t_loop_avg})
        except (AttributeError, ValueError):
            continue

    return seq_time, block_data

def plot_speedup(seq_time, data):
    if not data:
        print("No data to plot.")
        return

    # Sort by block size
    data.sort(key=lambda x: x['bs'])
    
    block_sizes = [d['bs'] for d in data]
    speedups = [seq_time / d['time'] for d in data]

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(block_sizes))
    width = 0.6
    
    bars = ax.bar(x, speedups, width, color='#f1c40f', edgecolor='black', linewidth=1)
    
    ax.set_ylabel('Speedup (Sequential / GPU)', fontweight='bold', fontsize=12)
    ax.set_xlabel('Block Size', fontweight='bold', fontsize=12)
    ax.set_title('KMeans Full-Offload GPU Speedup vs Block Size', fontweight='bold', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(block_sizes)
    ax.axhline(y=1, color='red', linestyle='--', linewidth=1, label='Baseline (1x)')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend()
    
    # Add speedup values on top of bars
    for i, (bar, speedup) in enumerate(zip(bars, speedups)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{speedup:.2f}x',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    plt.tight_layout()
    
    # Save plot
    if not os.path.exists('plots'):
        os.makedirs('plots')
    
    filename = 'plots/kmeans_all_gpu_speedup.png'
    plt.savefig(filename, dpi=300)
    print(f"Saved plot to {filename}")
    plt.show()

def main():
    filename = 'results/run_kmeans_all_gpu.out'
    
    seq_time, block_data = parse_all_gpu_results(filename)
    
    if seq_time == 0:
        print("Sequential time not found.")
        return
    
    print(f"Sequential time: {seq_time:.2f} ms")
    print(f"Found {len(block_data)} block size configurations")
    
    plot_speedup(seq_time, block_data)

if __name__ == "__main__":
    main()