import re
import sys
from typing import List, Dict
from matplotlib import pyplot as plt

def parse_results(filepath: str) -> List[Dict]:
	"""
	Parse a kmeans results file and return a list of dicts with:
	 dataset_size_MB, numObjs, numCoords, numClusters,
	 numThreads, nloops, total_time_s, per_loop_time_s
	"""
	header_re = re.compile(
		r"dataset_size\s*=\s*([\d\.]+)\s*MB\s+numObjs\s*=\s*(\d+)\s+numCoords\s*=\s*(\d+)\s+numClusters\s*=\s*(\d+)"
	)
	threads_re = re.compile(r"\(number of threads:\s*(\d+)\)")
	timing_re = re.compile(
		r"nloops\s*=\s*(\d+)\s*\(total\s*=\s*([\d\.]+)s\)\s*\(per loop\s*=\s*([\d\.]+)s\)"
	)

	results = []
	with open(filepath, "r", encoding="utf-8") as f:
		lines = f.readlines()

	i = 0
	while i < len(lines):
		mh = header_re.search(lines[i])
		if mh:
			entry = {
				"dataset_size_MB": float(mh.group(1)),
				"numObjs": int(mh.group(2)),
				"numCoords": int(mh.group(3)),
				"numClusters": int(mh.group(4)),
				"numThreads": None,
				"nloops": None,
				"total_time_s": None,
				"per_loop_time_s": None,
			}
			# scan forward for threads and timing until next header or EOF
			j = i + 1
			while j < len(lines):
				# stop if new header encountered
				if header_re.search(lines[j]):
					break
				mt = threads_re.search(lines[j])
				if mt:
					entry["numThreads"] = int(mt.group(1))
				mti = timing_re.search(lines[j])
				if mti:
					entry["nloops"] = int(mti.group(1))
					entry["total_time_s"] = float(mti.group(2))
					entry["per_loop_time_s"] = float(mti.group(3))
					# once timing found we can consider this run complete
					break
				j += 1
			results.append(entry)
			# continue from j to avoid re-parsing same block
			i = j
		else:
			i += 1
	return results

if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("Usage: python diagram_gen.py <results_file>")
		sys.exit(1)

	results_file = sys.argv[1]
	results = parse_results(results_file)

	for entry in results:
		print(entry)