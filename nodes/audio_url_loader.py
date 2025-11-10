import os
import tempfile
import mimetypes
import requests
from urllib.parse import urlparse
import subprocess

try:
    import numpy as np
except Exception:
    np = None

try:
    import torch
except Exception:
    torch = None


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

    # Return an Audio object and the loaded duration in seconds
    RETURN_TYPES = ("AUDIO", "STRING")
    RETURN_NAMES = ("audio", "loaded_duration")
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
    - Audio: an audio object (implemented here as a path to a temp file)

        Raises:
        - ValueError for invalid responses or non-audio content-types
        - requests.HTTPError for HTTP errors
        """

        if not url or not isinstance(url, str):
            raise ValueError("`url` must be a non-empty string")

        # sanitize timeout: requests does not accept 0 or negative values
        DEFAULT_TIMEOUT = 30
        try:
            t = float(timeout) if timeout is not None else DEFAULT_TIMEOUT
            if t <= 0:
                print(f"[AudioURLLoader] Provided timeout {timeout} is <= 0; using default {DEFAULT_TIMEOUT}s")
                t = DEFAULT_TIMEOUT
        except Exception:
            t = DEFAULT_TIMEOUT

        # Attempt to request the URL (streaming)
        try:
            resp = requests.get(url, stream=True, timeout=t)
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

        # Build a simple Audio object (dict) that many audio-aware nodes expect
        # to be indexable by string keys rather than a plain string path.
        # Include several commonly-used keys so downstream nodes like
        # SONIC_PreData can access at least one of them (path/filepath/name/mime).
        guessed_mime = content_type.split(";")[0].strip() if content_type else None

        # attempt to create a waveform numpy array shape (1, channels, samples)
        waveform = None
        sample_rate = None

        def read_wav_to_numpy(path):
            try:
                import wave as _wave
                with _wave.open(path, 'rb') as wf:
                    nch = wf.getnchannels()
                    sr = wf.getframerate()
                    nframes = wf.getnframes()
                    frames = wf.readframes(nframes)
                    sampwidth = wf.getsampwidth()

                    if np is None:
                        return None, sr

                    if sampwidth == 1:
                        dtype = np.uint8  # 8-bit WAV is unsigned
                    elif sampwidth == 2:
                        dtype = np.int16
                    elif sampwidth == 4:
                        dtype = np.int32
                    else:
                        dtype = np.int16

                    data = np.frombuffer(frames, dtype=dtype)
                    if nch > 1:
                        data = data.reshape(-1, nch).T  # shape (channels, samples)
                    else:
                        data = data.reshape(1, -1)

                    # normalize to float32 in -1..1
                    if dtype == np.uint8:
                        data = (data.astype(np.float32) - 128.0) / 128.0
                    elif dtype == np.int16:
                        data = data.astype(np.float32) / 32768.0
                    elif dtype == np.int32:
                        data = data.astype(np.float32) / 2147483648.0

                    # add batch dim -> shape (1, channels, samples)
                    return data[np.newaxis, :, :], sr
            except Exception:
                return None, None

        # try direct WAV read
        waveform, sample_rate = read_wav_to_numpy(tmp_path)

        # if not WAV or failed, try ffmpeg to convert to WAV then read
        if waveform is None:
            try:
                # check ffmpeg exists
                subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                conv_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                conv_path = conv_tmp.name
                conv_tmp.close()
                # convert to WAV with 1 channel, 16000 Hz to be safe
                cmd = [
                    "ffmpeg", "-y", "-i", tmp_path,
                    "-ar", "16000", "-ac", "1", conv_path
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                waveform, sample_rate = read_wav_to_numpy(conv_path)
                try:
                    os.remove(conv_path)
                except Exception:
                    pass
            except Exception:
                waveform = None

        # If still None, provide a silent waveform to avoid type errors downstream
        if waveform is None:
            if np is not None:
                waveform = np.zeros((1, 1, 1), dtype=np.float32)
                sample_rate = 16000
            else:
                waveform = None

        audio_obj = {
            "path": tmp_path,
            "filepath": tmp_path,
            "name": os.path.basename(tmp_path),
            "mime": guessed_mime or (mimetypes.types_map.get(suffix.lower()) if suffix else None),
            "source_url": url,
            "waveform": waveform,
            "sample_rate": sample_rate,
        }

        # Convert waveform to torch tensor if available; SONIC nodes often expect torch
        if waveform is not None and torch is not None and not isinstance(waveform, torch.Tensor):
            try:
                # ensure float32
                waveform = torch.from_numpy(waveform).float()
                audio_obj["waveform"] = waveform
            except Exception:
                pass

        # compute loaded duration: prefer tensor.size(2) like SONIC expects
        loaded_duration = 0.0
        try:
            if audio_obj["waveform"] is not None:
                if torch is not None and isinstance(audio_obj["waveform"], torch.Tensor):
                    frames = audio_obj["waveform"].size(2)
                elif np is not None:
                    frames = audio_obj["waveform"].shape[2]
                else:
                    frames = 0

                if audio_obj.get("sample_rate"):
                    loaded_duration = float(frames) / float(audio_obj["sample_rate"]) if frames and audio_obj["sample_rate"] else 0.0
        except Exception:
            loaded_duration = 0.0

        return (audio_obj, str(round(loaded_duration, 3)))
