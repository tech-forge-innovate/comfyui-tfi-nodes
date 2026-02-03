class AddNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "a": ("FLOAT", {"default": 0.0}),
                "b": ("FLOAT", {"default": 0.0}),
            },
        }

    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("result",)
    FUNCTION = "compute"
    CATEGORY = "TFI/Math"

    def compute(self, a, b):
        return (float(a) + float(b),)


class SubtractNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "a": ("FLOAT", {"default": 0.0}),
                "b": ("FLOAT", {"default": 0.0}),
            },
        }

    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("result",)
    FUNCTION = "compute"
    CATEGORY = "TFI/Math"

    def compute(self, a, b):
        return (float(a) - float(b),)


class MultiplyNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "a": ("FLOAT", {"default": 1.0}),
                "b": ("FLOAT", {"default": 1.0}),
            },
        }

    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("result",)
    FUNCTION = "compute"
    CATEGORY = "TFI/Math"

    def compute(self, a, b):
        return (float(a) * float(b),)


class DivideNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "a": ("FLOAT", {"default": 1.0}),
                "b": ("FLOAT", {"default": 1.0, "min": -1e9, "max": 1e9}),
            },
        }

    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("result",)
    FUNCTION = "compute"
    CATEGORY = "TFI/Math"

    def compute(self, a, b):
        b = float(b)
        if b == 0:
            return (0.0,)
        return (float(a) / b,)


class ClampNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("FLOAT", {"default": 0.0}),
                "min": ("FLOAT", {"default": 0.0}),
                "max": ("FLOAT", {"default": 1.0}),
            },
        }

    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("result",)
    FUNCTION = "compute"
    CATEGORY = "TFI/Math"

    def compute(self, value, min, max):
        v = float(value)
        lo = float(min)
        hi = float(max)
        if lo > hi:
            lo, hi = hi, lo
        return (max(lo, min(v, hi)),)


class FloorNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("FLOAT", {"default": 0.0}),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("result",)
    FUNCTION = "compute"
    CATEGORY = "TFI/Math"

    def compute(self, value):
        import math
        return (int(math.floor(float(value))),)


class CeilNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("FLOAT", {"default": 0.0}),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("result",)
    FUNCTION = "compute"
    CATEGORY = "TFI/Math"

    def compute(self, value):
        import math
        return (int(math.ceil(float(value))),)
