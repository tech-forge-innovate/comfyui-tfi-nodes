import os
import pathlib
from urllib.parse import urlparse
from .BunnyCDNStorage import CDNConnector
from comfy.comfy_types.node_typing import IO

class BunnyCDNStorageNodeVideoUpload:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # required input is a VIDEO socket (or a path string that points to a video)
                "filenames": (IO.ANY, {}),
                "index": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1}),
                "BUNNY_API_KEY": ("STRING", {"default": ""}),
                "BUNNY_TOKEN_KEY": ("STRING", {"default": ""}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    # Return the uploaded URL
    RETURN_TYPES = ("STRING", IO.ANY,)
    RETURN_NAMES = ("url", "filenames",)
    FUNCTION = "run"
    CATEGORY = "TFI/Video"
    OUTPUT_NODE = True

    def run(self, filenames, index, BUNNY_API_KEY, BUNNY_TOKEN_KEY, prompt=None, extra_pnginfo=None):
        # instantiate connector using env vars
        api_key = BUNNY_API_KEY or os.getenv("BUNNY_API_KEY") or os.getenv("BUNNY_ACCESS_KEY") or ""
        token_key = BUNNY_TOKEN_KEY or os.getenv("BUNNY_TOKEN_KEY", "")
        connector = CDNConnector(
            api_key,
            os.getenv("BUNNY_STORAGE_ZONE", "product-gennie"),
            os.getenv("BUNNY_STORAGE_REGION", "sg"),
            token_key,
        )

        # Validate local file
        # Resolve video input to a real filesystem path. The `video` input may be:
        # - a plain path string
        # - a pathlib.Path
        # - a dict-like audio/video socket with keys like 'path' or 'filepath'
        # - an object with attributes like 'path', 'filepath', 'file_path', or 'output_path'
        def resolve_path(obj):
            # list / tuple of filenames or video objects (e.g. from Video Combine VHS)
            try:
                if isinstance(obj, (list, tuple)) and obj:
                    # Special-case structure from Video Combine VHS:
                    # [ True/False, ["...png", "...mp4", "...-audio.mp4"] ]
                    if (
                        len(obj) == 2
                        and isinstance(obj[0], (bool, int))
                        and isinstance(obj[1], (list, tuple))
                    ):
                        candidates = [
                            pathlib.Path(s)
                            for s in obj[1]
                            if isinstance(s, str)
                        ]

                        # Prefer main video file (mp4, mov, mkv, webm) and avoid "-audio"
                        preferred_exts = [".mp4", ".mov", ".mkv", ".webm"]
                        for p in candidates:
                            if (
                                p.suffix.lower() in preferred_exts
                                and "-audio" not in p.name
                                and p.exists()
                            ):
                                return p

                        # Fallback: first existing path from the list
                        for p in candidates:
                            if p.exists():
                                return p

                    # Generic list/tuple handling: try each element recursively
                    for item in obj:
                        try:
                            p = resolve_path(item)
                            if p is not None:
                                return p
                        except Exception:
                            continue
            except Exception:
                pass

            # plain string or Path
            try:
                if isinstance(obj, (str, pathlib.Path)):
                    p = pathlib.Path(obj)
                    if p.exists():
                        return p
            except Exception:
                pass

            # dict-like (e.g. sockets with filenames or paths)
            try:
                if hasattr(obj, 'get') and callable(obj.get):
                    # explicit support for typical video combine structures
                    # that may expose 'filename' or 'filenames'
                    filenames = obj.get('filenames') or obj.get('filename')
                    if filenames:
                        # could be a single string or list
                        if isinstance(filenames, (list, tuple)):
                            for f in filenames:
                                if f:
                                    p = pathlib.Path(f)
                                    if p.exists():
                                        return p
                        else:
                            p = pathlib.Path(filenames)
                            if p.exists():
                                return p

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
        isSucess = filenames[0]
        if not isSucess:
            return ("",)
        path = filenames[1][index]
        p = resolve_path(path)

        # Determine cdn_path and file_name from output_url
        cdn_path = ""
        file_name = p.name

        # upload using CDNConnector (upload_file accepts a file path or file-like)
        result = connector.upload_file(cdn_path, file_name, str(p))
        # Prefer a signed/tokenized URL generated from the known path,
        # fall back to whatever upload_file returned in 'filepath'.
        try:
            relative_path = f"{cdn_path}/{file_name}" if cdn_path else file_name
            uploaded_url = connector.generate_url(relative_path)
        except Exception:
            uploaded_url = result.get("filepath", "") if isinstance(result, dict) else ""

        print(f"Uploaded to BunnyCDN: {uploaded_url}")
        return (uploaded_url, filenames,)
