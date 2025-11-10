import time

from datetime import datetime

EXEC_TIMERS = {}

class StartTimer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "job_id": ("STRING",),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ( "STRING", )
    RETURN_NAMES = ("job_id", )
    FUNCTION = "start_timer"
    CATEGORY = "TFI/Debug"

    def start_timer(self, job_id, prompt=None, extra_pnginfo=None):
        EXEC_TIMERS[job_id] = time.time()
        print(f"🟢 Timer started for workflow {job_id} at {datetime.now().strftime('%H:%M:%S')}")
        return (job_id, )
