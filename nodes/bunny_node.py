import os
import pathlib
from urllib.parse import urlparse
from .BunnyCDNStorage import CDNConnector


class BunnyCDNStorageNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # accept multiple file socket types (Audio/Video/Image) or a raw path string
                "file": ("AUDIO","VIDEO","IMAGE","STRING"),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    # Return the uploaded URL
    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "TFI"
    OUTPUT_NODE = True

    def run(self, file, prompt=None, extra_pnginfo=None):
        # instantiate connector using env vars
        connector = CDNConnector(
            os.getenv("BUNNY_API_KEY") or os.getenv("BUNNY_ACCESS_KEY") or os.getenv("BUNNY_TOKEN_KEY") or "",
            os.getenv("BUNNY_STORAGE_ZONE", "product-gennie"),
            os.getenv("BUNNY_STORAGE_REGION", "sg"),
            os.getenv("BUNNY_TOKEN_KEY", "")
        )

        # Validate local file
        # `file` may be a path string or a socket object that resolves to a path;
        # normalise by coercing to string then to Path
        p = pathlib.Path(str(file))
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Local file not found: {file}")

        # Determine cdn_path and file_name from output_url
        cdn_path = ""
        file_name = p.name

        # upload using CDNConnector (upload_file accepts a file path or file-like)
        result = connector.upload_file(cdn_path, file_name, str(p))
        uploaded_url = result.get("filepath", "")

        return (uploaded_url,)
