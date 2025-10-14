import re
from collections import defaultdict
from matplotlib import pyplot as plt
import os
import sys

if len(sys.argv) < 2:
    print("Usage: python diagram.py <input_file>")
    sys.exit(1)

input_file = sys.argv[1]

with open (input_file, 'r') as file:
    input_data = file.read()

number_of_threads = [1, 2, 4, 6, 8]

# Dictionary to store results
results = defaultdict(list)

# Regex to extract size and time
pattern = re.compile(r"GameOfLife: Size (\d+) Steps \d+ Time ([\d.]+)")

# Process each line
for line in input_data.splitlines():
    match = pattern.match(line)
    if match:
        size = int(match.group(1))
        time = float(match.group(2))
        results[size].append(time)

# Convert defaultdict to regular dict before printing
times = dict(results)

speedup = {}
for size, time_list in times.items():
    speedup[size] = []
    for i in range(0, len(time_list)):
        speedup[size].append(round(time_list[0] / time_list[i], 4))

# Display the result
print(times)
print(speedup)


def plot_times(times):
    fig, axs = plt.subplots(1, 3, figsize=(18, 6), sharey=False)
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray']
    sizes = sorted(times.keys())
    sizes_per_subplot = (len(sizes) + 2) // 3  # Divide sizes roughly equally

    for i in range(3):
        ax = axs[i]
        start = i * sizes_per_subplot
        end = min((i + 1) * sizes_per_subplot, len(sizes))
        for j, size in enumerate(sizes[start:end]):
            color = colors[i % len(colors)]
            ax.plot(number_of_threads, times[size], marker='o', label=f'Size {size}', color=color)
        ax.set_xlabel('Number of Threads')
        if i == 0:
            ax.set_ylabel('Time (seconds)')
        ax.set_title(f'Execution Time (Sizes {", ".join(str(s) for s in sizes[start:end])})')
        ax.legend()
        ax.grid(True, which="both", ls="--")
        y_maxs = [max(times[size]) for size in sizes[start:end]]
        if y_maxs:
            ax.set_ylim(0, max(y_maxs) * 1.05)

    plt.suptitle('Execution Time vs Number of Threads (Subdiagrams)')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(f"times_{os.path.splitext(os.path.basename(input_file))[0]}.png")
    plt.show()

def plot_speedup(speedup):
    plt.figure(figsize=(10, 6))
    for size, speedup_list in speedup.items():
        plt.plot(number_of_threads, speedup_list, marker='o', label=f'Size {size}')
    plt.xlabel('Number of Threads')
    plt.ylabel('Speedup')
    plt.title('Speedup vs Number of Threads')
    plt.legend()
    plt.grid(True)
    plt.savefig(f"speedup_{os.path.splitext(os.path.basename(input_file))[0]}.png")
    plt.show()

plot_times(times)
plot_speedup(speedup)