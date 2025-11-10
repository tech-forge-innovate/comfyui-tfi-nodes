import os
import tempfile
import mimetypes
import requests
from urllib.parse import urlparse


class AudioURLLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING",),
            },
            "optional": {
                "file_name": ("STRING",),
                "timeout": ("INT",),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("local_path",)
    FUNCTION = "download_audio"
    CATEGORY = "TFI/IO"
    OUTPUT_NODE = False

    def download_audio(self, url, file_name=None, timeout=30, prompt=None, extra_pnginfo=None):
        """Download an audio file from a URL and save it to a temporary file.

        Inputs:
        - url: str - remote URL to fetch
        - file_name: optional suggested filename (used only to determine extension)
        - timeout: request timeout in seconds

        Returns:
        - local file path (string) where the audio is saved

        Raises:
        - ValueError for invalid responses or non-audio content-types
        - requests.HTTPError for HTTP errors
        """

        if not url or not isinstance(url, str):
            raise ValueError("`url` must be a non-empty string")

        # Attempt to request the URL (streaming)
        try:
            resp = requests.get(url, stream=True, timeout=timeout)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch URL {url}: {e}")

        if resp.status_code != 200:
            raise requests.HTTPError(f"HTTP {resp.status_code} when fetching {url}")

        # Determine content type and extension
        content_type = resp.headers.get("Content-Type", "")

        # Accept common audio types; fall back to guessing from URL or provided file_name
        is_audio = False
        if content_type:
            # content type may include charset; split it
            main_type = content_type.split(";")[0].strip()
            if main_type.startswith("audio/"):
                is_audio = True

        # If not audio by header, try to guess from URL path or provided filename
        parsed = urlparse(url)
        path = parsed.path or ""
        guessed_ext = None
        if file_name:
            guessed_ext = os.path.splitext(file_name)[1]
        if not guessed_ext and path:
            guessed_ext = os.path.splitext(path)[1]

        if not is_audio:
            # check guessed extension against common audio extensions
            if guessed_ext:
                guessed_mime = mimetypes.types_map.get(guessed_ext.lower())
                if guessed_mime and guessed_mime.startswith("audio/"):
                    is_audio = True

        if not is_audio:
            raise ValueError(f"URL does not appear to be an audio file (Content-Type: {content_type})")

        # choose suffix for temp file
        suffix = guessed_ext if guessed_ext else ".mp3"

        # create temp file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_path = tmp.name

        try:
            # stream write
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    tmp.write(chunk)
            tmp.flush()
            tmp.close()
        except Exception as e:
            # ensure we don't leave a partial file
            try:
                tmp.close()
            except Exception:
                pass
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            raise RuntimeError(f"Failed writing audio to disk: {e}")

        return (tmp_path,)
