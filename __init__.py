from .nodes.show_url import ShowUrl
from .nodes.image_node import LoadImageFromURL
from .nodes.audio_url_loader import AudioURLLoader
from .nodes.bunny_node import BunnyCDNStorageNodeVideoUpload
from .nodes.cleanup_node import CleanupFilenamesNode
from .nodes.math_nodes import AddNode, SubtractNode, MultiplyNode, DivideNode, ClampNode, FloorNode, CeilNode

NODE_CLASS_MAPPINGS = {
    "Audio URL Loader": AudioURLLoader,
    "Bunny CDN Video Upload": BunnyCDNStorageNodeVideoUpload,
    "LoadImageFromURL": LoadImageFromURL,
    "CleanupFilenamesNode": CleanupFilenamesNode,
    "AddNode": AddNode,
    "SubtractNode": SubtractNode,
    "MultiplyNode": MultiplyNode,
    "DivideNode": DivideNode,
    "ClampNode": ClampNode,
    "FloorNode": FloorNode,
    "CeilNode": CeilNode,
    "ShowUrl": ShowUrl,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Audio URL Loader": "🔊 Audio URL Loader"
    ,"Bunny CDN Video Upload": "🐰 Bunny CDN Video Upload"
    ,"LoadImageFromURL": "Load Image From Url"
    ,"CleanupFilenamesNode": "Cleanup Filenames"
    ,"AddNode": "➕ Add"
    ,"SubtractNode": "➖ Subtract"
    ,"MultiplyNode": "✖ Multiply"
    ,"DivideNode": "➗ Divide"
    ,"ClampNode": "🔒 Clamp"
    ,"FloorNode": "📉 Floor"
    ,"CeilNode": "📈 Ceil"
    ,"ShowUrl": "Show URL"
}
