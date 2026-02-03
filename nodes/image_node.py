import numpy as np
import torch
from PIL import ImageOps

from comfy.cli_args import args
from .util import pil_to_tensor, read_image_from_url 


class LoadImageFromURL:
    """
    Load image from a remote URL
    """
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "url": ("STRING", {"multiline": True, "default": "", "dynamicPrompts": False}),
        },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")

    FUNCTION = "convert"

    CATEGORY = "TFI/Image"

    # INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (False, False,)

    def convert(self, url):
        image = None
        mask = None
        if url.strip() != "":
            if not url.strip().isspace():
                i = read_image_from_url(url.strip())
                i = ImageOps.exif_transpose(i)
                if i.mode == 'I':
                    i = i.point(lambda i: i * (1 / 255))
                image = i.convert("RGB")
                image = pil_to_tensor(image)
                if 'A' in i.getbands():
                    mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                    mask = 1. - torch.from_numpy(mask)
                else:
                    mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")

        return (image, mask)