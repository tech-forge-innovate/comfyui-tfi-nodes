import os
import tempfile
import subprocess
import numpy as np
import torch
from PIL import ImageOps, Image
from urllib.parse import urlparse

from .util import pil_to_tensor, read_image_from_url


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
import shutil

FFMPEG_PATH = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
FFPROBE_PATH = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"

if not FFMPEG_PATH:
    raise RuntimeError("ffmpeg not found in PATH")

class LoadImageFromURL:

    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "url": ("STRING", {"multiline": True, "default": "", "dynamicPrompts": False}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "convert"
    CATEGORY = "TFI/Image"
    OUTPUT_IS_LIST = (False, False)

    def _get_extension(self, url: str):
        parsed = urlparse(url)
        path = parsed.path
        _, ext = os.path.splitext(path)
        return ext.lower()

    def _download_temp_video(self, url: str):
        import requests

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        for chunk in response.iter_content(chunk_size=8192):
            tmp_file.write(chunk)

        tmp_file.close()
        return tmp_file.name

    def _extract_last_frame_ffmpeg(self, video_path: str):
        temp_image = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_image.close()

        # Step 1: get duration
        result = subprocess.run(
            [FFPROBE_PATH, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path],
            capture_output=True,
            text=True
        )

        duration = float(result.stdout.strip())

        # Step 2: seek 0.5 sec before end (safer than 0.001)
        seek_time = max(duration - 0.5, 0)

        cmd = [
            FFMPEG_PATH,
            "-y",
            "-ss", str(seek_time),
            "-i", video_path,
            "-frames:v", "1",
            temp_image.name
        ]

        subprocess.run(cmd, check=True)

        # Step 3: validate file size
        if os.path.getsize(temp_image.name) == 0:
            raise RuntimeError("FFmpeg produced empty frame.")

        img = Image.open(temp_image.name).convert("RGB")
        os.remove(temp_image.name)

        return img

    def convert(self, url):
        image = None
        mask = None

        url = url.strip()
        if not url:
            return (None, None)

        ext = self._get_extension(url)

        if ext in VIDEO_EXTENSIONS:
            video_path = self._download_temp_video(url)
            try:
                img = self._extract_last_frame_ffmpeg(video_path)
            finally:
                if os.path.exists(video_path):
                    os.remove(video_path)

        elif ext in IMAGE_EXTENSIONS:
            img = read_image_from_url(url)

        else:
            raise ValueError(f"Unsupported file extension: {ext}")

        # common processing
        img = ImageOps.exif_transpose(img)

        if img.mode == 'I':
            img = img.point(lambda i: i * (1 / 255))

        image = pil_to_tensor(img.convert("RGB"))

        if 'A' in img.getbands():
            mask_np = np.array(img.getchannel('A')).astype(np.float32) / 255.0
            mask = 1. - torch.from_numpy(mask_np)
        else:
            mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")

        return (image, mask)