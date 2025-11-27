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
    parsed = None
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            m = re.search(r"(\[\s*\{.*\}\s*\])", content, flags=re.S)
            if m:
                try:
                    parsed = json.loads(m.group(1))
                except Exception:
                    parsed = content
            else:
                parsed = content
    else:
        parsed = content
    return parsed
