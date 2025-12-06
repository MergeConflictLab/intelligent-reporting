import re
import base64
import json


def strip_code_fence(md: str) -> str:
    md = re.sub(r"^\s*```(?:\w+)?\s*\n", "", md)
    md = re.sub(r"\n\s*```\s*$", "", md)
    return md.strip()


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def json_fix(content):
    if not isinstance(content, str):
        return content

    try:
        return json.loads(content)
    except json.JSONDecodeError as f:
        # Fallback: extract only the JSON dict or list
        m = re.search(r"(\{.*\}|\[.*\])", content, flags=re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception as e:
                return e
        return f


def safe_json_load(raw):
            fixed = json_fix(raw)
            if isinstance(fixed, (dict, list)):
                return fixed
            if isinstance(fixed, str):
                try:
                    return json.loads(fixed)
                except Exception:
                    return fixed
            return raw

def normalize_tasks(parsed):
    """
    Normalizes any JSON-like structure into:
        {"tasks": [...]}
    """
    print(f"type of parsed: {type(parsed)}")
    # Nothing usable
    if parsed is None:
        return {"tasks": []}

    # Case 1: list → assume it's a list of task objects
    if isinstance(parsed, list):
        return {"tasks": parsed}

    # Case 2: dict
    if isinstance(parsed, dict):
        # If it already contains "tasks"
        if "tasks" in parsed and isinstance(parsed["tasks"], list):
            return parsed

        # If the dict does NOT contain tasks, treat whole dict as a single task
        return {"tasks": [parsed]}

    # Everything else → empty tasks
    return {"tasks": []}