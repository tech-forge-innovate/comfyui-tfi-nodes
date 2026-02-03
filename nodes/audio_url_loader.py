import os
import tempfile
from comfy_api.latest import IO
import requests
from urllib.parse import urlparse
import torch
import av

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
    
    def _f32_pcm(self, wav: torch.Tensor) -> torch.Tensor:
        """Convert audio to float 32 bits PCM format."""
        if wav.dtype.is_floating_point:
            return wav
        elif wav.dtype == torch.int16:
            return wav.float() / (2 ** 15)
        elif wav.dtype == torch.int32:
            return wav.float() / (2 ** 31)
        raise ValueError(f"Unsupported wav dtype: {wav.dtype}")
    
    def _load(self, filepath: str) -> tuple[torch.Tensor, int]:
        with av.open(filepath) as af:
            if not af.streams.audio:
                raise ValueError("No audio stream found in the file.")

            stream = af.streams.audio[0]
            sr = stream.codec_context.sample_rate
            n_channels = stream.channels

            frames = []
            length = 0
            for frame in af.decode(streams=stream.index):
                buf = torch.from_numpy(frame.to_ndarray())
                if buf.shape[0] != n_channels:
                    buf = buf.view(-1, n_channels).t()

                frames.append(buf)
                length += buf.shape[1]

            if not frames:
                raise ValueError("No audio frames decoded.")

            wav = torch.cat(frames, dim=1)
            wav = self._f32_pcm(wav)
            return wav, sr

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
            waveform, sample_rate = self._load(temp_path)

            # Cleanup temporary file
            os.unlink(temp_path)

            audio = {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}
            return IO.NodeOutput(audio)

        except Exception as e:
            print(f"Error loading audio from URL: {str(e)}")
            # Return empty audio in case of error
            waveform = torch.zeros((1, 2, 1))
            sample_rate = 44100
            return IO.NodeOutput({"waveform": waveform, "sample_rate": sample_rate})
