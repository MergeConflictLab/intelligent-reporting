import sys
import os
import time
import json
import argparse
import logging
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("benchmark_remote")


def run_remote_benchmark(
    file_path: str,
    offline_mode: bool = True,
    output_file: str = "benchmark_remote_results.json",
    base_url: str = "http://localhost:8000",
    direct_vm: bool = False,
    local_url: str = "http://localhost:8000",
):
    results = {
        "timestamp": datetime.now().isoformat(),
        "file": file_path,
        "mode": "offline" if offline_mode else "online",
        "type": "direct_vm" if direct_vm else "remote_api",
        "target": base_url,
        "local_prep": local_url if direct_vm else None,
        "steps": {},
        "totals": {
            "latency_ms": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }

    start_total = time.perf_counter()

    # Helper to accumulate tokens
    def add_usage(step_name, usage_dict):
        if not usage_dict:
            return

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

        results["totals"]["prompt_tokens"] += prompt
        results["totals"]["completion_tokens"] += completion
        results["totals"]["total_tokens"] += total

    # 1. Upload/Profile (Using LOCAL Sidecar for Data)
    # Even in direct_vm mode, we need the initial data structures (sample_data, etc.)
    # Strategy: Use local_url for profiling if direct_vm is set,
    # to simulate the "Frontend" preparing the data.
    prep_url = local_url if direct_vm else base_url

    logger.info(f"Step 1: Uploading & Profiling (Prep via {prep_url})...")
    start = time.perf_counter()

    # Upload
    files = {"file": open(file_path, "rb")}
    try:
        resp = requests.post(f"{prep_url}/api/upload", files=files)
        resp.raise_for_status()
        upload_data = resp.json()
        uploaded_path = upload_data["file_path"]
        logger.info(f"File uploaded to: {uploaded_path}")
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return

    # Profile
    profile_req = {"file_path": uploaded_path, "max_rows": 10}
    resp = requests.post(f"{prep_url}/api/profile", json=profile_req)
    resp.raise_for_status()
    profile_data = resp.json()

    sample_data = profile_data["sample_data"]
    description = profile_data["description"]
    schema_info = profile_data["schema_info"]

    results["steps"]["profiling"] = {"latency_ms": (time.perf_counter() - start) * 1000}

    # Helper for endpoints
    def get_endpoint(step):
        if direct_vm:
            return f"{base_url}/agents/{step}/run"
        return f"{base_url}/api/{step}"

    # 3. Metadata Agent
    logger.info("Step 3: Metadata Agent...")
    start = time.perf_counter()

    metadata_req = {
        "sample_data": sample_data,
        "schema_info": schema_info,
        "description": description,  # Note: Backend expects Dict, Sidecar might expect something else but backend schema says Dict.
        "offline_mode": offline_mode,
    }

    # Fix for backend schema mismatch if needed
    # Backend MetadataInput description is Dict[str, Any], but Profile returns List[Dict] or Dict?
    # Profile (DataSummarizer) typically returns a list of column descriptions.
    # If direct_vm, we might need to wrap it?
    if direct_vm and isinstance(description, list):
        metadata_req["description"] = {"columns": description}

    endpoint = get_endpoint("metadata")
    resp = requests.post(endpoint, json=metadata_req)
    resp.raise_for_status()
    metadata_out = resp.json()

    # Handle response differences
    # Sidecar returns: {metadata_json: ..., usage: ...}
    # Backend returns: The raw JSON from agent (which might be {columns: ...} or {table_description: ...})
    # If direct_vm, usage data might NOT be present unless agent includes it inside the JSON.

    usage = metadata_out.get("usage", metadata_out.get("_usage", {}))
    results["steps"]["metadata_agent"] = {
        "latency_ms": (time.perf_counter() - start) * 1000,
        "usage": usage,
    }
    add_usage("metadata_agent", usage)

    if direct_vm:
        # For Supervisor, we need the output.
        # MetadataAgent returns {columns: [...], table_description: ...}
        # Sidecar wraps this in "metadata_json" and creates "supervisor_description"
        supervisor_description = [metadata_out]  # Wrap plainly
    else:
        supervisor_description = metadata_out["supervisor_description"]

    # 4. Supervisor Agent
    logger.info("Step 4: Supervisor Agent...")
    start = time.perf_counter()
    supervisor_req = {
        "sample_data": sample_data,
        "description": (
            supervisor_description if direct_vm else None
        ),  # Backend expects "description", Sidecar "supervisor_description"
        "supervisor_description": supervisor_description if not direct_vm else None,
        "offline_mode": offline_mode,
    }

    # Fix for direct VM schema match
    # Backend SupervisorInput: sample_data: List, description: List
    # supervisor_description is a List[Dict], so it fits `description`.
    if direct_vm:
        supervisor_req = {
            "sample_data": sample_data,
            "description": supervisor_description,
            "offline_mode": offline_mode,
        }

    endpoint = get_endpoint("supervisor")
    resp = requests.post(endpoint, json=supervisor_req)
    resp.raise_for_status()
    supervisor_out = resp.json()

    usage = supervisor_out.get("usage", supervisor_out.get("_usage", {}))
    results["steps"]["supervisor_agent"] = {
        "latency_ms": (time.perf_counter() - start) * 1000,
        "usage": usage,
    }
    add_usage("supervisor_agent", usage)

    if direct_vm:
        tasks = supervisor_out.get("tasks", [])
        # Agent returns {tasks: [...]}, Sidecar returns {tasks: [...]}
    else:
        tasks = supervisor_out.get("tasks", [])

    logger.info(f"Supervisor planned {len(tasks)} tasks.")

    # 5. Execute Tasks (Assistant)
    logger.info("Step 5: Assistant Agent...")
    results["steps"]["assistant_agent"] = {
        "latency_ms": 0,
        "tasks_executed": 0,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }

    # We need a sandbox data path. For local execution, it's just the upload path
    # ideally we should use the absolute path of the uploaded file
    sandbox_path = os.path.abspath(uploaded_path)

    for task in tasks:
        logger.info(f"  executing task: {task.get('name')}")
        start_task = time.perf_counter()

        if direct_vm:
            # Backend AssistantInput: supervisor_response: Dict, path: str
            # This is different from Sidecar which takes task, description, etc.
            # And backend `run_assistant` only generates code, doesn't execute in sandbox?
            # backend/api/routes.py: run_assistant takes AssistantInput(supervisor_response, path)
            # It calls assistant_agent.run(supervisor_response, path)
            # The AssistantAgent expects `supervisor_response` which contains the *plan* or the *specific task*?
            # `AssistantAgent.run` signature: (self, supervisor_response: str | Dict, path: str = "data.csv", ...)
            # We should probably pass the WHOLE task as `supervisor_response`?
            # Or constructs a prompt.

            task_req = {
                "supervisor_response": task,
                "path": "data.csv",  # Remote path assumption? or just used for prompt context.
                "offline_mode": offline_mode,
            }
            endpoint = f"{base_url}/agents/assistant/run"
        else:
            task_req = {
                "task": task,
                "sandbox_data_path": sandbox_path,
                "offline_mode": offline_mode,
                "sample_data": sample_data,
                "description": description,
                "schema_info": schema_info,
            }
            endpoint = f"{base_url}/api/execute_task"

        resp = requests.post(endpoint, json=task_req)
        resp.raise_for_status()
        task_out = resp.json()

        duration = (time.perf_counter() - start_task) * 1000
        usage = task_out.get("usage", task_out.get("_usage", {}))

        results["steps"]["assistant_agent"]["latency_ms"] += duration
        results["steps"]["assistant_agent"]["tasks_executed"] += 1

        # Access or initialize detailed tasks list
        if "details" not in results["steps"]["assistant_agent"]:
            results["steps"]["assistant_agent"]["details"] = []

        results["steps"]["assistant_agent"]["details"].append(
            {"task_name": task.get("name"), "latency_ms": duration, "usage": usage}
        )

        # Aggregate manually for assistant
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

    logger.info(f"Direct VM Benchmark completed. Results saved to {output_file}")

    # Print Summary
    print("\n--- Direct VM Benchmark Summary ---")
    print(f"Total Duration: {results['totals']['latency_ms']:.2f} ms")
    print(f"Total Tokens:   {results['totals']['total_tokens']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark the Intelligent Reporting Pipeline via API"
    )
    parser.add_argument(
        "--file", type=str, default="data/all_album_data.csv", help="Path to CSV file"
    )
    parser.add_argument(
        "--online", action="store_true", help="Run in online mode (requires keys)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_remote_results.json",
        help="Output JSON file",
    )
    parser.add_argument(
        "--base-url", type=str, default="http://localhost:8000", help="Base URL for API"
    )
    parser.add_argument(
        "--local-url",
        type=str,
        default="http://localhost:8000",
        help="Local Prep URL (default localhost:8000)",
    )
    parser.add_argument(
        "--direct-vm", action="store_true", help="Target remote VM endpoints directly"
    )

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File {args.file} not found.")
        sys.exit(1)

    # Check if local prep server is running if needed
    prep_url = args.local_url if args.direct_vm else args.base_url
    try:
        requests.get(f"{prep_url}/health", timeout=2)
    except:
        print(
            f"Error: Local Sidecar/Prep API ({prep_url}) is required. Please start it on the correct port."
        )
        sys.exit(1)

    run_remote_benchmark(
        args.file,
        offline_mode=not args.online,
        output_file=args.output,
        base_url=args.base_url,
        direct_vm=args.direct_vm,
        local_url=prep_url,
    )
