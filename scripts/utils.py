import re
import base64
import json
def strip_code_fence(md: str) -> str:
    # remove opening ```lang and closing ``` (keeps inner content)
    md = re.sub(r"^\s*```(?:\w+)?\s*\n", "", md)  # remove opening fence+lang line
    md = re.sub(r"\n\s*```\s*$", "", md)  # remove trailing fence
    return md.strip()

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
    

def json_fix(content):
    parsed = None
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # Attempt to extract the first JSON array/object from the text
            import re

            m = re.search(r"(\[\s*\{.*\}\s*\])", content, flags=re.S)
            if m:
                try:
                    parsed = json.loads(m.group(1))
                except Exception:
                    parsed = content
            else:
                parsed = content
    else:
        # Already a structured object (list/dict)
        parsed = content
    return parsed