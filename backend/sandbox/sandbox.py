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
    sample_data: list | None = None,
    filename: str = "data.csv",
):
    """
    Run a given code snippet inside a Docker sandbox with restricted resources.
    The code is saved to a uniquely named file and executed within the container.
    All output files are prefixed with a unique task ID for easy identification.
    If sample_data is provided, it is saved as a CSV file in the data directory.
    """
    if name:
        safe = re.sub(r"[^a-zA-Z0-9_\-]+", "_", name).strip("_")
        base = safe[:40] if safe else "task"
    else:
        base = hashlib.sha1(code.encode("utf-8")).hexdigest()[:12]

    suffix = uuid.uuid4().hex[:4]
    task_id = f"{base}_{suffix}"

    # Use absolute paths relative to the backend location or a fixed temporary location
    # For a VM backend, we might want a dedicated temp area.
    # Using 'sandbox/code' and 'sandbox/output' relative to CWD (which will be app root)
    tasks_dir = os.path.abspath("sandbox/code")
    outputs_dir = os.path.abspath("sandbox/output")
    data_dir_abs = os.path.abspath("sandbox/data")

    os.makedirs(tasks_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)
    os.makedirs(data_dir_abs, exist_ok=True)

    # Save sample_data as CSV if provided
    if sample_data:
        import csv

        csv_path = os.path.join(data_dir_abs, filename)
        if sample_data:
            keys = sample_data[0].keys()
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(sample_data)
            print(f"Saved sample data to {csv_path}")

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

    # Ensure data_dir exists if it's relative (for backward compatibility)
    abs_data_dir = data_dir_abs  # Use our sandbox/data directory

    # Resolve paths for the Docker command (Host vs Container)
    mount_data_dir = abs_data_dir
    mount_tasks_dir = tasks_dir
    mount_outputs_dir = outputs_dir

    host_workdir = os.getenv("HOST_WORKDIR")
    if host_workdir:
        # We are running inside a container, but need to tell the sibling container
        # where the files are on the HOST.
        # We assume the layout inside the container matches the host (relative to workdir)
        # OR we perform a prefix replacement.
        container_cwd = os.getcwd()  # e.g. /app

        if mount_data_dir.startswith(container_cwd):
            mount_data_dir = mount_data_dir.replace(container_cwd, host_workdir, 1)

        if mount_tasks_dir.startswith(container_cwd):
            mount_tasks_dir = mount_tasks_dir.replace(container_cwd, host_workdir, 1)

        if mount_outputs_dir.startswith(container_cwd):
            mount_outputs_dir = mount_outputs_dir.replace(
                container_cwd, host_workdir, 1
            )

    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--memory=1g",
        "--cpus=1.0",
        "-v",
        f"{mount_data_dir}:/sandbox/data:ro",
        "-v",
        f"{mount_tasks_dir}:/sandbox/code:ro",
        "-v",
        f"{mount_outputs_dir}:/sandbox/output",
        image,
        "python",
        f"/sandbox/code/{task_id}.py",
    ]

    try:
        process = subprocess.Popen(
            docker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
    except FileNotFoundError:
        return {
            "stdout": "",
            "stderr": "Error: 'docker' command not found. Please ensure Docker is installed and in the PATH on the backend server.",
            "artifacts": [],
            "media": [],
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Error running Docker: {str(e)}",
            "artifacts": [],
            "media": [],
        }

    artifacts = [
        p
        for p in glob.glob(os.path.join(outputs_dir, "*"))
        if task_id in os.path.basename(p)
    ]

    import base64

    media = []
    for art in artifacts:
        # Check if it looks like an image
        if art.lower().endswith((".png", ".jpg", ".jpeg", ".pdf", ".svg")):
            try:
                with open(art, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                    media.append(
                        {"filename": os.path.basename(art), "content": encoded}
                    )
            except Exception as e:
                print(f"Failed to encode artifact {art}: {e}")

    return {
        "stdout": stdout,
        "stderr": stderr,
        "artifacts": artifacts,
        "media": media,
    }
