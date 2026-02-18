import datetime
import os
import pathlib
import tempfile
from urllib.parse import urlparse
from .BunnyCDNStorage import CDNConnector
from .util import tensor_to_pil
from comfy.comfy_types.node_typing import IO

class BunnyCDNStorageNodeVideoUpload:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # required input is a VIDEO socket (or a path string that points to a video)
                "process_id": ("STRING", {"default": ""}),
                "cdn_path": ("STRING", {"default": ""}),
            },
            "optional": {
                "filenames": (IO.ANY, {}),
                "image": (IO.IMAGE, {}),
                "video": (IO.VIDEO, {}),
                "index": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    # Return the uploaded URL
    RETURN_TYPES = ("STRING", "ANY")
    RETURN_NAMES = ("url", "filenames")
    CATEGORY = "TFI/Video"
    FUNCTION = "run"
    
    def resolve_path(self, obj):
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
                        p = self.resolve_path(item)
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

    def _extract_sequence_entry(self, payload, index):
        """Return (success_flag, selected_entry) from common Comfy payload shapes."""
        if isinstance(payload, (list, tuple)):
            if len(payload) == 0:
                raise FileNotFoundError("Input payload is empty; no files to upload.")

            if (
                len(payload) == 2
                and isinstance(payload[0], (bool, int))
                and isinstance(payload[1], (list, tuple))
            ):
                success = bool(payload[0])
                if not success:
                    return False, None

                files = payload[1]
                if not files:
                    raise FileNotFoundError("Input payload did not include any filenames.")
                if index >= len(files):
                    raise IndexError(f"Requested index {index} but only {len(files)} file(s) available.")
                return True, files[index]

            if index >= len(payload):
                raise IndexError(f"Requested index {index} but only {len(payload)} item(s) available.")
            return True, payload[index]

        return True, payload

    def _materialize_image(self, image):
        """Persist an IMAGE tensor/list to a temporary PNG and return its Path."""
        img_data = image
        if isinstance(img_data, (list, tuple)):
            if not img_data:
                raise FileNotFoundError("IMAGE input was empty; nothing to upload.")
            img_data = img_data[0]

        try:
            pil_image = tensor_to_pil(img_data)
        except Exception as exc:
            raise FileNotFoundError("Unable to convert IMAGE input into a file for upload.") from exc

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp.close()
        pil_image.save(tmp.name, format="PNG")
        return pathlib.Path(tmp.name)

    def _looks_like_video_input(self, obj):
        return (
            hasattr(obj, "get_stream_source")
            and callable(getattr(obj, "get_stream_source"))
            and hasattr(obj, "save_to")
            and callable(getattr(obj, "save_to"))
        )

    def _materialize_video_input(self, video_obj):
        """Convert a VIDEO input object into a local path. Returns (Path, should_cleanup)."""
        source = None
        try:
            if hasattr(video_obj, "get_stream_source") and callable(getattr(video_obj, "get_stream_source")):
                source = video_obj.get_stream_source()
        except Exception:
            source = None

        if isinstance(source, (str, os.PathLike)):
            path = pathlib.Path(source)
            if path.exists():
                return path, False

        if source is not None and hasattr(source, "read"):
            try:
                source.seek(0)
            except Exception:
                pass
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tmp.close()
            with open(tmp.name, "wb") as handle:
                handle.write(source.read())
            return pathlib.Path(tmp.name), True

        if hasattr(video_obj, "save_to") and callable(getattr(video_obj, "save_to")):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tmp.close()
            video_obj.save_to(tmp.name)
            return pathlib.Path(tmp.name), True

        raise FileNotFoundError("Unable to resolve a local path from the provided VIDEO input.")

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")
    
    def run(
        self,
        process_id,
        cdn_path,
        filenames=None,
        image=None,
        video=None,
        index=0,
        prompt=None,
        extra_pnginfo=None,
    ):
        # instantiate connector using env vars only
        api_key = os.getenv("BUNNY_API_KEY", "")
        token_key = os.getenv("BUNNY_TOKEN_KEY", "")
        connector = CDNConnector(
            api_key,
            os.getenv("BUNNY_STORAGE_ZONE", "product-gennie"),
            os.getenv("BUNNY_STORAGE_REGION", "sg"),
            token_key,
        )

        passthrough = None
        candidate = None

        if filenames is not None:
            passthrough = filenames
            success, candidate = self._extract_sequence_entry(filenames, index)
            if not success:
                return ("", passthrough)
        elif video is not None:
            passthrough = video
            success, candidate = self._extract_sequence_entry(video, index)
            if not success:
                return ("", passthrough)
        elif image is not None:
            passthrough = image
            candidate = image
        else:
            raise ValueError("No filenames, video, or image input provided for upload.")

        cleanup_paths = []
        try:
            if self._looks_like_video_input(candidate):
                p, should_cleanup = self._materialize_video_input(candidate)
                if should_cleanup:
                    cleanup_paths.append(p)
            else:
                try:
                    p = self.resolve_path(candidate)
                except FileNotFoundError:
                    if image is not None:
                        temp_image = self._materialize_image(image)
                        cleanup_paths.append(temp_image)
                        p = temp_image
                    elif self._looks_like_video_input(candidate):
                        p, should_cleanup = self._materialize_video_input(candidate)
                        if should_cleanup:
                            cleanup_paths.append(p)
                    else:
                        raise

            # Determine cdn_path and file_name from output_url
            # Prefer a non-empty process_id; otherwise use a timestamp.
            base_name = process_id.strip() if isinstance(process_id, str) else ""
            if not base_name:
                base_name = datetime.datetime.now().strftime("upload_%Y%m%d_%H%M%S")
            file_name = f"{base_name}{p.suffix}"

            # upload using CDNConnector (upload_file accepts a file path or file-like)
            result = connector.upload_file(cdn_path, file_name, str(p))
            # Prefer a signed/tokenized URL generated from the known path,
            # fall back to whatever upload_file returned in 'filepath'.
            print(f"BunnyCDNStorageNodeVideoUpload: Upload result: {result}")
            try:
                relative_path = f"{cdn_path}/{file_name}" if cdn_path else file_name
                uploaded_url = connector.generate_url(relative_path)
            except Exception:
                uploaded_url = result.get("filepath", "") if isinstance(result, dict) else ""
            return (uploaded_url, passthrough)
        finally:
            for tmp_path in cleanup_paths:
                try:
                    if tmp_path.exists():
                        tmp_path.unlink()
                except Exception:
                    pass