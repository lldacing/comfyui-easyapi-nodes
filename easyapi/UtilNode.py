import mimetypes
import os

import simplejson
import torch

import folder_paths
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
            },
            "optional": {
                "method": (["delimiter", "LF", "tab"], {"default": "delimiter", "tooltip": "分隔符选取方式"}),
            }
        }

    RETURN_TYPES = ("LIST",)

    FUNCTION = "convert"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/String"
    DESCRIPTION = "按分隔符把字符串拆分成列表。如 \"a,b,c\" => [a,b,c]"

    def convert(self, str, to_type, delimiter, method="delimiter"):
        if method == "LF":
            delimiter = "\n"
        elif method == "tab":
            delimiter = "\t"
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
                "index": ('INT', {'default': 0, 'step': 1, 'min': 0, 'max': 100000}),
            }
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("any",)

    FUNCTION = "execute"

    CATEGORY = "EasyApi/List"

    DESCRIPTION = "根据索引过滤，若index >= len(lst)，返回None"

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


class SliceList:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "lst": (any_type, {}),
                "start_index": ('INT', {'default': 0, 'step': 1, 'min': -100000, 'max': 100000}),
                "step": ('INT', {'default': 1, 'step': 1, 'min': -100000, 'max': 100000}),
                "end_index": ('INT', {'default': 100000, 'step': 1, 'min': -100000, 'max': 100000}),
                "reverse": ('BOOLEAN', {'default': False}),
            }
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("lst",)

    FUNCTION = "execute"

    CATEGORY = "EasyApi/List"

    DESCRIPTION = "列表切片, lst入参不是list时，返回None"

    def execute(self, lst, start_index, step, end_index, reverse):
        if isinstance(lst, list):
            sliceList = lst[start_index:end_index:step]
            if reverse:
                sliceList.reverse()
            return (sliceList, )
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


class ConvertTypeToAny:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"any": (any_type, {"forceInput": True})},
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("any",)

    FUNCTION = "execute"

    CATEGORY = "EasyApi/Utils"

    def execute(self, any):
        return (any,)


class LoadJsonStrToList:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "json_str": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ("LIST",)
    CATEGORY = "EasyApi/Utils"
    FUNCTION = "load_json"

    def load_json(self, json_str: str):
        if len(json_str.strip()) == 0:
            return ([],)
        json = simplejson.loads(json_str)
        if isinstance(json, list):
            return (json,)
        else:
            return ([json],)


class GetValueFromJsonObj:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "json": (any_type, {"forceInput": True, "tooltip": "json对象(非数组类型)"}),
                "key": ("STRING", {"default": ""}),
                "to_type": (["default", "str", "int", "float", "bool"], {"default": "default"}),
            },
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("any",)

    FUNCTION = "execute"

    CATEGORY = "EasyApi/Utils"

    def execute(self, json, key, to_type):
        if isinstance(json, dict) and key in json:
            if to_type == "str":
                return (str(json[key]),)
            if to_type == "int":
                return (int(json[key]),)
            if to_type == "float":
                return (float(json[key]),)
            if to_type == "bool":
                return (bool(json[key]),)
            return (json[key],)
        return (None,)


class FilterValueForList:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "lst": ("LIST", {"forceInput": True, "tooltip": "Object列表，如[{\"name\": \"\"}]"}),
                "key": ("STRING", {"default": ""}),
                "value": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("LIST",)
    RETURN_NAMES = ("LIST",)
    OUTPUT_TOOLTIPS = ("符合过滤条件的列表", )

    FUNCTION = "execute"

    CATEGORY = "EasyApi/Utils"

    DESCRIPTION = "根据key和value过滤出列表中符合条件的元素，返回符合条件的元素列表，如果找不到符合条件的元素则返回None"

    def execute(self, lst, key, value):
        # 过滤出lst中key等于value的元素列表，如果不存在相等的元素则返回None
        filtered = [i for i in lst if key in i and i[key] == value]
        if len(filtered) == 0:
            return (None,)

        return (filtered,)


class LoadLocalFilePath:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "directory": ("STRING", {"default": "", "tooltip": "若为空，遍历input目录"}),
                "max_depth": ("INT", {"default": 1, "min": 1, "max": 64, "step": 1, "tooltip": "查找最大目录层级"}),
                "file_type": (["image", "video", "text"], {"default": "image", "tooltip": "file_suffix值不为空时，此配置失效"}),
                "file_suffix": ("STRING", {"default": "", "tooltip": "指定过滤文件后缀，多个以|分割，如.png|.jpg"}),
            }
        }

    RETURN_TYPES = ("LIST", "INT",)
    RETURN_NAMES = ("paths", "count",)
    OUTPUT_TOOLTIPS = ("文件路径列表，若过滤不到文件返回空列表", "文件个数",)

    FUNCTION = "get_paths"

    CATEGORY = "EasyApi/Utils"

    DESCRIPTION = "根据条件遍历指定目录下文件路径"

    mime_types_dict = {
        'image': {'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/tiff'},
        'video': {'video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska'},
        'text': {'text/plain', 'text/html', 'text/css', 'text/csv'}
    }

    @classmethod
    def recursive_file_paths(cls, directory, max_depth, file_type, file_suffix, current_depth=1):
        """
        获取指定目录及其子目录中的图片文件路径（深度优先遍历）

        参数:
            directory (str): 要遍历的目录路径
            max_depth (int): 最大遍历层级
            current_depth (int): 当前遍历层级（默认值为1）

        返回:
            List[str]: 图片文件路径列表
        """

        image_paths = []

        if current_depth > max_depth:
            return image_paths

        with os.scandir(directory) as it:
            for item in it:
                if item.is_file():
                    if len(file_suffix.strip()) > 0:
                        suffixes = [s.strip().lower() for s in file_suffix.split('|')]
                        if any(item.name.lower().endswith(suffix) for suffix in suffixes):
                            image_paths.append(item.path)
                    elif file_type:
                        mime_type, _ = mimetypes.guess_type(item.path)
                        if mime_type in cls.mime_types_dict.get(file_type, set()):
                            image_paths.append(item.path)
                elif item.is_dir():
                    image_paths.extend(cls.recursive_file_paths(item.path, max_depth, file_type, file_suffix, current_depth + 1))
        return image_paths

    def get_paths(self, directory, max_depth, file_type, file_suffix):
        if directory is None or len(directory.strip()) == 0:
            directory = folder_paths.get_input_directory()
        image_paths = self.recursive_file_paths(directory, max_depth, file_type, file_suffix)

        return image_paths, len(image_paths),


class IsNoneOrEmpty:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "any": (any_type,)
            }
        }

    RETURN_TYPES = ("BOOLEAN",)
    RETURN_NAMES = ("boolean",)
    FUNCTION = "execute"
    CATEGORY = "EasyApi/Utils"
    DESCRIPTION = "判断输入是否为None、空列表、空字符串(trim后判断)、空字典"

    def execute(self, any):
        if any is None:
            return True,
        if isinstance(any, list):
            return (True if len(any) == 0 else False,)
        if isinstance(any, str):
            return (True if len(any.strip()) == 0 else False,)
        if isinstance(any, dict):
            return (True if len(any) == 0 else False,)
        return False


class IsNoneOrEmptyOptional:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "any": (any_type,)
            },
            "optional": {
                "default": (any_type, {"lazy": True})
            }
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("any",)
    FUNCTION = "execute"
    CATEGORY = "EasyApi/Utils"
    DESCRIPTION = "判断输入any是否为None、空列表、空字符串(trim后判断)、空字典，若为true，返回default的值，否则返回输入值"

    def execute(self, any, default=None):
        if any is None:
            return default,
        if isinstance(any, list):
            return (default if len(any) == 0 else any,)
        if isinstance(any, str):
            return (default if len(any.strip()) == 0 else any,)
        if isinstance(any, dict):
            return (default if len(any) == 0 else any,)
        return (any,)

    def check_lazy_status(self, any, default=None):
        if any is None:
            return ["default"]
        if isinstance(any, list):
            return ["default"] if len(any) == 0 else ["any"]
        if isinstance(any, str):
            return ["default"] if len(any.strip()) == 0 else ["any"]
        if isinstance(any, dict):
            return ["default"] if len(any) == 0 else ["any"]
        return ["any"]


class EmptyOutputNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "any": (any_type,)
            }
        }
    RETURN_TYPES = ()
    FUNCTION = "execute"
    CATEGORY = "EasyApi/Utils"
    DESCRIPTION = "可配合for循环批量处理图片，for循环后连接此输出节点"
    OUTPUT_NODE = True
    def execute(self, any):
        return ()


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
    "SliceList": SliceList,
    "StringArea": StringArea,
    "ConvertTypeToAny": ConvertTypeToAny,
    "GetValueFromJsonObj": GetValueFromJsonObj,
    "LoadJsonStrToList": LoadJsonStrToList,
    "FilterValueForList": FilterValueForList,
    "LoadLocalFilePath": LoadLocalFilePath,
    "IsNoneOrEmpty": IsNoneOrEmpty,
    "IsNoneOrEmptyOptional": IsNoneOrEmptyOptional,
    "EmptyOutputNode": EmptyOutputNode,
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
    "SliceList": "SliceList",
    "StringArea": "StringArea",
    "ConvertTypeToAny": "ConvertTypeToAny",
    "GetValueFromJsonObj": "GetValueFromJsonObj",
    "LoadJsonStrToList": "LoadJsonStrToList",
    "FilterValueForList": "FilterValueForList",
    "LoadLocalFilePath": "LoadLocalFilePath",
    "IsNoneOrEmpty": "IsNoneOrEmpty",
    "IsNoneOrEmptyOptional": "IsNoneOrEmptyOptional",
    "EmptyOutputNode": "EmptyOutputNode",
}
