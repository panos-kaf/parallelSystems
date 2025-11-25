import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Read sequential baseline
def parse_sequential(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
            match = re.search(r'nloops\s+=\s+\d+\s+\(total\s+=\s+([\d.]+)s\)', content)
            if match:
                return float(match.group(1))
    except FileNotFoundError:
        print(f"Warning: {filename} not found")
    return None

# Parse parallel execution times
def parse_parallel(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Warning: {filename} not found")
        return {}
    
    results = {}
    # Find all thread configurations
    pattern = r'--- nthreads = (\d+) ---.*?nloops\s+=\s+\d+\s+\(total\s+=\s+([\d.]+)s\)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for threads, time in matches:
        results[int(threads)] = float(time)
    
    return results

# Setup paths
results_dir = Path('/home/nicholas/parallelSystems/lab2/kmeans_locks/results')
plots_dir = Path('/home/nicholas/parallelSystems/lab2/kmeans_locks/plots')
seq_file = results_dir / 'kmeans_seq.out'

# Define lock implementations
lock_implementations = {
    'Sequential': None,  # Added sequential as first entry
    'Naive': 'kmeans_omp_naive.out',
    'Critical': 'kmeans_omp_critical.out',
    'Array Lock': 'kmeans_omp_array_lock.out',
    'CLH Lock': 'kmeans_omp_clh_lock.out',
    'TAS Lock': 'kmeans_omp_tas_lock.out',
    'TTAS Lock': 'kmeans_omp_ttas_lock.out',
    'Mutex Lock': 'kmeans_omp_pthread_mutex_lock.out',
    'Spin Lock': 'kmeans_omp_pthread_spin_lock.out',
}

# Parse sequential time
seq_time = parse_sequential(seq_file)
if seq_time is None:
    print("Error: Could not parse sequential time. Exiting.")
    exit(1)

print(f"Sequential time: {seq_time:.4f}s\n")

# Parse all parallel implementations
all_data = {}
for name, filename in lock_implementations.items():
    if name == 'Sequential':
        # Skip parsing for sequential, we'll handle it separately
        continue
    filepath = results_dir / filename
    data = parse_parallel(filepath)
    if data:
        all_data[name] = data
        print(f"{name}: {len(data)} thread configurations found")

if not all_data:
    print("Error: No parallel data found. Exiting.")
    exit(1)

# Get thread counts (assuming all implementations use same thread counts)
thread_counts = sorted(list(all_data[list(all_data.keys())[0]].keys()))
print(f"\nThread counts: {thread_counts}")

# Create plots directory if it doesn't exist
plots_dir.mkdir(exist_ok=True)

# Use colors from tab10 colormap
colors = plt.cm.tab10(range(len(lock_implementations)))

# --- Plot 1: Execution Time Comparison ---
fig1, ax1 = plt.subplots(figsize=(12, 6))

# Create x positions with equal spacing
x_positions = list(range(len(thread_counts)))
x_labels = ['seq'] + [str(t) for t in thread_counts[1:]] if len(thread_counts) > 0 else []
bar_width = 0.8 / len(lock_implementations)

# Plot sequential first
times_seq = [seq_time] * len(thread_counts)
x_pos_seq = [i for i in x_positions]
ax1.bar(x_pos_seq, times_seq, width=bar_width, label='Sequential', 
        color=colors[0], edgecolor='black', linewidth=0.5)

# Plot parallel implementations
for idx, (name, data) in enumerate(all_data.items(), start=1):
    times = [data.get(t, 0) for t in thread_counts]
    x_pos = [i + idx * bar_width for i in x_positions]
    ax1.bar(x_pos, times, width=bar_width, label=name, 
            color=colors[idx], edgecolor='black', linewidth=0.5)

ax1.set_xlabel('Number of threads')
ax1.set_ylabel('Per-loop time (s)')
ax1.set_title('Execution time — all implementations')
ax1.set_xticks([i + bar_width * (len(lock_implementations) - 1) / 2 for i in x_positions])
ax1.set_xticklabels([str(t) for t in thread_counts])
ax1.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
ax1.grid(axis='y', linestyle=':', alpha=0.6)
ax1.set_axisbelow(True)

plt.tight_layout()
output_file1 = plots_dir / 'execution_time_comparison.svg'
plt.savefig(output_file1, format='svg', bbox_inches='tight')
print(f"\n✓ Execution time plot saved as '{output_file1}'")
plt.close()

# --- Plot 2: Speedup Comparison ---
fig2, ax2 = plt.subplots(figsize=(12, 6))

# Plot sequential speedup (always 1.0)
speedups_seq = [1.0] * len(thread_counts)
x_pos_seq = [i for i in x_positions]
ax2.bar(x_pos_seq, speedups_seq, width=bar_width, label='Sequential',
        color=colors[0], edgecolor='black', linewidth=0.5)

# Plot parallel implementations speedup
for idx, (name, data) in enumerate(all_data.items(), start=1):
    speedups = [seq_time / data.get(t, seq_time) for t in thread_counts]
    x_pos = [i + idx * bar_width for i in x_positions]
    ax2.bar(x_pos, speedups, width=bar_width, label=name,
            color=colors[idx], edgecolor='black', linewidth=0.5)

ax2.set_xlabel('Number of threads')
ax2.set_ylabel('Speedup (baseline: sequential)')
ax2.set_title('Speedup — all implementations')
ax2.set_xticks([i + bar_width * (len(lock_implementations) - 1) / 2 for i in x_positions])
ax2.set_xticklabels([str(t) for t in thread_counts])
ax2.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
ax2.grid(axis='y', linestyle=':', alpha=0.6)
ax2.set_axisbelow(True)

plt.tight_layout()
output_file2 = plots_dir / 'speedup_comparison.svg'
plt.savefig(output_file2, format='svg', bbox_inches='tight')
print(f"✓ Speedup plot saved as '{output_file2}'")
plt.close()

# --- Generate summary statistics table ---
print("\n" + "="*100)
print("SPEEDUP SUMMARY TABLE")
print("="*100)
print(f"{'Lock Type':<22}", end='')
for t in thread_counts:
    print(f"{t:>10} threads", end='')
print()
print("-"*100)

# Print sequential first
print(f"{'Sequential':<22}", end='')
for t in thread_counts:
    print(f"{1.0:>17.2f}x", end='')
print()

for name, data in all_data.items():
    print(f"{name:<22}", end='')
    for t in thread_counts:
        if t in data:
            speedup = seq_time / data[t]
            print(f"{speedup:>17.2f}x", end='')
        else:
            print(f"{'N/A':>17}", end='')
    print()

print("\n" + "="*100)
print("EXECUTION TIME SUMMARY TABLE (seconds)")
print("="*100)
print(f"{'Lock Type':<22}", end='')
for t in thread_counts:
    print(f"{t:>10} threads", end='')
print()
print("-"*100)

print(f"{'Sequential':<22}{seq_time:>17.4f}")
for name, data in all_data.items():
    print(f"{name:<22}", end='')
    for t in thread_counts:
        if t in data:
            print(f"{data[t]:>17.4f}", end='')
        else:
            print(f"{'N/A':>17}", end='')
    print()

# --- Best performance analysis ---
print("\n" + "="*100)
print("BEST PERFORMING LOCK PER THREAD COUNT")
print("="*100)
for t in thread_counts:
    valid_locks = {name: data[t] for name, data in all_data.items() if t in data}
    if valid_locks:
        best_name = min(valid_locks.keys(), key=lambda k: valid_locks[k])
        best_time = valid_locks[best_name]
        best_speedup = seq_time / best_time
        print(f"{t:>3} threads: {best_name:<22} Time: {best_time:>8.4f}s  Speedup: {best_speedup:>6.2f}x")

# --- Efficiency Analysis ---
print("\n" + "="*100)
print("PARALLEL EFFICIENCY (Speedup / Number of Threads)")
print("="*100)
print(f"{'Lock Type':<22}", end='')
for t in thread_counts:
    print(f"{t:>10} threads", end='')
print()
print("-"*100)

# Print sequential efficiency (100% by definition for 1 thread)
print(f"{'Sequential':<22}", end='')
for t in thread_counts:
    efficiency = (1.0 / t) * 100
    print(f"{efficiency:>16.1f}%", end='')
print()

for name, data in all_data.items():
    print(f"{name:<22}", end='')
    for t in thread_counts:
        if t in data:
            speedup = seq_time / data[t]
            efficiency = (speedup / t) * 100
            print(f"{efficiency:>16.1f}%", end='')
        else:
            print(f"{'N/A':>17}", end='')
    print()

print("\n" + "="*100)