import torch

from comfy.model_patcher import ModelPatcher
import comfy.model_base
from .util import tensor_to_pil, hex_to_rgba, any_type


class GetImageBatchSize:
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "image": ('IMAGE', {}),
        },
        }

    RETURN_TYPES = ("NUMBER", "INT", "FLOAT",)
    RETURN_NAMES = ("number", "int", "float",)

    FUNCTION = "batch_size"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/Image"

    # INPUT_IS_LIST = False
    # OUTPUT_IS_LIST = (False, False)

    def batch_size(self, image):
        size = image.shape[0]
        return (size, size, float(size),)


class JoinList:
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "lst": ('LIST', {}),
            "delimiter": ('STRING', {"default": ','},),
        },
        }

    RETURN_TYPES = ("STRING",)
    # RETURN_NAMES = ("STRING", )

    FUNCTION = "join"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/List"

    # INPUT_IS_LIST = False
    # OUTPUT_IS_LIST = (False, False)
    DESCRIPTION = "将列表中的元素用分隔符连接成字符串。如 [\"a\",\"b\",\"c\"] => \"a,b,c\""

    def join(self, lst, delimiter=','):
        lst = delimiter.join(list(map(str, lst)))
        return (lst,)


class IntToNumber:
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "INT": ('INT', {"forceInput": True}),
        },
        }

    RETURN_TYPES = ("NUMBER",)

    FUNCTION = "convert"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/Integer"

    def convert(self, INT):
        return (INT,)


class IntToList:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "int_a": ('INT', {"forceInput": True}),
            },
            "optional": {
                "int_b": ('INT', {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("LIST",)

    FUNCTION = "convert"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/Integer"

    def convert(self, int_a, int_b=None):
        list = [int_a]
        if int_b:
            list.append(int_b)
        return (list,)


class StringToList:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "str_a": ('STRING', {"forceInput": True}),
            },
            "optional": {
                "str_b": ('STRING', {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("LIST",)

    FUNCTION = "convert"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/String"
    DESCRIPTION = "字符串拼接在一起。如 a和b => [a,b]"

    def convert(self, str_a, str_b=None):
        list = [str_a]
        if str_b:
            list.append(str_b)
        return (list,)


class SplitStringToList:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "str": ('STRING', {"forceInput": True}),
                "to_type": (["str", "int", "float", "bool"], {"default": "str"}),
                "delimiter": ('STRING', {"default": ","}),
            }
        }

    RETURN_TYPES = ("LIST",)

    FUNCTION = "convert"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/String"
    DESCRIPTION = "按分隔符把字符串拆分成列表。如 \"a,b,c\" => [a,b,c]"

    def convert(self, str, to_type, delimiter):
        result = [item.strip() for item in str.split(delimiter)]
        if to_type == "int":
            result = [int(x) for x in result]
        elif to_type == "float":
            result = [float(x) for x in result]
        elif to_type == "bool":
            result = [bool(x) for x in result]
        return (result,)


class ListMerge:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "list_a": ('LIST', {"forceInput": True}),
            },
            "optional": {
                "list_b": ('LIST', {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("LIST",)

    FUNCTION = "convert"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/List"

    def convert(self, list_a, list_b=None):
        list = [] + list_a
        if list_b:
            list = list + list_b
        return (list,)


class ShowString:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "str": ("STRING", {"forceInput": True}),
                "key": ('STRING', {"default": "text"}),
            }
        }

    RETURN_TYPES = ("STRING",)

    FUNCTION = "show"

    CATEGORY = "EasyApi/String"
    # 作为输出节点，返回数据格式是{"ui": {output_name:value}, "result": (value,)}
    # ui中是websocket返回给前端的内容，result是py执行传给下个节点用的
    OUTPUT_NODE = True

    def show(self, str, key):
        return {"ui": {key: (str,)}, "result": (str,)}


class ShowInt:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "INT": ("INT", {"forceInput": True}),
                "key": ('STRING', {"default": "text"}),
            }
        }

    RETURN_TYPES = ("INT",)

    FUNCTION = "show"

    CATEGORY = "EasyApi/Integer"
    # 作为输出节点，返回数据格式是{"ui": {output_name:value}, "result": (value,)}
    # ui中是websocket返回给前端的内容，result是py执行传给下个节点用的
    OUTPUT_NODE = True

    def show(self, INT, key):
        return {"ui": {key: (INT,)}, "result": (INT,)}


class ShowFloat:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "FLOAT": ("FLOAT", {"forceInput": True}),
                "key": ('STRING', {"default": "text"}),
            }
        }

    RETURN_TYPES = ("FLOAT",)

    FUNCTION = "show"

    CATEGORY = "EasyApi/Float"
    # 作为输出节点，返回数据格式是{"ui": {output_name:value}, "result": (value,)}
    # ui中是websocket返回给前端的内容，result是py执行传给下个节点用的
    OUTPUT_NODE = True

    def show(self, FLOAT, key):
        return {"ui": {key: (FLOAT,)}, "result": (FLOAT,)}


class ShowNumber:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "number": ("NUMBER", {"forceInput": True}),
                "key": ('STRING', {"default": "text"}),
            }
        }

    RETURN_TYPES = ("NUMBER",)

    FUNCTION = "show"

    CATEGORY = "EasyApi/Number"
    # 作为输出节点，返回数据格式是{"ui": {output_name:value}, "result": (value,)}
    # ui中是websocket返回给前端的内容，result是py执行传给下个节点用的
    OUTPUT_NODE = True

    def show(self, number, key):
        return {"ui": {key: (number,)}, "result": (number,)}


class ShowBoolean:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "Bool": ("BOOLEAN", {"forceInput": True}),
                "key": ('STRING', {"default": "text"}),
            }
        }

    RETURN_TYPES = ("BOOLEAN",)

    FUNCTION = "show"

    CATEGORY = "EasyApi/Boolean"
    OUTPUT_NODE = True

    def show(self, Bool, key):
        return {"ui": {key: (Bool,)}, "result": (Bool,)}


class ColorPicker:
    @classmethod
    def INPUT_TYPES(s):
        return {"required":
            {
                "color": ("SINGLECOLORPICKER",),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT",)
    RETURN_NAMES = ("HEX", "RGBA", "RGB", "A",)

    FUNCTION = "picker"

    CATEGORY = "EasyApi/Color"

    INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (False, False, False, False, )

    def picker(self, color):
        r, g, b, a = hex_to_rgba(color)
        h = color
        rgba = f"#{r:02X}{g:02X}{b:02X}{a:02X}"
        rgb = f"#{r:02X}{g:02X}{b:02X}"
        return h, rgba, rgb, a,


class ImageEqual:
    @classmethod
    def INPUT_TYPES(s):
        return {"required":
            {
                "a": ("IMAGE",),
                "b": ('IMAGE',),
            },
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("is_b",)

    FUNCTION = "compare"

    CATEGORY = "EasyApi/Image"

    INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (False, )

    def compare(self, a, b):
        if a.shape != b.shape:
            return False,
        result = torch.all(a == b)
        return bool(result),


# from ComfyUI-layer_diffusion
def get_model_sd_version(model: ModelPatcher):
    base: comfy.model_base.BaseModel = model.model
    model_config: comfy.supported_models.supported_models_base.BASE = base.model_config
    if isinstance(model_config, comfy.supported_models.SDXL):
        return False, True, False, False, False
    elif isinstance(
        model_config, (comfy.supported_models.SD15, comfy.supported_models.SD20)
    ):
        # SD15 and SD20 are compatible with each other.
        return True, False, False, False, False
    elif isinstance(model_config, comfy.supported_models.AuraFlow):
        return False, False, True, False, False
    elif isinstance(model_config, comfy.supported_models.Flux):
        return False, False, False, True, False
    elif isinstance(model_config, comfy.supported_models.HunyuanDiT):
        return False, False, False, False, True
    else:
        return False, False, False, False, False


class SDBaseVerNumber:
    @classmethod
    def INPUT_TYPES(s):
        return {"required":
            {
                "model": ("MODEL",),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "BOOLEAN", "BOOLEAN", "BOOLEAN", "BOOLEAN")
    RETURN_NAMES = ("sd1.5", "sdxl", "aura", "flux", "hunyuan")

    FUNCTION = "exec"

    CATEGORY = "EasyApi/Logic"

    INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (False, False, False, False, False)

    def exec(self, model):
        return (*get_model_sd_version(model),)


class ListWrapper:
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "any_1": (any_type, {"forceInput": True}),
        },
            "optional": {
                "any_2": (any_type, {"forceInput": True}),
            },
        }

    RETURN_TYPES = (any_type,)
    # RETURN_NAMES = ("STRING", )

    FUNCTION = "wrapper"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/List"

    INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (False, )
    DESCRIPTION = "把输入放到一个列表中，如 [a,b]和[c] => [[a,b],[c]]"

    def wrapper(self, any_1, any_2=None):
        if any_1 is None:
            return None,
        else:
            if any_2 is None:
                return ([any_1,],)
            else:
                return ([any_1, any_2],)


class ListUnWrapper:
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "lst": (any_type, {}),
        },
        }

    RETURN_TYPES = (any_type,)
    # RETURN_NAMES = ("STRING", )

    FUNCTION = "unwrapper"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/List"

    # INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (True, False)
    DESCRIPTION = "输出的是一个个的元素，相当于执行多次后面连接的那个节点，配合ListWrapper可以实现预览不同尺寸的图像"

    def unwrapper(self, lst):
        return (lst,)


class IndexOfList:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "lst": (any_type, {}),
                "index": ('INT', {'default': 0, 'step': 1, 'min': 0, 'max': 50}),
            }
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("any",)

    FUNCTION = "execute"

    CATEGORY = "EasyApi/List"

    DESCRIPTION = "根据索引过滤"

    def execute(self, lst, index):
        if isinstance(lst, list) and len(lst) > index:
            return (lst[index], )
        return (None, )


class IndexesOfList:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "lst": (any_type, {}),
                "index": ('STRING', {'default': "0"}),
            }
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("lst",)

    FUNCTION = "execute"

    CATEGORY = "EasyApi/List"

    DESCRIPTION = "根据索引(支持逗号分隔)过滤"

    def execute(self, lst, index):
        indices = [int(i.strip()) for i in index.split(",")]
        if isinstance(lst, list):
            filtered = [lst[i] for i in indices if 0 <= i < len(lst)]
            return (filtered,)
        return (None, )


class StringArea:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"value": ("STRING", {"default": "", "multiline": True})},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)

    FUNCTION = "execute"

    CATEGORY = "EasyApi/String"

    def execute(self, value):
        return (value,)


NODE_CLASS_MAPPINGS = {
    "GetImageBatchSize": GetImageBatchSize,
    "JoinList": JoinList,
    "IntToNumber": IntToNumber,
    "StringToList": StringToList,
    "IntToList": IntToList,
    "ListMerge": ListMerge,
    "ShowString": ShowString,
    "ShowInt": ShowInt,
    "ShowNumber": ShowNumber,
    "ShowFloat": ShowFloat,
    "ShowBoolean": ShowBoolean,
    "ColorPicker": ColorPicker,
    "ImageEqual": ImageEqual,
    "SDBaseVerNumber": SDBaseVerNumber,
    "ListWrapper": ListWrapper,
    "ListUnWrapper": ListUnWrapper,
    "SplitStringToList": SplitStringToList,
    "IndexOfList": IndexOfList,
    "IndexesOfList": IndexesOfList,
    "StringArea": StringArea,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "GetImageBatchSize": "GetImageBatchSize",
    "JoinList": "Join List",
    "IntToNumber": "Int To Number",
    "StringToList": "String To List",
    "IntToList": "Int To List",
    "ListMerge": "Merge List",
    "ShowString": "Show String",
    "ShowInt": "Show Int",
    "ShowNumber": "Show Number",
    "ShowFloat": "Show Float",
    "ShowBoolean": "Show Boolean",
    "ColorPicker": "Color Picker",
    "ImageEqual": "Image Equal Judgment",
    "SDBaseVerNumber": "SD Base Version Number",
    "ListWrapper": "ListWrapper",
    "ListUnWrapper": "ListUnWrapper",
    "SplitStringToList": "SplitStringToList",
    "IndexOfList": "IndexOfList",
    "IndexesOfList": "IndexesOfList",
    "StringArea": "StringArea",
}
