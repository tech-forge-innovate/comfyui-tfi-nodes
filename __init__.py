from .nodes.webhook import *
from .nodes.start_timer import *
from .nodes.execution_timer import *

NODE_CLASS_MAPPINGS = {
    "TFI Webhook": Webhook,
    "Start timer": StartTimer,
    "Execution timer": ExecutionTimer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TFI Job Data": "💾 TFI Job Data",
    "Start timer": "Start timer",
    "Execution timer": "Execution timer"
}
