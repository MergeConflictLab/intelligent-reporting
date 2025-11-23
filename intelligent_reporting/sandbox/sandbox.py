import os
import uuid
import subprocess
import glob


def run_in_docker_sandbox(code: str, data_dir="data", image="llm-sandbox"):
    task_id = str(uuid.uuid4())

    tasks_dir = os.path.abspath("temp_tasks")
    outputs_dir = os.path.abspath("task_outputs")

    os.makedirs(tasks_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)

    # Inject code so all plots and files get saved properly
    header = f"""
import os
OUTPUT_DIR = "/sandbox/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
TASK_ID = "{task_id}"

import matplotlib.pyplot as plt
_old_savefig = plt.savefig
def _custom_savefig(path, *args, **kwargs):
    fname = TASK_ID + "_" + os.path.basename(path)
    full = os.path.join(OUTPUT_DIR, fname)
    _old_savefig(full, *args, **kwargs)
plt.savefig = _custom_savefig
"""

    code = header + "\n" + code

    # Write code file
    task_file = os.path.join(tasks_dir, f"{task_id}.py")
    with open(task_file, "w") as f:
        f.write(code)

    # Docker command
    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--memory=1g",
        "--cpus=1.0",
        "-v",
        f"{os.path.abspath(data_dir)}:/sandbox/data:ro",
        "-v",
        f"{tasks_dir}:/sandbox/code:ro",
        "-v",
        f"{outputs_dir}:/sandbox/output",
        image,
        "python",
        f"/sandbox/code/{task_id}.py",
    ]

    process = subprocess.Popen(
        docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    stdout, stderr = process.communicate()

    # Collect artifacts
    artifacts = [
        p
        for p in glob.glob(os.path.join(outputs_dir, "*"))
        if task_id in os.path.basename(p)
    ]

    return {
        "stdout": stdout,
        "stderr": stderr,
        "artifacts": artifacts,
    }
