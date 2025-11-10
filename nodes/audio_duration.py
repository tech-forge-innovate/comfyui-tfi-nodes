import os
import wave
import contextlib

try:
    # mutagen supports many formats (mp3, m4a, flac, etc.)
    from mutagen import File as MutagenFile
except Exception:
    MutagenFile = None


class AudioDuration:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING",),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("duration_seconds",)
    FUNCTION = "get_duration"
    CATEGORY = "TFI/Audio"

    def get_duration(self, file_path, prompt=None, extra_pnginfo=None):
        """Return audio duration in seconds (as a string).

        Strategy:
        - If mutagen is available, use it to read duration for many formats.
        - Otherwise, if file is WAV, use the standard library wave module.
        - If neither works, raise an informative error telling the user to
          install mutagen: `pip install mutagen`.
        """

        if not file_path or not isinstance(file_path, str):
            raise ValueError("`file_path` must be a non-empty string")

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # First try mutagen when available
        if MutagenFile is not None:
            try:
                audio = MutagenFile(file_path)
                if audio is not None and hasattr(audio, "info") and getattr(audio.info, "length", None) is not None:
                    duration = float(audio.info.length)
                    return (duration,)
            except Exception:
                # fall through to other methods
                pass

        # Fallback: support WAV using wave module
        try:
            # wave only supports uncompressed WAV files
            with contextlib.closing(wave.open(file_path, 'rb')) as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
                return (duration,)
        except wave.Error:
            # not a WAV or unsupported WAV
            pass
        except Exception:
            # other IO errors
            pass

        # If we reach here, we couldn't determine duration
        raise RuntimeError(
            "Could not determine audio duration. Install mutagen (`pip install mutagen`) to support MP3/M4A/FLAC, or provide a WAV file."
        )
