from nodes.ImageNode import LoadImageFromURL
from .nodes.audio_url_loader import AudioURLLoader
from .nodes.audio_duration import AudioDuration
from .nodes.bunny_node import BunnyCDNStorageNodeVideoUpload

NODE_CLASS_MAPPINGS = {
    "Audio URL Loader": AudioURLLoader,
    "Audio duration": AudioDuration,
    "Bunny CDN Video Upload": BunnyCDNStorageNodeVideoUpload,
    "LoadImageFromURL": LoadImageFromURL,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Audio URL Loader": "🔊 Audio URL Loader",
    "Audio duration": "⏱️ Audio duration"
    ,"Bunny CDN Video Upload": "🐰 Bunny CDN Video Upload"
    ,"LoadImageFromURL": "Load Image From Url"
}
