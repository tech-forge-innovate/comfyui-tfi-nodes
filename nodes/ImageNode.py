import base64
import copy
import io
import os

import numpy as np
import torch
from PIL import ImageOps, Image, ImageSequence

from nodes import LoadImage
from comfy.cli_args import args
from PIL.PngImagePlugin import PngInfo
from json import JSONEncoder, JSONDecoder
from .util import pil_to_tensor, read_image_from_url 


class LoadImageFromURL:
    """
    Load image from a remote URL
    """
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "urls": ("STRING", {"multiline": True, "default": "", "dynamicPrompts": False}),
        },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("images", "masks")

    FUNCTION = "convert"

    CATEGORY = "TFI/Image"

    # INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (True, True,)

    def convert(self, urls):
        urls = urls.splitlines()
        images = []
        masks = []
        for url in urls:
            if not url.strip().isspace():
                i = read_image_from_url(url.strip())
                i = ImageOps.exif_transpose(i)
                if i.mode == 'I':
                    i = i.point(lambda i: i * (1 / 255))
                image = i.convert("RGB")
                image = pil_to_tensor(image)
                images.append(image)
                if 'A' in i.getbands():
                    mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                    mask = 1. - torch.from_numpy(mask)
                else:
                    mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
                masks.append(mask.unsqueeze(0))

        return (images, masks, )


NODE_CLASS_MAPPINGS = {
    "LoadImageFromURL": LoadImageFromURL,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromURL": "Load Image From Url",
}