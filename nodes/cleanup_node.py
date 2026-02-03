import os
import pathlib


class CleanupFilenamesNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # Expected to be the same structure as Video Combine VHS "Filenames" output:
                # [ True/False, ["/path/one", "/path/two", ...] ]
                "filenames": ("STRING", {"multiline": True, "default": ""}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "TFI/Utils"
    OUTPUT_NODE = False

    def run(self, filenames):
        # Comfy usually passes the raw Python object, not JSON, so
        # here we assume filenames is already a list-like structure
        # [success, [paths...]] as shown in the preview.
        try:
            success = filenames[0]
            paths = filenames[1] if len(filenames) > 1 else []
        except Exception:
            return ("Invalid filenames input",)

        if not success:
            return ("No files to delete (success flag is false)",)

        deleted = []
        missing = []

        for p in paths:
            try:
                path_obj = pathlib.Path(p)
                if path_obj.exists():
                    os.remove(path_obj)
                    deleted.append(str(path_obj))
                else:
                    missing.append(str(path_obj))
            except Exception:
                missing.append(str(p))

        msg_parts = []
        if deleted:
            msg_parts.append(f"Deleted {len(deleted)} file(s)")
        if missing:
            msg_parts.append(f"{len(missing)} file(s) missing or failed to delete")

        if not msg_parts:
            msg_parts.append("No files provided")

        return ("; ".join(msg_parts),)
