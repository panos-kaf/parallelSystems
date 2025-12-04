import re
import matplotlib.pyplot as plt
from collections import defaultdict

INPUT_FILE = "../results/run_conc_ll_nb_mod.out"

# Patterns
re_header = re.compile(
    r"SIZE\s*=\s*(\d+)\s*-\s*PERCENTS\s*=\s*(\d+)\s+(\d+)\s+(\d+)",
    re.IGNORECASE
)
re_impl = re.compile(r"^(x\.\w+)", re.IGNORECASE)
re_result = re.compile(
    r"Nthreads:\s*(\d+).*?Workload:\s*(\d+)\/(\d+)\/(\d+).*?Throughput.*?:\s*([\d\.]+)",
    re.IGNORECASE,
)

# Data:
# data[(size, (p1,p2,p3))][impl][nthreads] = throughput
data = defaultdict(lambda: defaultdict(dict))
serial = defaultdict(lambda: defaultdict(float))

current_size = None
current_perc = None
current_impl = None

with open(INPUT_FILE) as f:
    for line in f:

        impl = re_impl.match(line.strip())
        if impl:
            current_impl = impl.group(1)
            continue

        head = re_header.search(line)
        if head:
            current_size = int(head.group(1))
            current_perc = (
                int(head.group(2)),
                int(head.group(3)),
                int(head.group(4)),
            )
            continue

        res = re_result.search(line)
        if res and current_impl and current_size and current_perc:
            nthreads = int(res.group(1))
            throughput = float(res.group(5))

            key = (current_size, current_perc)

            data[key][current_impl][nthreads] = throughput

            if nthreads == 1:
                serial[key][current_impl] = throughput


# -------- Plotting --------
for key, impl_data in data.items():
    size, (p1, p2, p3) = key

    plt.figure()
    plt.title(f"Speedup vs Threads\nSize={size}, Workload={p1}/{p2}/{p3}")
    plt.xlabel("Threads (log scale)")
    plt.ylabel("Speedup")
    plt.grid(True)

    # Collect all nthread values across implementations for x-axis ticks
    all_threads = set()
    for runs in impl_data.values():
        all_threads.update(runs.keys())
    xticks = sorted(all_threads)

    for impl, runs in impl_data.items():
        if impl not in serial[key] or serial[key][impl] == 0:
            print(f"[WARN] No serial baseline for {impl} {key}")
            continue

        nt = sorted(runs.keys())
        speedup = [runs[t] / serial[key][impl] for t in nt]

        plt.plot(nt, speedup, marker="o", label=impl)

    # Log scale on x-axis
    plt.xscale("log", base=2)

    # Exact nthread values as ticks
    plt.xticks(xticks, xticks, rotation=45)

    plt.legend()
    outname = f"speedup_size{size}_{p1}-{p2}-{p3}.png"
    plt.tight_layout()
    plt.savefig(outname, dpi=200)
    plt.close()

    print(f"Generated: {outname}")

print("Done.")

