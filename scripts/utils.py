import re
import base64
import json


def strip_code_fence(md: str) -> str:
    md = re.sub(r"^\s*```(?:\w+)?\s*\n", "", md)
    md = re.sub(r"\n\s*```\s*$", "", md)
    return md.strip()


from PIL import Image
import io


def encode_image(image_path, max_dimension=1024):
    """
    Encodes an image to base64, resizing it if it exceeds max_dimension.
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB to ensure compatibility (e.g. for JPEGs)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resize if too large
            width, height = img.size
            if max(width, height) > max_dimension:
                scale_factor = max_dimension / max(width, height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                print(
                    f"[utils] Resized image from {width}x{height} to {new_size[0]}x{new_size[1]}"
                )

            # Save to buffer
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except ImportError:
        # Fallback if Pillow is not installed
        print("[utils] Pillow not found, falling back to raw read.")
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"[utils] Error resizing image: {e}, falling back to raw read.")
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")


def json_fix(content):
    if not isinstance(content, str):
        return content

    try:
        loaded = json.loads(content)
        if isinstance(loaded, str):
            return json_fix(loaded)
        return loaded
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", content, re.S)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    try:
        first_brace = content.find("{")
        first_bracket = content.find("[")

        start_index = -1
        end_index = -1
        is_object = False

        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            start_index = first_brace
            end_index = content.rfind("}")
            is_object = True
        elif first_bracket != -1:
            start_index = first_bracket
            end_index = content.rfind("]")
            is_object = False

        if start_index != -1 and end_index != -1:
            json_str = content[start_index : end_index + 1]
            return json.loads(json_str)

    except json.JSONDecodeError:
        pass

    return content
