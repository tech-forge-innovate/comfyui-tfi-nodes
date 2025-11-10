from .nodes.webhook import *
from .nodes.start_timer import *
from .nodes.execution_timer import *
from .nodes.audio_url_loader import AudioURLLoader
from .nodes.audio_duration import AudioDuration
from .nodes.bunny_node import BunnyCDNStorageNode

NODE_CLASS_MAPPINGS = {
    "TFI Webhook": Webhook,
    "Start timer": StartTimer,
    "Execution timer": ExecutionTimer,
    "Audio URL Loader": AudioURLLoader,
    "Audio duration": AudioDuration,
    "Bunny CDN Storage": BunnyCDNStorageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TFI Job Data": "💾 TFI Job Data",
    "Start timer": "Start timer",
    "Execution timer": "Execution timer"
    ,"Audio URL Loader": "🔊 Audio URL Loader",
    "Audio duration": "⏱️ Audio duration"
    ,"Bunny CDN Storage": "🐰 Bunny CDN Storage"
}
