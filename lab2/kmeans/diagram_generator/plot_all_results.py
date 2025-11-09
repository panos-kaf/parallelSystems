import os
import glob
import sys
from collections import defaultdict, OrderedDict
from typing import List

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)

from diagram_gen import parse_results

import matplotlib.pyplot as plt


def find_result_files(results_root: str) -> List[str]:
    patterns = [os.path.join(results_root, "**", "run_*.out"), os.path.join(results_root, "**", "run_*.err")]
    files = []
    for p in patterns:
        files.extend(glob.glob(p, recursive=True))
    files = sorted(files)
    return files
import os
import glob
import sys
from collections import defaultdict, OrderedDict
from typing import List

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)

from diagram_gen import parse_results
from matplotlib.ticker import FuncFormatter

import matplotlib.pyplot as plt


def find_result_files(results_root: str) -> List[str]:
    patterns = [os.path.join(results_root, "**", "run_*.out"), os.path.join(results_root, "**", "run_*.err")]
    files = []
    for p in patterns:
        files.extend(glob.glob(p, recursive=True))
    files = sorted(files)
    return files


def label_for_path(filepath: str, results_root: str) -> str:
    rel = os.path.relpath(filepath, results_root)
    parts = rel.split(os.sep)
    if len(parts) == 1:
        name = os.path.splitext(parts[0])[0]
        return name
    if len(parts) >= 3:
        return f"{parts[0]} - {parts[1]}"
    return parts[0]


def aggregate_runs(files: List[str], results_root: str):
    data = defaultdict(dict)
    raw_entries = defaultdict(list)
    for f in files:
        try:
            entries = parse_results(f)
        except Exception as e:
            print(f"Failed to parse {f}: {e}")
            continue
        if not entries:
            continue
        label = label_for_path(f, results_root)
        for e in entries:
            t = e.get("numThreads")
            time = e.get("per_loop_time_s")
            if t is None or time is None:
                continue
            if t in data[label]:
                data[label][t] = min(data[label][t], time)
            else:
                data[label][t] = time
            raw_entries[label].append((t, time))
    return data, raw_entries


def plot_per_implementation(data, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    created = []
    canonical = [1, 2, 4, 8, 16, 32, 64]

    def int_formatter(x, pos):
        return str(int(round(x))) if abs(x - round(x)) < 1e-6 else str(x)

    for label, thread_map in data.items():
        if not thread_map:
            continue
        ordered = OrderedDict(sorted(thread_map.items()))
        threads = [t for t in canonical if t in ordered]
        times = [ordered[t] for t in threads]

        if not threads:
            continue

        if 1 in ordered:
            baseline = ordered[1]
            baseline_thread = 1
        else:
            baseline_thread = threads[0]
            baseline = ordered[baseline_thread]

        speedups = [baseline / t for t in times]

        safe_label = label.replace("/", "_").replace(" ", "_")

        # Execution time
        plt.figure(figsize=(8, 4.5))
        plt.plot(threads, times, marker="o", linewidth=2)
        plt.xlabel("Number of threads")
        plt.ylabel("Per-loop time (s)")
        plt.title(f"Execution time — {label}")
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.xscale('log', base=2)
        plt.xticks(canonical)
        plt.xlim(1, 64)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(FuncFormatter(int_formatter))
        time_file = os.path.join(out_dir, f"time_{safe_label}.png")
        plt.savefig(time_file, bbox_inches="tight")
        plt.close()

        # Speedup
        plt.figure(figsize=(8, 4.5))
        plt.plot(threads, speedups, marker="o", linewidth=2)
        plt.xlabel("Number of threads")
        plt.ylabel(f"Speedup (baseline: {baseline_thread} thread)")
        plt.title(f"Speedup — {label}")
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.xscale('log', base=2)
        plt.xticks(canonical)
        plt.xlim(1, 64)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(FuncFormatter(int_formatter))
        speed_file = os.path.join(out_dir, f"speedup_{safe_label}.png")
        plt.savefig(speed_file, bbox_inches="tight")
        plt.close()

        created.extend([time_file, speed_file])
    return created


def plot_combined(data, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    canonical = [1, 2, 4, 8, 16, 32, 64]

    def int_formatter(x, pos):
        return str(int(round(x))) if abs(x - round(x)) < 1e-6 else str(x)

    plt.figure(figsize=(12, 6))
    for label, thread_map in data.items():
        if not thread_map:
            continue
        ordered = OrderedDict(sorted(thread_map.items()))
        threads = [t for t in canonical if t in ordered]
        times = [ordered[t] for t in threads]
        plt.plot(threads, times, marker="o", linewidth=1.5, markersize=6, label=label)
    plt.xlabel("Number of threads")
    plt.ylabel("Per-loop time (s)")
    plt.title("Execution time — all implementations")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.xscale('log', base=2)
    plt.xticks(canonical)
    plt.xlim(1, 64)
    ax = plt.gca()
    ax.xaxis.set_major_formatter(FuncFormatter(int_formatter))
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
    combined_time = os.path.join(out_dir, "combined_time.png")
    plt.savefig(combined_time, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(12, 6))
    for label, thread_map in data.items():
        if not thread_map:
            continue
        ordered = OrderedDict(sorted(thread_map.items()))
        threads = [t for t in canonical if t in ordered]
        times = [ordered[t] for t in threads]
        if 1 in ordered:
            baseline = ordered[1]
        else:
            baseline = times[0]
        speedups = [baseline / t for t in times]
        plt.plot(threads, speedups, marker="o", linewidth=1.5, markersize=6, label=label)
    plt.xlabel("Number of threads")
    plt.ylabel("Speedup")
    plt.title("Speedup — all implementations")
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.xscale('log', base=2)
    plt.xticks(canonical)
    plt.xlim(1, 64)
    ax = plt.gca()
    ax.xaxis.set_major_formatter(FuncFormatter(int_formatter))
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
    combined_speed = os.path.join(out_dir, "combined_speedup.png")
    plt.savefig(combined_speed, bbox_inches="tight")
    plt.close()

    return [combined_time, combined_speed]


def main():
    results_root = os.path.abspath(os.path.join(HERE, "..", "results"))
    files = find_result_files(results_root)
    if not files:
        print("No result files found under", results_root)
        return
    print(f"Found {len(files)} result files")
    data, _ = aggregate_runs(files, results_root)
    out_dir = os.path.join(HERE, "..", "diagrams")
    created = plot_per_implementation(data, out_dir)
    created += plot_combined(data, out_dir)
    print("Created plots:")
    for c in created:
        print(" -", c)
if __name__ == "__main__":
    main()