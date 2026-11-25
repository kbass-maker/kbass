"""Generate academic figures from the sustained HTTP benchmark results."""

import json
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmarks/results/sustained_30s"
OUTPUT = ROOT / "docs/project/images"

OUTPUT.mkdir(parents=True, exist_ok=True)

files = sorted(RESULTS.glob("run_*.json"))

if len(files) != 29:
    raise SystemExit(f"Expected 29 runs, found {len(files)}")

experiment_data = [json.loads(path.read_text()) for path in files]
runs = [data["summary"] for data in experiment_data]
expected_requests = 29_000
all_latencies = []
for index, data in enumerate(experiment_data, start=1):
    summary = data["summary"]
    requests = data["requests"]
    if summary["total_requests"] != 1000:
        raise SystemExit(f"Unexpected request count in batch {index}.")
    if summary["workers"] != 10:
        raise SystemExit(f"Unexpected worker count in batch {index}.")
    if len(requests) != summary["total_requests"]:
        raise SystemExit(f"Request record mismatch in batch {index}.")
    successful = [
        request for request in requests
        if request["status"] == 200
    ]
    if len(successful) != summary["successful_requests"]:
        raise SystemExit(f"Success count mismatch in batch {index}.")
    if len(requests) - len(successful) != summary["failed_requests"]:
        raise SystemExit(f"Failure count mismatch in batch {index}.")
    if summary["failed_requests"] != 0:
        raise SystemExit(f"Failed requests found in batch {index}.")
    all_latencies.extend(
        request["latency_ms"] for request in successful
    )
if len(all_latencies) != expected_requests:
    raise SystemExit("Unexpected number of successful latency observations.")
if sum(r["total_requests"] for r in runs) != expected_requests:
    raise SystemExit("Unexpected total request count.")
if sum(r["successful_requests"] for r in runs) != expected_requests:
    raise SystemExit("Not all expected requests were successful.")
run_numbers = np.arange(1, len(runs) + 1)
throughput = [r["throughput_rps"] for r in runs]
avg_latency = [r["latency_ms"]["average"] for r in runs]


# Figure 5.1: Throughput across experimental batches
fig, ax = plt.subplots(figsize=(10, 5.5))

ax.plot(run_numbers, throughput, marker="o", linewidth=1.8,
        markersize=5, label="Batch throughput")

ax.axhline(statistics.mean(throughput), linestyle="--",
           label=f"Mean: {statistics.mean(throughput):.2f} req/s")

ax.set(
    title="HTTP Throughput Across 29 Experimental Batches",
    xlabel="Experimental batch",
    ylabel="Throughput (requests/second)",
)
ax.set_xticks(run_numbers)
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()
fig.savefig(OUTPUT / "benchmark-throughput.png", dpi=300)
plt.close(fig)

# Figure 5.2: Average latency across experimental batches
fig, ax = plt.subplots(figsize=(10, 5.5))

ax.plot(run_numbers, avg_latency, marker="o", linewidth=1.8,
        markersize=5)

ax.axhline(statistics.mean(avg_latency), linestyle="--",
           label=f"Mean batch latency: {statistics.mean(avg_latency):.2f} ms")

ax.set(
    title="Average HTTP Response Latency Across Experimental Batches",
    xlabel="Experimental batch",
    ylabel="Average response latency (ms)",
)
ax.set_xticks(run_numbers)
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()
fig.savefig(OUTPUT / "benchmark-batch-latency.png", dpi=300)
plt.close(fig)

# Figure 5.3: Distribution of pooled request latencies
fig, ax = plt.subplots(figsize=(10, 5.5))

def nearest_rank_percentile(values, percentage):
    ordered = sorted(values)
    index = max(0, int(np.ceil(len(ordered) * percentage / 100)) - 1)
    return ordered[index]


p50 = nearest_rank_percentile(all_latencies, 50)
p95 = nearest_rank_percentile(all_latencies, 95)
p99 = nearest_rank_percentile(all_latencies, 99)

ax.hist(all_latencies, bins=60, edgecolor="black", linewidth=0.3)

ax.axvline(p50, linestyle="--", label=f"P50: {p50:.2f} ms")
ax.axvline(p95, linestyle="--", label=f"P95: {p95:.2f} ms")
ax.axvline(p99, linestyle=":", label=f"P99: {p99:.2f} ms")

ax.set(
    title="Distribution of HTTP Response Latencies",
    xlabel="Response latency (ms)",
    ylabel="Number of requests",
)
ax.grid(axis="y", alpha=0.25)
ax.legend()
fig.tight_layout()
fig.savefig(OUTPUT / "benchmark-latency-distribution.png", dpi=300)
plt.close(fig)

if len(all_latencies) != expected_requests:
    raise SystemExit("Unexpected number of successful latency observations.")

# Figure 5.4: Exploratory comparison of the two observed performance phases
phases = [
    (1, 16, "Batches 1–16"),
    (17, 29, "Batches 17–29"),
]

phase_names = []
phase_throughput = []
phase_latency = []

for start, end, name in phases:
    selected = runs[start - 1:end]
    phase_names.append(name)
    phase_throughput.append(
        statistics.mean(r["throughput_rps"] for r in selected)
    )
    phase_latency.append(
        statistics.mean(r["latency_ms"]["average"] for r in selected)
    )

fig, axes = plt.subplots(1, 2, figsize=(11, 5))

axes[0].bar(phase_names, phase_throughput)
axes[0].set_title("Mean Throughput")
axes[0].set_ylabel("Requests/second")
axes[0].grid(axis="y", alpha=0.25)

axes[1].bar(phase_names, phase_latency)
axes[1].set_title("Mean Response Latency")
axes[1].set_ylabel("Milliseconds")
axes[1].grid(axis="y", alpha=0.25)

fig.suptitle("Performance Comparison Across Experimental Phases")
fig.tight_layout()
fig.savefig(OUTPUT / "benchmark-phase-comparison.png", dpi=300)
plt.close(fig)

print("Four experimental figures generated successfully.")
print(f"Output directory: {OUTPUT}")
print(f"Total requests: {len(all_latencies):,}")
print(f"P50 latency: {p50:.3f} ms")
print(f"P95 latency: {p95:.3f} ms")
print(f"P99 latency: {p99:.3f} ms")

for name, value in zip(phase_names, phase_throughput):
    print(f"{name} mean throughput: {value:.2f} requests/s")

for name, value in zip(phase_names, phase_latency):
    print(f"{name} mean latency: {value:.3f} ms")
