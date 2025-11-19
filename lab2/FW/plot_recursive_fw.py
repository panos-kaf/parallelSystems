#!/usr/bin/env python3
"""
Parse recursive FW results and produce bar plots (time and speedup) for each matrix size.

Usage: python3 plot_recursive_fw.py
Produces PNG files in lab2/FW/diagrams/
"""
import re
import os
from collections import OrderedDict
import matplotlib.pyplot as plt

ROOT = os.path.dirname(__file__)
RESULTS = os.path.join(ROOT, "results", "recursive", "run_fw.out")
OUTDIR = os.path.join(ROOT, "diagrams")
os.makedirs(OUTDIR, exist_ok=True)


def parse_fw_recursive(filepath):
    # Returns dict size -> { 'serial': float, 'threads': {t: time, ...} }
    data = {}
    size_re = re.compile(r"-- SIZE:\s*(\d+) x (\d+) --")
    serial_re = re.compile(r"FW,\s*(\d+),(\d+\.?\d*)")
    thread_time_re = re.compile(r"FW_SR,\s*N\s*=\s*(\d+),.*Time:\s*(\d+\.?\d*)")

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cur_size = None
    for i, ln in enumerate(lines):
        m = size_re.search(ln)
        if m:
            cur_size = int(m.group(1))
            data[cur_size] = {"serial": None, "threads": {}}
            continue

        if cur_size is not None:
            ms = serial_re.search(ln)
            if ms and int(ms.group(1)) == cur_size:
                data[cur_size]["serial"] = float(ms.group(2))
                continue
            mt = thread_time_re.search(ln)
            if mt and int(mt.group(1)) == cur_size:
                # Need to find the nthreads value above this block
                # search backwards for "nthreads=K:"
                nthreads = None
                for j in range(i-1, max(i-6, -1), -1):
                    mth = re.search(r"nthreads=(\d+)", lines[j])
                    if mth:
                        nthreads = int(mth.group(1))
                        break
                if nthreads is None:
                    # fallback: if thread_time_re gives no info, skip
                    continue
                data[cur_size]["threads"][nthreads] = float(mt.group(2))

    return data


def make_plots(data):
    canonical = [1, 2, 4, 8, 16, 32, 64]
    for size, d in sorted(data.items()):
        serial = d.get("serial")
        threads_map = d.get("threads", {})
        if serial is None:
            print(f"Skipping size {size}: no serial time found")
            continue

        # Build sequences: x labels = ['seq', '1','2',...]
        x_labels = ["seq"] + [str(t) for t in canonical]
        # times: seq then canonical threads (fill missing with None)
        times = [serial]
        for t in canonical:
            times.append(threads_map.get(t, float('nan')))

        # Time bar plot
        x = list(range(len(x_labels)))
        plt.figure(figsize=(8, 4.5))
        plt.bar(x, times, color='skyblue', edgecolor='black')
        plt.xticks(x, x_labels)
        plt.xlabel('Configuration')
        plt.ylabel('Time (s)')
        plt.title(f'FW recursive — Time (N={size})')
        plt.grid(axis='y', linestyle=':', alpha=0.6)
        plt.subplots_adjust(bottom=0.15)
        out = os.path.join(OUTDIR, f'time_fw_recursive_N{size}.png')
        plt.savefig(out, bbox_inches='tight')
        plt.close()
        print('Wrote', out)

        # Speedup bar plot (baseline=serial)
        speedups = [1.0]
        for t in canonical:
            val = threads_map.get(t)
            speedups.append(serial / val if val is not None and val != 0 else float('nan'))

        plt.figure(figsize=(8, 4.5))
        plt.bar(x, speedups, color='orange', edgecolor='black')
        plt.xticks(x, x_labels)
        plt.xlabel('Configuration')
        plt.ylabel('Speedup (baseline = seq)')
        plt.title(f'FW recursive — Speedup (N={size})')
        plt.grid(axis='y', linestyle=':', alpha=0.6)
        plt.subplots_adjust(bottom=0.15)
        out2 = os.path.join(OUTDIR, f'speedup_fw_recursive_N{size}.png')
        plt.savefig(out2, bbox_inches='tight')
        plt.close()
        print('Wrote', out2)


def main():
    if not os.path.exists(RESULTS):
        print('Results file not found:', RESULTS)
        return
    data = parse_fw_recursive(RESULTS)
    # Filter only sizes requested (1024,2048,4096) and ensure data exists
    wanted = [1024, 2048, 4096]
    data = {k: v for k, v in data.items() if k in wanted}
    make_plots(data)


if __name__ == '__main__':
    main()
