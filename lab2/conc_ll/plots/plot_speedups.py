import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import argparse

def parse_conc_ll_results(filename: Path):
    """Parse a single concurrent linked list results file"""
    with open(filename, 'r') as f:
        content = f.read()

    # Serial baselines per (size, workload tuple)
    serial_pattern = r'---\s+SIZE = (\d+) - PERCENTS = ([\d\s]+) ---.*?Throughput\(Kops/sec\): ([\d.]+)'
    serial_matches = re.findall(serial_pattern, content, re.DOTALL)
    serial_baselines = {}
    for size, percents, throughput in serial_matches:
        key = (int(size), tuple(map(int, percents.split())))
        # Keep the first seen value
        if key not in serial_baselines:
            serial_baselines[key] = float(throughput)

    # Parallel blocks (one header followed by multiple impls)
    header_pattern = r'--- NTHREADS = (\d+) - SIZE = (\d+) - PERCENTS = ([\d\s]+) ---'
    parts = re.split(header_pattern, content)

    data = {}  # {(size, percents): {impl: {threads: throughput}}}
    for i in range(1, len(parts), 4):
        if i + 3 >= len(parts):
            break
        nthreads = int(parts[i])
        size = int(parts[i + 1])
        percents_str = parts[i + 2]
        block_content = parts[i + 3]
        key = (size, tuple(map(int, percents_str.split())))

        impl_pattern = r'x\.([\w]+).*?Throughput\(Kops/sec\):\s+([\d.]+)'
        impl_matches = re.findall(impl_pattern, block_content, re.DOTALL)

        for impl_name, throughput in impl_matches:
            # If this file is the nick-mod variant, rename nb_mod to nb_mod_nick
            if filename.name.endswith('_nb_mod_nick.out') and impl_name == 'nb_mod':
                impl_name = 'nb_mod_nick'
            throughput = float(throughput)
            data.setdefault(key, {}).setdefault(impl_name, {})[nthreads] = throughput

    return serial_baselines, data

def merge_results(acc_serial, acc_data, serial_add, data_add):
    # Merge serial baselines (keep existing if present)
    for k, v in serial_add.items():
        acc_serial.setdefault(k, v)
    # Merge parallel data
    for cfg, impls in data_add.items():
        acc_data.setdefault(cfg, {})
        for impl, thr_map in impls.items():
            acc_data[cfg].setdefault(impl, {})
            acc_data[cfg][impl].update(thr_map)

def plot_speedup(serial_baselines, data, output_dir):
    """Generate speedup plots for each configuration"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    impl_names = {
        'cgl': 'Coarse-Grained',
        'fgl': 'Fine-Grained',
        'lazy': 'Lazy Sync',
        'nb': 'Non-Blocking',
        'opt': 'Optimistic',
        'nb_mod': 'Non-Blocking (Modified)',
        'nb_mod_nick': 'Non-Blocking (Nick)'
    }

    for config_key, impl_data in sorted(data.items()):
        size, percents = config_key
        read, insert, delete = percents

        if config_key not in serial_baselines:
            print(f"Warning: No serial baseline for Size={size}, Workload={percents}")
            continue

        serial_throughput = serial_baselines[config_key]

        fig, ax = plt.subplots(figsize=(10, 6))

        all_threads = sorted({t for impl_results in impl_data.values() for t in impl_results.keys()})

        colors = plt.cm.tab10(np.arange(len(impl_data)) % 10)
        for idx, (impl, results) in enumerate(sorted(impl_data.items())):
            threads = []
            speedups = []
            for t in all_threads:
                if t in results:
                    threads.append(t)
                    speedups.append(results[t] / serial_throughput)
            if threads:
                label = impl_names.get(impl, impl)
                ax.plot(
                    threads, speedups, 'o-',
                    label=label, color=colors[idx % len(colors)],
                    linewidth=2, markersize=6, markeredgecolor='black', markeredgewidth=0.5
                )

        ax.set_xlabel('Number of threads', fontsize=12)
        ax.set_ylabel('Speedup (baseline: serial)', fontsize=12)
        ax.set_title(f'Speedup — Size={size}, Workload={read}/{insert}/{delete}', fontsize=13)

        # Regular (linear) scale for both axes
        # Ensure ticks align with available thread counts
        ax.set_xticks(all_threads)
        ax.set_xticklabels([str(t) for t in all_threads])

        ax.grid(True, which="both", ls="-", alpha=0.2)
        ax.grid(True, which="major", ls="-", alpha=0.5)
        
        # Legend outside
        ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, fontsize=10)
        
        plt.tight_layout()
        filename = f'speedup_size{size}_workload{read}_{insert}_{delete}.svg'
        filepath = output_dir / filename
        plt.savefig(filepath, format='svg', bbox_inches='tight')
        print(f"Saved: {filepath}")
        plt.close()

def print_summary(serial_baselines, data):
    print("\n" + "="*120)
    print("SPEEDUP SUMMARY")
    print("="*120)

    impl_names = {
        'cgl': 'Coarse-Grained',
        'fgl': 'Fine-Grained',
        'lazy': 'Lazy Sync',
        'nb': 'Non-Blocking',
        'opt': 'Optimistic',
        'nb_mod': 'NB-Modified',
        'nb_mod_nick': 'NB-Nick'
    }

    for config_key, impl_data in sorted(data.items()):
        size, percents = config_key
        read, insert, delete = percents
        serial_throughput = serial_baselines.get(config_key, 0.0)

        print(f"\nConfiguration: Size={size}, Workload={read}/{insert}/{delete}")
        print(f"Serial baseline: {serial_throughput:.2f} Kops/sec")
        print("-" * 120)

        all_threads = sorted({t for impl_results in impl_data.values() for t in impl_results.keys()})

        print(f"{'Implementation':<22}", end='')
        for t in all_threads:
            print(f"{t:>8} thr", end='')
        print()
        print("-" * 120)

        for impl in sorted(impl_data.keys()):
            results = impl_data[impl]
            impl_label = impl_names.get(impl, impl)
            print(f"{impl_label:<22}", end='')
            for t in all_threads:
                if t in results and serial_throughput > 0:
                    speedup = results[t] / serial_throughput
                    print(f"{speedup:>11.2f}x", end='')
                else:
                    print(f"{'N/A':>12}", end='')
            print()

def main():
    # File paths
    results_file = Path('/home/nicholas/parallelSystems/lab2/conc_ll/results/run_conc_ll_nb_mod.out')
    output_dir = Path('/home/nicholas/parallelSystems/lab2/conc_ll/plots')
    
    # Parse results
    print("Parsing results...")
    serial_baselines, data = parse_conc_ll_results(results_file)
    
    print(f"\nFound {len(serial_baselines)} serial baselines")
    print(f"Found {len(data)} parallel configurations")

    # Report implementations found
    impl_counts = {}
    for cfg_data in data.values():
        for impl in cfg_data.keys():
            impl_counts[impl] = impl_counts.get(impl, 0) + 1
    print("\nImplementations found:")
    for impl, count in sorted(impl_counts.items()):
        print(f"  {impl}: {count} configurations")

    output_dir = Path('/home/nicholas/parallelSystems/lab2/conc_ll/plots')

    print("\nGenerating plots...")
    plot_speedup(serial_baselines, data, output_dir)

    print_summary(serial_baselines, data)

    print("\n" + "="*120)
    print("Done!")

if __name__ == "__main__":
    main()
