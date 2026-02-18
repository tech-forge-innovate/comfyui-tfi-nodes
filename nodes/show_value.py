import json
from comfy.comfy_types.node_typing import IO


class ShowValue:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"value": (IO.ANY, {})},
        }

    RETURN_TYPES = ()
    FUNCTION = "main"
    OUTPUT_NODE = True

    CATEGORY = "TFI/utils"
    SEARCH_ALIASES = ["show value", "display value"]

    def _to_display_string(self, v):
        try:
            # Try JSON serialization for readable dict/list structures
            return json.dumps(v, ensure_ascii=False, indent=2)
        except Exception:
            try:
                return str(v)
            except Exception:
                return "<unserializable>"

    def main(self, value=None):
        display_str = self._to_display_string(value)
        print(f"ShowValue: Received value: {display_str}")
        # The UI preview convention mirrors ShowUrl but with a different key
        return {"ui": {"show_value": (True, display_str,)}}
