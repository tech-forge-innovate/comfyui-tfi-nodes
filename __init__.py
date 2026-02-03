from .nodes.image_node import LoadImageFromURL
from .nodes.audio_url_loader import AudioURLLoader
from .nodes.bunny_node import BunnyCDNStorageNodeVideoUpload
from .nodes.cleanup_node import CleanupFilenamesNode

NODE_CLASS_MAPPINGS = {
    "Audio URL Loader": AudioURLLoader,
    "Bunny CDN Video Upload": BunnyCDNStorageNodeVideoUpload,
    "LoadImageFromURL": LoadImageFromURL,
    "CleanupFilenamesNode": CleanupFilenamesNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Audio URL Loader": "🔊 Audio URL Loader"
    ,"Bunny CDN Video Upload": "🐰 Bunny CDN Video Upload"
    ,"LoadImageFromURL": "Load Image From Url"
    ,"CleanupFilenamesNode": "Cleanup Filenames"
}
