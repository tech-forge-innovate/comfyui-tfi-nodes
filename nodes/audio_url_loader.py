import os
import tempfile
import torchaudio
import requests
from urllib.parse import urlparse
import torch
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'}


class AudioURLLoader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "url": ("STRING", {"default": "https://example.com/audio.mp3"}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "load_audio"
    CATEGORY = "TFI/Audio"

    def load_audio(self, url):
        try:
            # Check if URL is valid
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid URL: {url}")

            # Download audio file
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Create temporary file to save the audio
            extension = os.path.splitext(parsed_url.path)[1].lower()
            if extension not in AUDIO_EXTENSIONS:
                extension = '.mp3'  # Default extension if not recognized

            with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
                temp_path = temp_file.name
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)

            # Load audio using torchaudio
            waveform, sample_rate = torchaudio.load(temp_path)

            # Cleanup temporary file
            os.unlink(temp_path)

            # Return audio in ComfyUI format
            return ({"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate},)

        except Exception as e:
            print(f"Error loading audio from URL: {str(e)}")
            # Return empty audio in case of error
            waveform = torch.zeros((1, 2, 1))
            sample_rate = 44100
            return ({"waveform": waveform, "sample_rate": sample_rate},)
