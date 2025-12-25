import os
import uuid
import subprocess
import glob
import hashlib
import re


def run_in_docker_sandbox(
    code: str,
    data_dir="data",
    image="llm-sandbox",
    name: str | None = None,
):
    """
    Run a given code snippet inside a Docker sandbox with restricted resources.
    The code is saved to a uniquely named file and executed within the container.
    All output files are prefixed with a unique task ID for easy identification.
    """
    if name:
        safe = re.sub(r"[^a-zA-Z0-9_\-]+", "_", name).strip("_")
        base = safe[:40] if safe else "task"
    else:
        base = hashlib.sha1(code.encode("utf-8")).hexdigest()[:12]

    suffix = uuid.uuid4().hex[:4]
    task_id = f"{base}_{suffix}"

    tasks_dir = os.path.abspath("sandbox/code")
    outputs_dir = os.path.abspath("sandbox/output")

    os.makedirs(tasks_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)

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

    task_file = os.path.join(tasks_dir, f"{task_id}.py")
    with open(task_file, "w") as f:
        f.write(code)

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
