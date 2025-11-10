import time
from datetime import timedelta

from .start_timer import EXEC_TIMERS  # same shared dict

class ExecutionTimer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "job_id": ("STRING",),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("elapsed_time", "job_id", )
    FUNCTION = "measure_execution_time"
    CATEGORY = "TFI/Debug"

    def measure_execution_time(self, job_id, prompt=None, extra_pnginfo=None):
        start = EXEC_TIMERS.get(job_id, time.time())
        elapsed = time.time() - start + 15
        elapsed_seconds = round(elapsed, 2)  # keep two decimals for precision
        print(f"🏁 Workflow {job_id} elapsed time: {elapsed_seconds} seconds")
        if job_id in EXEC_TIMERS:
            del EXEC_TIMERS[job_id]
        return (elapsed_seconds, job_id,)
