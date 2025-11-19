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
    metadata = {}  # Store dataset metadata per label
    sequential_data = {}  # Store sequential times per config
    
    for f in files:
        try:
            entries = parse_results(f)
        except Exception as e:
            print(f"Failed to parse {f}: {e}")
            continue
        if not entries:
            continue
        label = label_for_path(f, results_root)
        
        # Check if this is a sequential run
        is_sequential = 'sequential' in label.lower()
        
        for e in entries:
            t = e.get("numThreads")
            time = e.get("per_loop_time_s")
            
            # Create config key
            config_key = (
                e.get('dataset_size_MB'),
                e.get('numCoords'),
                e.get('numClusters')
            )
            
            # Handle sequential runs (no numThreads)
            if is_sequential and time is not None and t is None:
                sequential_data[config_key] = time
                if label not in metadata:
                    metadata[label] = {
                        'dataset_size_MB': e.get('dataset_size_MB'),
                        'numCoords': e.get('numCoords'),
                        'numClusters': e.get('numClusters'),
                        'numObjs': e.get('numObjs')
                    }
                continue
            
            if t is None or time is None:
                continue
            if t in data[label]:
                data[label][t] = min(data[label][t], time)
            else:
                data[label][t] = time
            raw_entries[label].append((t, time))
            # Store metadata (same for all runs of the same label)
            if label not in metadata:
                metadata[label] = {
                    'dataset_size_MB': e.get('dataset_size_MB'),
                    'numCoords': e.get('numCoords'),
                    'numClusters': e.get('numClusters'),
                    'numObjs': e.get('numObjs')
                }
    return data, raw_entries, metadata, sequential_data


def plot_per_implementation(data, out_dir: str, metadata: dict, sequential_data: dict):
    os.makedirs(out_dir, exist_ok=True)
    created = []
    canonical = [1, 2, 4, 8, 16, 32, 64]

    for label, thread_map in data.items():
        if not thread_map:
            continue
        ordered = OrderedDict(sorted(thread_map.items()))
        
        # Get config key for this label
        meta = metadata.get(label, {})
        config_key = (
            meta.get('dataset_size_MB'),
            meta.get('numCoords'),
            meta.get('numClusters')
        )
        
        # Get sequential baseline for this config
        seq_time = sequential_data.get(config_key)
        if seq_time is None:
            print(f"Warning: No sequential baseline found for {label}, skipping...")
            continue
        
        # Build data with sequential as first entry
        threads = ['seq'] + [t for t in canonical if t in ordered]
        times = [seq_time] + [ordered[t] for t in canonical if t in ordered]

        if len(times) <= 1:  # Only sequential, no parallel data
            continue

        # Use sequential time as baseline for speedup
        baseline = seq_time
        speedups = [baseline / t for t in times]

        safe_label = label.replace("/", "_").replace(" ", "_")

        # Create x positions with equal spacing
        x_positions = list(range(len(threads)))
        x_labels = [str(t) for t in threads]

        config_text = ""
        if meta.get('dataset_size_MB') is not None:
            config_text = f"Dataset: {meta['dataset_size_MB']:.2f} MB"
        if meta.get('numCoords') is not None:
            config_text += f"  |  Coordinates: {meta['numCoords']}"
        if meta.get('numClusters') is not None:
            config_text += f"  |  Clusters: {meta['numClusters']}"

        # Execution time bar plot
        plt.figure(figsize=(8, 4.5))
        plt.bar(x_positions, times, color='red', edgecolor='black', width=0.6)
        plt.xlabel("Number of threads")
        plt.ylabel("Per-loop time (s)")
        plt.title(f"Execution time — {label}")
        plt.grid(axis='y', linestyle=':', alpha=0.6)
        plt.xticks(x_positions, x_labels)
        # Add configuration text below the plot
        if config_text:
            plt.subplots_adjust(bottom=0.15)
            plt.figtext(0.5, 0.02, config_text, ha='center', fontsize=9, style='italic')
        time_file = os.path.join(out_dir, f"time_{safe_label}.png")
        plt.savefig(time_file, bbox_inches="tight")
        plt.close()

        # Speedup bar plot
        plt.figure(figsize=(8, 4.5))
        plt.bar(x_positions, speedups, color='lightblue', edgecolor='black', width=0.6)
        plt.xlabel("Number of threads")
        plt.ylabel(f"Speedup (baseline: sequential)")
        plt.title(f"Speedup — {label}")
        plt.grid(axis='y', linestyle=':', alpha=0.6)
        plt.xticks(x_positions, x_labels)
        # Add configuration text below the plot
        if config_text:
            plt.subplots_adjust(bottom=0.15)
            plt.figtext(0.5, 0.02, config_text, ha='center', fontsize=9, style='italic')
        speed_file = os.path.join(out_dir, f"speedup_{safe_label}.png")
        plt.savefig(speed_file, bbox_inches="tight")
        plt.close()

        created.extend([time_file, speed_file])
    return created


def plot_combined(data, out_dir: str, metadata: dict, sequential_data: dict):
    os.makedirs(out_dir, exist_ok=True)
    canonical = [1, 2, 4, 8, 16, 32, 64]
    created = []
    
    # Group implementations by their dataset configuration
    config_groups = defaultdict(list)
    for label, thread_map in data.items():
        if not thread_map:
            continue
        meta = metadata.get(label, {})
        # Create a config key from dataset parameters
        config_key = (
            meta.get('dataset_size_MB'),
            meta.get('numCoords'),
            meta.get('numClusters')
        )
        config_groups[config_key].append(label)
    
    # Create combined plots for each unique configuration
    for config_key, labels in config_groups.items():
        if len(labels) < 2:  # Skip if only one implementation with this config
            continue
        
        # Get sequential baseline for this config
        seq_time = sequential_data.get(config_key)
        if seq_time is None:
            print(f"Warning: No sequential baseline for config {config_key}, skipping combined plot...")
            continue
            
        dataset_size, num_coords, num_clusters = config_key
        
        # Create config text and safe filename
        config_text = ""
        config_suffix = ""
        if dataset_size is not None:
            config_text = f"Dataset: {dataset_size:.2f} MB"
            config_suffix += f"_{int(dataset_size)}MB"
        if num_coords is not None:
            config_text += f"  |  Coordinates: {num_coords}"
            config_suffix += f"_{num_coords}coords"
        if num_clusters is not None:
            config_text += f"  |  Clusters: {num_clusters}"
            config_suffix += f"_{num_clusters}clusters"
        
        # Add 'seq' as first position
        x_positions = list(range(len(canonical) + 1))
        x_labels = ['seq'] + [str(t) for t in canonical]
        
        # Combined execution time bar plot
        plt.figure(figsize=(12, 6))
        bar_width = 0.8 / len(labels)
        colors = plt.cm.tab10(range(len(labels)))
        
        for idx, label in enumerate(labels):
            thread_map = data[label]
            ordered = OrderedDict(sorted(thread_map.items()))
            # Start with sequential time
            times = [seq_time]
            x_pos = [0 + idx * bar_width]
            for i, t in enumerate(canonical):
                if t in ordered:
                    times.append(ordered[t])
                    x_pos.append((i + 1) + idx * bar_width)
            
            plt.bar(x_pos, times, width=bar_width, label=label, 
                    edgecolor='black', linewidth=0.5, color=colors[idx])
        
        plt.xlabel("Number of threads")
        plt.ylabel("Per-loop time (s)")
        plt.title("Execution time — all implementations")
        plt.grid(axis='y', linestyle=':', alpha=0.6)
        plt.xticks([i + bar_width * (len(labels) - 1) / 2 for i in x_positions], x_labels)
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        if config_text:
            plt.subplots_adjust(bottom=0.12)
            plt.figtext(0.45, 0.02, config_text, ha='center', fontsize=9, style='italic')
        combined_time = os.path.join(out_dir, f"combined_time{config_suffix}.png")
        plt.savefig(combined_time, bbox_inches="tight")
        plt.close()
        created.append(combined_time)
        
        # Combined speedup bar plot
        plt.figure(figsize=(12, 6))
        baseline = seq_time
        
        for idx, label in enumerate(labels):
            thread_map = data[label]
            ordered = OrderedDict(sorted(thread_map.items()))
            
            # Start with sequential speedup (1.0)
            speedups = [baseline / seq_time]
            x_pos = [0 + idx * bar_width]
            for i, t in enumerate(canonical):
                if t in ordered:
                    speedups.append(baseline / ordered[t])
                    x_pos.append((i + 1) + idx * bar_width)
            
            plt.bar(x_pos, speedups, width=bar_width, label=label,
                    edgecolor='black', linewidth=0.5, color=colors[idx])
        
        plt.xlabel("Number of threads")
        plt.ylabel("Speedup (baseline: sequential)")
        plt.title("Speedup — all implementations")
        plt.grid(axis='y', linestyle=':', alpha=0.6)
        plt.xticks([i + bar_width * (len(labels) - 1) / 2 for i in x_positions], x_labels)
        plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        if config_text:
            plt.subplots_adjust(bottom=0.12)
            plt.figtext(0.45, 0.02, config_text, ha='center', fontsize=9, style='italic')
        combined_speed = os.path.join(out_dir, f"combined_speedup{config_suffix}.png")
        plt.savefig(combined_speed, bbox_inches="tight")
        plt.close()
        created.append(combined_speed)
    
    return created


def main():
    results_root = os.path.abspath(os.path.join(HERE, "..", "results"))
    files = find_result_files(results_root)
    if not files:
        print("No result files found under", results_root)
        return
    print(f"Found {len(files)} result files")
    data, _, metadata, sequential_data = aggregate_runs(files, results_root)
    
    print(f"Found {len(sequential_data)} sequential baseline(s):")
    for config_key, time in sequential_data.items():
        print(f"  Config {config_key}: {time:.4f}s")
    
    out_dir = os.path.join(HERE, "..", "diagrams")
    created = plot_per_implementation(data, out_dir, metadata, sequential_data)
    created += plot_combined(data, out_dir, metadata, sequential_data)
    print("Created plots:")
    for c in created:
        print(" -", c)
if __name__ == "__main__":
    main()