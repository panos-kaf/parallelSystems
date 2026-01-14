import matplotlib.pyplot as plt
import numpy as np
import re
import os
import sys
import argparse

def parse_results(filename):
    """Parse results file and extract sequential time and implementation data."""
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        return 0, {}, 0

    with open(filename, 'r') as f:
        content = f.read()

    # Extract Sequential Time
    seq_section = re.search(r'Sequential Kmeans.*?t_loop_avg = ([\d.]+) ms', content, re.DOTALL)
    seq_time = float(seq_section.group(1)) if seq_section else 0

    # Extract number of coordinates
    coords_match = re.search(r'numCoords = (\d+)', content)
    num_coords = int(coords_match.group(1)) if coords_match else 0

    # Split by separator
    sections = content.split('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

    impl_data = {}

    for section in sections:
        if 'block_size' not in section:
            continue
        
        try:
            bs = int(re.search(r'block_size = (\d+)', section).group(1))
            t_loop_avg = float(re.search(r't_loop_avg = ([\d.]+) ms', section).group(1))
            
            # Determine implementation type from the section header
            impl_match = re.search(r'\|-+([^|]+?)\s*Kmeans[^|]*\|', section)
            if not impl_match:
                continue
            
            impl_name = impl_match.group(1).strip()
            # Clean up implementation name
            impl_name = impl_name.replace('-', '').strip()
            
            if impl_name not in impl_data:
                impl_data[impl_name] = []
            
            impl_data[impl_name].append({'bs': bs, 'time': t_loop_avg})
            
        except (AttributeError, ValueError):
            continue

    return seq_time, impl_data, num_coords

def filter_implementations(impl_data, include_impls):
    """Filter implementations based on include list."""
    if not include_impls:
        return impl_data
    
    # Create mapping for case-insensitive matching
    impl_mapping = {
        'naive': ['Naive GPU', 'Naive'],
        'transpose': ['Transpose GPU', 'Transpose'],
        'shared': ['Shared GPU', 'Shared'],
        'fulloffload': ['Fulloffload GPU', 'Fulloffload', 'Full-offload'],
        'all': None  # Special case to include all
    }
    
    # Build list of implementations to include
    impls_to_include = set()
    for impl in include_impls:
        impl_lower = impl.lower()
        if impl_lower == 'all':
            return impl_data
        if impl_lower in impl_mapping:
            for variant in impl_mapping[impl_lower]:
                if variant in impl_data:
                    impls_to_include.add(variant)
    
    # Filter the data
    filtered_data = {k: v for k, v in impl_data.items() if k in impls_to_include}
    return filtered_data

def plot_all_speedups(seq_time, impl_data, num_coords, filename):
    """Create bar plot comparing speedups of all implementations."""
    if not impl_data:
        print("No data to plot.")
        return

    # Sort each implementation's data by block size
    for impl_name in impl_data:
        impl_data[impl_name].sort(key=lambda x: x['bs'])
    
    # Get all block sizes (assuming all implementations have same block sizes)
    block_sizes = [d['bs'] for d in list(impl_data.values())[0]]
    
    # Create plot
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Colors for each implementation
    colors = {
        'Naive GPU': '#e74c3c',
        'Transpose GPU': '#3498db',
        'Shared GPU': '#2ecc71',
        'Fulloffload GPU': '#FFD700',
        'Naive': '#e74c3c',
        'Transpose': '#3498db',
        'Shared': '#2ecc71',
        'Fulloffload': '#FFD700',
        'Full-offload': '#FFD700',
    }
    
    # Width and positions for grouped bars
    x = np.arange(len(block_sizes))
    n_impls = len(impl_data)
    width = 0.8 / n_impls  # Adjust width based on number of implementations
    offsets = np.linspace(-(n_impls-1)*width/2, (n_impls-1)*width/2, n_impls)
    
    # Plot bars for each implementation
    for i, (impl_name, offset) in enumerate(zip(sorted(impl_data.keys()), offsets)):
        data = impl_data[impl_name]
        speedups = [seq_time / d['time'] for d in data]
        
        bars = ax.bar(x + offset, speedups, width, 
                     label=impl_name, 
                     color=colors.get(impl_name, '#95a5a6'),
                     edgecolor='black', 
                     linewidth=0.8)
        
        # Add speedup values on top of bars (only if not too crowded)
        if len(block_sizes) <= 7 and n_impls <= 4:
            for bar, speedup in zip(bars, speedups):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{speedup:.1f}x',
                       ha='center', va='bottom', 
                       fontweight='bold', fontsize=8, rotation=0)
    
    ax.set_ylabel('Speedup (Sequential / GPU)', fontweight='bold', fontsize=13)
    ax.set_xlabel('Block Size', fontweight='bold', fontsize=13)
    
    # Include number of coordinates in title
    title = f'KMeans GPU Implementations: Speedup Comparison ({num_coords} Coordinates)'
    ax.set_title(title, fontweight='bold', fontsize=15)
    
    ax.set_xticks(x)
    ax.set_xticklabels(block_sizes, fontsize=11)
    ax.axhline(y=1, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, label='Baseline (1x)')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(fontsize=11, loc='lower right')
    
    plt.tight_layout()
    
    # Save plot
    if not os.path.exists('plots'):
        os.makedirs('plots')
    
    # Create output filename based on input filename
    base_name = os.path.splitext(os.path.basename(filename))[0]
    out_filename = f'plots/{base_name}_speedup_comparison.svg'
    
    plt.savefig(out_filename, dpi=300)
    print(f"Saved plot to {out_filename}")
    plt.show()

def main():
    parser = argparse.ArgumentParser(
        description='Plot speedup comparison for KMeans GPU implementations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plot all implementations
  python plot_all_speedups.py results/run_kmeans_32_coords_all.out
  
  # Plot only Naive and Transpose
  python plot_all_speedups.py results/run_kmeans_32_coords_all.out --include naive transpose
  
  # Plot only Full-offload
  python plot_all_speedups.py results/run_kmeans_32_coords_all.out --include fulloffload
        """
    )
    
    parser.add_argument('filename', help='Path to results file')
    parser.add_argument('--include', '-i', nargs='+', 
                       choices=['naive', 'transpose', 'shared', 'fulloffload', 'all'],
                       help='Include only specific implementations (default: all)')
    
    args = parser.parse_args()
    
    seq_time, impl_data, num_coords = parse_results(args.filename)
    
    if seq_time == 0:
        print("Sequential time not found in file.")
        return
    
    if not impl_data:
        print("No implementation data found in file.")
        return
    
    # Filter implementations if specified
    if args.include:
        impl_data = filter_implementations(impl_data, args.include)
        if not impl_data:
            print(f"No matching implementations found for: {', '.join(args.include)}")
            return
    
    print(f"Sequential time: {seq_time:.2f} ms")
    print(f"Number of coordinates: {num_coords}")
    print(f"Found implementations: {', '.join(impl_data.keys())}")
    for impl_name, data in impl_data.items():
        print(f"  {impl_name}: {len(data)} block sizes")
    
    plot_all_speedups(seq_time, impl_data, num_coords, args.filename)

if __name__ == "__main__":
    main()