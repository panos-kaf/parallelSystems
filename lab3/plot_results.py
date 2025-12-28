import matplotlib.pyplot as plt
import numpy as np
import re
import os

def parse_results(filename):
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        return 0, [], []

    with open(filename, 'r') as f:
        content = f.read()

    # Extract Sequential Time
    seq_section = re.search(r'Sequential Kmeans.*?t_loop_avg = ([\d.]+) ms', content, re.DOTALL)
    seq_time = float(seq_section.group(1)) if seq_section else 0

    # Split by the separator used in the file
    sections = content.split('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    
    naive_data = []
    transpose_data = []

    for section in sections:
        if 'block_size' not in section:
            continue
        
        try:
            bs = int(re.search(r'block_size = (\d+)', section).group(1))
            t_gpu = float(re.search(r't_gpu_avg = ([\d.]+) ms', section).group(1))
            t_transfers = float(re.search(r't_transfers_avg = ([\d.]+) ms', section).group(1))
            t_cpu = float(re.search(r't_cpu_avg = ([\d.]+) ms', section).group(1))
            t_total = float(re.search(r't_loop_avg = ([\d.]+) ms', section).group(1))

            entry = {'bs': bs, 'gpu': t_gpu, 'transfers': t_transfers, 'cpu': t_cpu, 'total': t_total}

            if 'Naive GPU Kmeans' in section:
                naive_data.append(entry)
            elif 'Transpose GPU Kmeans' in section:
                transpose_data.append(entry)
        except (AttributeError, ValueError):
            continue

    return seq_time, naive_data, transpose_data

def generate_plots(seq_time, data, title_suffix):
    if not data:
        return

    # Sort data by block size
    data.sort(key=lambda x: x['bs'])
    
    bs_labels = [str(d['bs']) for d in data]
    x_labels_time = bs_labels
    
    gpu_times = np.array([d['gpu'] for d in data])
    transfer_times = np.array([d['transfers'] for d in data])
    cpu_times = np.array([d['cpu'] for d in data])
    speedups = [seq_time / d['total'] for d in data]

    # Broken y-axis: two subplots for time, one for speedup
    fig = plt.figure(figsize=(16, 9))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 3], width_ratios=[2, 1])
    ax1_top = fig.add_subplot(gs[0, 0])
    ax1_bottom = fig.add_subplot(gs[1, 0], sharex=ax1_top)
    ax2 = fig.add_subplot(gs[:, 1])

    fig.suptitle(f'{title_suffix}', fontsize=16, fontweight='bold')

    x_time = np.arange(len(x_labels_time))
    width = 0.6

    # Plot bars on both axes
    for ax in [ax1_top, ax1_bottom]:
        ax.bar(x_time, gpu_times, width, label='GPU Execution', color='#2ecc71', edgecolor='black', linewidth=0.5)
        ax.bar(x_time, transfer_times, width, bottom=gpu_times, label='Data Transfers', color='#e74c3c', edgecolor='black', linewidth=0.5)
        ax.bar(x_time, cpu_times, width, bottom=gpu_times + transfer_times, label='Other CPU', color='#3498db', edgecolor='black', linewidth=0.5)

    # Top axis: show only the sequential line
    ax1_top.axhline(seq_time, color='gray', linestyle='--', linewidth=2, label=f'Sequential Time ({seq_time:.1f} ms)')
    ax1_top.text(len(x_time)-0.5, seq_time, f'Sequential: {seq_time:.1f} ms', 
                 color='gray', fontsize=10, fontweight='bold', va='bottom', ha='right', alpha=0.8)

    # Set y-limits for broken axis
    ax1_top.set_ylim(seq_time * 0.95, seq_time * 1.05)  # Show only around the sequential time
    ax1_bottom.set_ylim(0, max(gpu_times + transfer_times + cpu_times) * 1.2)  # Show only the GPU bars

    # Hide spines between axes
    ax1_top.spines['bottom'].set_visible(False)
    ax1_bottom.spines['top'].set_visible(False)
    ax1_top.tick_params(labeltop=False)  # don't put tick labels at the top
    ax1_bottom.xaxis.tick_bottom()

    # Diagonal lines to indicate break
    d = .015  # size of diagonal lines
    kwargs = dict(transform=ax1_top.transAxes, color='k', clip_on=False)
    ax1_top.plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    ax1_top.plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal

    kwargs.update(transform=ax1_bottom.transAxes)  # switch to the bottom axes
    ax1_bottom.plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    ax1_bottom.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal

    ax1_bottom.set_ylabel('Time (ms)', fontweight='bold')
    ax1_bottom.set_xlabel('Block Size', fontweight='bold')
    ax1_bottom.set_xticks(x_time)
    ax1_bottom.set_xticklabels(x_labels_time)
    ax1_bottom.legend()
    ax1_bottom.grid(axis='y', linestyle='--', alpha=0.7)

    # Only show legend once
    ax1_top.legend().set_visible(False)

    # 2. Speedup Plot
    x_speedup = np.arange(len(bs_labels))
    bars = ax2.bar(x_speedup, speedups, width, color='#f1c40f', edgecolor='black', linewidth=1)
    
    ax2.set_ylabel('Speedup (Seq Time / GPU Total Time)', fontweight='bold')
    ax2.set_xlabel('Block Size', fontweight='bold')
    ax2.set_xticks(x_speedup)
    ax2.set_xticklabels(bs_labels)
    ax2.axhline(y=1, color='red', linestyle='--', linewidth=1, label='Baseline (1x)')
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add values on top of speedup bars
    for i, v in enumerate(speedups):
        ax2.text(i, v + 0.1, f'{v:.2f}x', ha='center', fontweight='bold', fontsize=10)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    if not os.path.exists('plots'):
        os.makedirs('plots')
    
    filename = f'plots/kmeans_{title_suffix.lower().replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300)
    print(f"Saved plot to {filename}")

def main():
    seq_time, naive_data, transpose_data = parse_results('results/run_kmeans_shared_transpose.out')
    
    if naive_data:
        generate_plots(seq_time, naive_data, 'Naive Implementation')
    
    if transpose_data:
        generate_plots(seq_time, transpose_data, 'Transpose Implementation')

if __name__ == "__main__":
    main()