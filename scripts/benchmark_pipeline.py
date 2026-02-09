import sys
import os
import time
import json
import argparse
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from intelligent_reporting.pipeline import Pipeline
from intelligent_reporting.profiling import DataSampler, DataSummarizer, DataVisualizer
from intelligent_reporting.agents.metadata_agent import MetadataAgent
from intelligent_reporting.agents.supervisor_agent import SupervisorAgent
from intelligent_reporting.agents.assistant_agent import AssistantAgent
from intelligent_reporting.agents.insights_agent import InsightsAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("benchmark")


def run_benchmark(
    file_path: str,
    offline_mode: bool = True,
    output_file: str = "benchmark_results.json",
):
    results = {
        "timestamp": datetime.now().isoformat(),
        "file": file_path,
        "mode": "offline" if offline_mode else "online",
        "steps": {},
        "totals": {
            "latency_ms": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }

    start_total = time.perf_counter()

    # 1. Data Loading
    logger.info("Step 1: Data Loading...")
    start = time.perf_counter()
    pipeline = Pipeline(file=file_path)
    df = pipeline.load()
    if df is None:
        logger.error("Failed to load dataframe.")
        return

    # Infer and Downcast
    typed, schema_map = pipeline.infer(data=df)
    downcasted = pipeline.downcast(data=typed)

    results["steps"]["loading"] = {
        "latency_ms": (time.perf_counter() - start) * 1000,
        "rows": df.height,
        "cols": df.width,
    }

    # 2. Profiling (Sampler, Summarizer, Visualizer)
    logger.info("Step 2: Profiling...")
    start = time.perf_counter()
    RESULTS_DIR = "results_benchmark"
    FIGURES_DIR = "figures_benchmark"
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    sampler = DataSampler(df=downcasted, max_rows=10, sample_dir=RESULTS_DIR)
    summarizer = DataSummarizer(
        df=downcasted, summary_dir=RESULTS_DIR, figures_dir=FIGURES_DIR
    )

    sample_data = sampler.run_sample()
    description = summarizer.summary()
    input_schema = {col: str(downcasted.schema[col]) for col in downcasted.columns}

    results["steps"]["profiling"] = {"latency_ms": (time.perf_counter() - start) * 1000}

    # Helper to accumulate tokens
    def add_usage(step_name, usage_dict):
        if step_name not in results["steps"]:
            results["steps"][step_name] = {
                "latency_ms": 0,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            }

        step_usage = results["steps"][step_name].setdefault("usage", {})
        prompt = usage_dict.get("prompt_tokens", 0)
        completion = usage_dict.get("completion_tokens", 0)
        total = usage_dict.get("total_tokens", prompt + completion)

        if "prompt_tokens" not in step_usage:
            step_usage["prompt_tokens"] = 0
        if "completion_tokens" not in step_usage:
            step_usage["completion_tokens"] = 0
        if "total_tokens" not in step_usage:
            step_usage["total_tokens"] = 0

        step_usage["prompt_tokens"] += prompt
        step_usage["completion_tokens"] += completion
        step_usage["total_tokens"] += total

        results["totals"]["prompt_tokens"] += prompt
        results["totals"]["completion_tokens"] += completion
        results["totals"]["total_tokens"] += total

    # 3. Agents
    metadata_agent = MetadataAgent()
    supervisor_agent = SupervisorAgent()
    assistant_agent = AssistantAgent()

    # Metropolitan Agent (Metadata)
    logger.info("Step 3: Metadata Agent...")
    start = time.perf_counter()
    metadata_out = metadata_agent.run(
        sample_data=sample_data,
        schema=input_schema,
        description=description,
        offline_mode=offline_mode,
    )
    results["steps"]["metadata_agent"] = {
        "latency_ms": (time.perf_counter() - start) * 1000,
        "usage": metadata_out.get("_usage", {}),
    }
    add_usage("metadata_agent", metadata_out.get("_usage", {}))

    # Supervisor Agent
    logger.info("Step 4: Supervisor Agent...")

    # Prepare supervisor description
    supervisor_description = []
    if isinstance(metadata_out, dict) and "columns" in metadata_out:
        supervisor_description = metadata_out["columns"]
    elif isinstance(metadata_out, list):
        supervisor_description = metadata_out
    else:
        supervisor_description = [metadata_out]

    start = time.perf_counter()
    supervisor_out = supervisor_agent.run(
        sample_data=sample_data,
        description=supervisor_description,
        offline_mode=offline_mode,
    )

    results["steps"]["supervisor_agent"] = {
        "latency_ms": (time.perf_counter() - start) * 1000,
        "usage": supervisor_out.get("_usage", {}),
    }
    add_usage("supervisor_agent", supervisor_out.get("_usage", {}))

    tasks = supervisor_out.get("tasks", [])
    logger.info(f"Supervisor planned {len(tasks)} tasks.")

    # Assistant Agent
    logger.info("Step 5: Assistant Agent...")
    results["steps"]["assistant_agent"] = {
        "latency_ms": 0,
        "tasks_executed": 0,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }

    for task in tasks:
        logger.info(f"  generating code for: {task.get('name')}")
        start_task = time.perf_counter()

        # We need a dummy path for assistant
        abs_path = os.path.abspath(file_path)

        assistant_out = assistant_agent.run(
            supervisor_response=task, path=abs_path, offline_mode=offline_mode
        )

        duration = (time.perf_counter() - start_task) * 1000
        usage = assistant_out.get("_usage", {})

        results["steps"]["assistant_agent"]["latency_ms"] += duration
        results["steps"]["assistant_agent"]["tasks_executed"] += 1

        # Aggregate manually for assistant since it loops
        step_usage = results["steps"]["assistant_agent"]["usage"]
        p = usage.get("prompt_tokens", 0)
        c = usage.get("completion_tokens", 0)
        t = usage.get("total_tokens", p + c)

        step_usage["prompt_tokens"] += p
        step_usage["completion_tokens"] += c
        step_usage["total_tokens"] += t

        results["totals"]["prompt_tokens"] += p
        results["totals"]["completion_tokens"] += c
        results["totals"]["total_tokens"] += t

    # Total Time
    results["totals"]["latency_ms"] = (time.perf_counter() - start_total) * 1000

    # Save Results
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Benchmark completed. Results saved to {output_file}")

    # Print Summary
    print("\n--- Benchmark Summary ---")
    print(f"Total Duration: {results['totals']['latency_ms']:.2f} ms")
    print(f"Total Tokens:   {results['totals']['total_tokens']}")
    print(f"  - Prompt:     {results['totals']['prompt_tokens']}")
    print(f"  - Completion: {results['totals']['completion_tokens']}")
    print("-------------------------\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark the Intelligent Reporting Pipeline"
    )
    parser.add_argument(
        "--file", type=str, default="data/all_album_data.csv", help="Path to CSV file"
    )
    parser.add_argument(
        "--online", action="store_true", help="Run in online mode (requires keys)"
    )
    parser.add_argument(
        "--output", type=str, default="benchmark_results.json", help="Output JSON file"
    )

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File {args.file} not found.")
        sys.exit(1)

    run_benchmark(args.file, offline_mode=not args.online, output_file=args.output)
