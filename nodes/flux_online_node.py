import os
import time
import io
from typing import Any, Dict, Optional

import requests

from .util import (
    pil_to_tensor,
    base64_to_image,
    read_image_from_url,
    tensor_to_pil,
    image_to_base64,
)
from comfy.comfy_types.node_typing import IO


class FLUXImageGeneratorOnline:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "", "dynamicPrompts": False}),
                "model": ("STRING", {"default": "flux-2-klein-9b"}),
                "width": ("INT", {"default": 1024, "min": 64, "max": 2048, "step": 8}),
                "height": ("INT", {"default": 1024, "min": 64, "max": 2048, "step": 8}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2**31 - 1, "step": 1}),
                "safety_tolerance": ("INT", {"default": 2, "min": 0, "max": 5, "step": 1}),
                "output_format": ("STRING", {"default": "png"}),
            },
            "optional": {
                "ref_1": (IO.IMAGE, {}),
                "ref_2": (IO.IMAGE, {}),
                "ref_3": (IO.IMAGE, {}),
                "ref_4": (IO.IMAGE, {}),
                "poll_interval_ms": ("INT", {"default": 2000, "min": 500, "max": 10000, "step": 500}),
                "timeout_ms": ("INT", {"default": 600000, "min": 10000, "max": 1800000, "step": 10000}),
            },
        }

    RETURN_TYPES = (IO.IMAGE, "FLOAT")
    RETURN_NAMES = ("image", "image_size_mb")
    FUNCTION = "generate"
    CATEGORY = "TFI/Image"

    API_HOST = "https://api.bfl.ai"

    def _resolve_api_key(self) -> str:
        key = os.getenv("BFL_API_KEY", "").strip()
        if not key:
            raise RuntimeError("BFL_API_KEY is not configured (pass via node input or environment variable)")
        return key

    def _trigger(self, api_key: str, model: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        model = (model or "flux-2-klein-9b").strip()
        url = f"{self.API_HOST}/v1/{model}"
        headers = {
            "Content-Type": "application/json",
            "x-key": api_key,
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if "polling_url" not in data:
            raise RuntimeError(f"Unexpected response from BFL API: {data}")
        return data

    def _get_result_from_polling_url(self, api_key: str, polling_url: str) -> Dict[str, Any]:
        headers = {"x-key": api_key}
        resp = requests.get(polling_url, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def _wait_for_result(
        self,
        api_key: str,
        polling_url: str,
        poll_interval_ms: int,
        timeout_ms: int,
    ) -> Dict[str, Any]:
        start = time.time() * 1000.0

        while True:
            result = self._get_result_from_polling_url(api_key, polling_url)
            status = str(result.get("status", "")).lower()

            if status == "ready":
                return result

            if (time.time() * 1000.0) - start > timeout_ms:
                raise TimeoutError(f"Timeout while waiting for result from {polling_url}")

            time.sleep(max(poll_interval_ms, 100) / 1000.0)

    def _ref_image_to_data_url(self, ref_image: Any):
        """Convert an IMAGE tensor (or list of tensors) into a base64 data URL string
        and return (data_url, size_mb) based on PNG-encoded bytes.
        """
        if ref_image is None:
            raise ValueError("Reference IMAGE is None")

        img_tensor = ref_image
        if isinstance(img_tensor, (list, tuple)) and img_tensor:
            img_tensor = img_tensor[0]

        pil_img = tensor_to_pil(img_tensor)
        # Measure encoded size in bytes (PNG) for credit calculation
        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        size_bytes = buffer.tell()
        image_size_mb = float(size_bytes) / (1024.0 * 1024.0)

        data_url = image_to_base64(pil_img)
        return data_url, image_size_mb

    def _sample_to_pil(self, sample: Any):
        if isinstance(sample, (list, tuple)) and sample:
            sample = sample[0]

        if not isinstance(sample, str):
            raise RuntimeError(f"Unsupported sample type from BFL API: {type(sample)}")

        sample_str = sample.strip()

        # Heuristic: URL vs base64/data URI
        if sample_str.startswith("http://") or sample_str.startswith("https://"):
            img = read_image_from_url(sample_str)
            if img is None:
                raise RuntimeError("Failed to load image from URL returned by BFL API")
            return img

        try:
            return base64_to_image(sample_str)
        except Exception:
            # As a last resort, try treating it as a URL
            if sample_str.startswith("http://") or sample_str.startswith("https://"):
                img = read_image_from_url(sample_str)
                if img is None:
                    raise RuntimeError("Failed to load image from URL returned by BFL API")
                return img
            raise

    def generate(
        self,
        prompt: str,
        model: str,
        width: int,
        height: int,
        seed: int,
        safety_tolerance: int,
        output_format: str,
        ref_1=None,
        ref_2=None,
        ref_3=None,
        ref_4=None,
        poll_interval_ms: int = 2000,
        timeout_ms: int = 600000,
    ):
        api_key = self._resolve_api_key()

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "seed": seed,
            "safety_tolerance": safety_tolerance,
            "output_format": output_format if output_format in ("png", "jpeg") else "png",
        }

        total_input_size_mb = 0.0

        # Map ref_1..ref_4 to the API's reference image fields if provided
        if ref_1 is not None:
            data_url, size_mb = self._ref_image_to_data_url(ref_1)
            payload["input_image"] = data_url
            total_input_size_mb += size_mb
        if ref_2 is not None:
            data_url, size_mb = self._ref_image_to_data_url(ref_2)
            payload["input_image_2"] = data_url
            total_input_size_mb += size_mb
        if ref_3 is not None:
            data_url, size_mb = self._ref_image_to_data_url(ref_3)
            payload["input_image_3"] = data_url
            total_input_size_mb += size_mb
        if ref_4 is not None:
            data_url, size_mb = self._ref_image_to_data_url(ref_4)
            payload["input_image_4"] = data_url
            total_input_size_mb += size_mb

        async_resp = self._trigger(api_key, model, payload)
        polling_url: Optional[str] = async_resp.get("polling_url")
        if not polling_url:
            raise RuntimeError(f"BFL API did not return a polling_url: {async_resp}")

        final_result = self._wait_for_result(api_key, polling_url, poll_interval_ms, timeout_ms)
        sample = (
            (final_result.get("result") or {}).get("sample")
            if isinstance(final_result.get("result"), dict)
            else final_result.get("sample")
        )

        if not sample:
            raise RuntimeError(f"BFL API result is ready but no 'sample' field was found: {final_result}")

        img = self._sample_to_pil(sample).convert("RGB")

        # Compute approximate output image size in megabytes using the selected format
        buffer = io.BytesIO()
        save_format = "PNG" if output_format.lower() == "png" else "JPEG"
        img.save(buffer, format=save_format)
        size_bytes = buffer.tell()
        output_image_size_mb = float(size_bytes) / (1024.0 * 1024.0)

        # Total size includes all input reference images plus output image
        image_size_mb = total_input_size_mb + output_image_size_mb

        image_tensor = pil_to_tensor(img)

        return (image_tensor, image_size_mb)
