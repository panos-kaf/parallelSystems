import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def parse_conc_ll_results(filename):
    """Parse the concurrent linked list results file"""
    with open(filename, 'r') as f:
        content = f.read()
    
    # Parse serial baseline for each configuration (Size + Workload)
    # Pattern looks for: --- SIZE = 1024 - PERCENTS = 100 0 0 --- ... Throughput: 1569.58
    serial_pattern = r'---\s+SIZE = (\d+) - PERCENTS = ([\d\s]+) ---.*?Throughput\(Kops/sec\): ([\d.]+)'
    serial_matches = re.findall(serial_pattern, content, re.DOTALL)
    
    serial_baselines = {}
    for size, percents, throughput in serial_matches:
        # Create a specific key for each configuration
        key = (int(size), tuple(map(int, percents.split())))
        # Only store if not already present (to avoid overwriting if duplicates exist, though unlikely for serial)
        if key not in serial_baselines:
            serial_baselines[key] = float(throughput)
            
    # Parse parallel results
    # We split the file by the configuration header to handle multiple implementations per block correctly
    # The split will return: [preamble, thread1, size1, perc1, block1, thread2, size2, perc2, block2, ...]
    header_pattern = r'--- NTHREADS = (\d+) - SIZE = (\d+) - PERCENTS = ([\d\s]+) ---'
    parts = re.split(header_pattern, content)
    
    # Organize data: {(size, percents): {impl: {threads: throughput}}}
    data = {}
    
    # Iterate over the parts in steps of 4 (skipping the preamble at index 0)
    for i in range(1, len(parts), 4):
        if i + 3 >= len(parts):
            break
            
        nthreads = int(parts[i])
        size = int(parts[i+1])
        percents_str = parts[i+2]
        block_content = parts[i+3]
        
        key = (size, tuple(map(int, percents_str.split())))
        
        # Find all implementations within this specific block
        # Pattern looks for "x.implname" followed eventually by "Throughput..."
        impl_pattern = r'x\.([\w]+).*?Throughput\(Kops/sec\):\s+([\d.]+)'
        impl_matches = re.findall(impl_pattern, block_content, re.DOTALL)
        
        for impl_name, throughput in impl_matches:
            throughput = float(throughput)
            
            if key not in data:
                data[key] = {}
            if impl_name not in data[key]:
                data[key][impl_name] = {}
            data[key][impl_name][nthreads] = throughput
    
    return serial_baselines, data

def plot_speedup(serial_baselines, data, output_dir):
    """Generate speedup plots for each configuration"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Implementation names mapping
    impl_names = {
        'cgl': 'Coarse-Grained',
        'fgl': 'Fine-Grained',
        'lazy': 'Lazy Sync',
        'nb': 'Non-Blocking',
        'opt': 'Optimistic',
        'nb_mod': 'Non-Blocking (Modified)'
    }
    
    for config_key, impl_data in sorted(data.items()):
        size, percents = config_key
        read, insert, delete = percents
        
        # Get specific serial baseline for this configuration
        if config_key not in serial_baselines:
            print(f"Warning: No serial baseline for Size={size}, Workload={percents}")
            continue
        
        serial_throughput = serial_baselines[config_key]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Get all thread counts (sorted)
        all_threads = sorted(set(
            threads 
            for impl_results in impl_data.values() 
            for threads in impl_results.keys()
        ))
        
        # Plot each implementation
        colors = plt.cm.tab10(range(len(impl_data)))
        for idx, (impl, results) in enumerate(sorted(impl_data.items())):
            threads = []
            speedups = []
            
            for t in all_threads:
                if t in results:
                    threads.append(t)
                    # Speedup = parallel_throughput / serial_throughput
                    speedup = results[t] / serial_throughput
                    speedups.append(speedup)
            
            if threads:
                label = impl_names.get(impl, impl)
                ax.plot(threads, speedups, 'o-', label=label, 
                       color=colors[idx], linewidth=2, markersize=6,
                       markeredgecolor='black', markeredgewidth=0.5)
        
        # Formatting
        ax.set_xlabel('Number of threads', fontsize=12)
        ax.set_ylabel('Speedup (baseline: serial)', fontsize=12)
        ax.set_title(f'Speedup — Size={size}, Workload={read}/{insert}/{delete}', 
                    fontsize=13)
        
        # Regular scale for both axes
        ax.set_xscale('log', base=2)
        # ax.set_yscale('log', base=2)
        
        # Set ticks
        ax.set_xticks(all_threads)
        ax.set_xticklabels([str(t) for t in all_threads])
        
        # Add grid
        ax.grid(True, which="both", ls="-", alpha=0.2)
        ax.grid(True, which="major", ls="-", alpha=0.5)
        
        # Legend outside
        ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, fontsize=10)
        
        plt.tight_layout()
        
        # Save figure
        filename = f'speedup_size{size}_workload{read}_{insert}_{delete}.svg'
        filepath = output_dir / filename
        plt.savefig(filepath, format='svg', bbox_inches='tight')
        print(f"Saved: {filepath}")
        plt.close()

def print_summary(serial_baselines, data):
    """Print summary statistics"""
    print("\n" + "="*120)
    print("SPEEDUP SUMMARY")
    print("="*120)
    
    impl_names = {
        'cgl': 'Coarse-Grained',
        'fgl': 'Fine-Grained',
        'lazy': 'Lazy Sync',
        'nb': 'Non-Blocking',
        'opt': 'Optimistic',
        'nb_mod': 'NB-Modified'
    }
    
    for config_key, impl_data in sorted(data.items()):
        size, percents = config_key
        read, insert, delete = percents
        serial_throughput = serial_baselines.get(config_key, 0)
        
        print(f"\nConfiguration: Size={size}, Workload={read}/{insert}/{delete}")
        print(f"Serial baseline: {serial_throughput:.2f} Kops/sec")
        print("-" * 120)
        
        # Get thread counts
        all_threads = sorted(set(
            threads 
            for impl_results in impl_data.values() 
            for threads in impl_results.keys()
        ))
        
        # Print header
        print(f"{'Implementation':<22}", end='')
        for t in all_threads:
            print(f"{t:>8} thr", end='')
        print()
        print("-" * 120)
        
        # Print each implementation
        for impl in sorted(impl_data.keys()):
            results = impl_data[impl]
            impl_label = impl_names.get(impl, impl)
            print(f"{impl_label:<22}", end='')
            for t in all_threads:
                if t in results:
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
    
    # Print implementation counts
    impl_counts = {}
    for config_data in data.values():
        for impl in config_data.keys():
            impl_counts[impl] = impl_counts.get(impl, 0) + 1
    
    print(f"\nImplementations found:")
    for impl, count in sorted(impl_counts.items()):
        print(f"  {impl}: {count} configurations")
    
    # Generate plots
    print("\nGenerating plots...")
    plot_speedup(serial_baselines, data, output_dir)
    
    # Print summary
    print_summary(serial_baselines, data)
    
    print("\n" + "="*120)
    print("Done!")

if __name__ == "__main__":
    main()
