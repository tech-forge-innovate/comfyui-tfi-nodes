import json
from comfy.comfy_types.node_typing import IO
from urllib.parse import urlparse

# Preview Any - original implement from
# https://github.com/rgthree/rgthree-comfy/blob/main/py/display_any.py
# upstream requested in https://github.com/Kosinkadink/rfcs/blob/main/rfcs/0000-corenodes.md#preview-nodes
class ShowUrl():
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"url": (IO.STRING, {})},
        }

    RETURN_TYPES = ()
    FUNCTION = "main"
    OUTPUT_NODE = True

    CATEGORY = "TFI/utils"
    SEARCH_ALIASES = ["show url"]

    def _is_valid_url(self, s):
        if not isinstance(s, str):
            return False
        try:
            parsed = urlparse(s.strip())
            return parsed.scheme in ("http", "https") and bool(parsed.netloc)
        except Exception:
            return False

    def main(self, url=None):
        isValid = self._is_valid_url(url)
        print(f"ShowUrl: Received URL: {url}, is valid: {isValid}")
        value = url if isValid else "Not updated"
        print(f"ShowUrl: URL is valid: {isValid}, value: {value}")
        return {"ui": {"bunny_upload_result": (isValid, value,)}}
