import os
import pathlib
from urllib.parse import urlparse
from .BunnyCDNStorage import CDNConnector


class BunnyCDNStorageNodeVideoUpload:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # required input is a VIDEO socket (or a path string that points to a video)
                "video": ("VIDEO",),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    # Return the uploaded URL
    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "TFI/Video"
    OUTPUT_NODE = True

    def run(self, video, prompt=None, extra_pnginfo=None):
        # instantiate connector using env vars
        connector = CDNConnector(
            os.getenv("BUNNY_API_KEY") or os.getenv("BUNNY_ACCESS_KEY") or os.getenv("BUNNY_TOKEN_KEY") or "",
            os.getenv("BUNNY_STORAGE_ZONE", "product-gennie"),
            os.getenv("BUNNY_STORAGE_REGION", "sg"),
            os.getenv("BUNNY_TOKEN_KEY", "")
        )

        # Validate local file
        # Resolve video input to a real filesystem path. The `video` input may be:
        # - a plain path string
        # - a pathlib.Path
        # - a dict-like audio/video socket with keys like 'path' or 'filepath'
        # - an object with attributes like 'path', 'filepath', 'file_path', or 'output_path'
        def resolve_path(obj):
            # plain string or Path
            try:
                if isinstance(obj, (str, pathlib.Path)):
                    p = pathlib.Path(obj)
                    if p.exists():
                        return p
            except Exception:
                pass

            # dict-like
            try:
                if hasattr(obj, 'get') and callable(obj.get):
                    for key in ('filepath', 'path', 'file', 'file_path', 'output_path'):
                        v = obj.get(key)
                        if v:
                            p = pathlib.Path(v)
                            if p.exists():
                                return p
            except Exception:
                pass

            # object attributes
            for attr in ('filepath', 'path', 'file', 'file_path', 'output_path', 'filename', 'name'):
                try:
                    v = getattr(obj, attr, None)
                    if v:
                        p = pathlib.Path(v)
                        if p.exists():
                            return p
                except Exception:
                    pass

            # fallback: try converting to string and test
            try:
                s = str(obj)
                p = pathlib.Path(s)
                if p.exists():
                    return p
            except Exception:
                pass

            # couldn't resolve
            raise FileNotFoundError(f"Local file not found or could not resolve path from video input (type={type(obj)!r}, repr={repr(obj)})")

        p = resolve_path(video)

        # Determine cdn_path and file_name from output_url
        cdn_path = ""
        file_name = p.name

        # upload using CDNConnector (upload_file accepts a file path or file-like)
        result = connector.upload_file(cdn_path, file_name, str(p))
        uploaded_url = result.get("filepath", "")

        return (uploaded_url,)
