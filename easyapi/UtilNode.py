import gc
import mimetypes
import os
import shutil
from collections import defaultdict

import simplejson
import torch

import folder_paths
from comfy.model_patcher import ModelPatcher
import comfy.model_base
import comfy.model_management as mm
from server import PromptServer
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

    DESCRIPTION = "合并两个列表。如 [1,2] 和 [3,4] => [1,2,3,4]"

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
        if isinstance(lst, (list, tuple)) and len(lst) > index:
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
        if isinstance(lst, (list, tuple)):
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
        if isinstance(lst, (list, tuple)):
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
        if isinstance(json, (list, tuple)):
            return (json,)
        else:
            return ([json],)


class ConvertToJsonStr:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "obj": (any_type, {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json_str",)
    CATEGORY = "EasyApi/Utils"
    FUNCTION = "to_json_str"
    DESCRIPTION = "将任意对象序列化为json字符串"

    def to_json_str(self, obj):
        json = simplejson.dumps(obj, ignore_nan=True)
        return (json,)


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

    RETURN_TYPES = ("LIST", "INT", "LIST", "STRING", )
    RETURN_NAMES = ("paths", "count", "relative_path", "base_dir", )
    OUTPUT_TOOLTIPS = ("文件路径列表，若过滤不到文件返回空列表", "文件个数", "文件相对路径列表", "保存的根目录", )

    FUNCTION = "get_paths"

    CATEGORY = "EasyApi/Utils"

    DESCRIPTION = "根据条件遍历指定目录下文件路径"

    mime_types_dict = {
        'image': {'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/tiff'},
        'video': {'video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska'},
        'text': {'text/plain', 'text/html', 'text/css', 'text/csv'}
    }

    @classmethod
    def recursive_file_paths(cls, directory, max_depth, file_type, file_suffix, base_directory=None, current_depth=1):
        """
        获取指定目录及其子目录中的图片文件路径（深度优先遍历）

        参数:
            directory (str): 要遍历的目录路径
            max_depth (int): 最大遍历层级
            file_type (str): 文件类型（如 'image'）
            file_suffix (str): 文件后缀（多个后缀用 '|' 分隔）
            base_directory (str): 根目录路径（用于计算相对路径，默认为 None）
            current_depth (int): 当前遍历层级（默认值为1）

        返回:
            List[str]: 图片文件路径列表
            List[str]: 图片文件相对路径列表
        """

        image_paths = []
        relative_image_paths = []

        if base_directory is None:
            base_directory = directory

        if current_depth > max_depth:
            return image_paths, relative_image_paths

        with os.scandir(directory) as it:
            for item in it:
                if item.is_file():
                    if len(file_suffix.strip()) > 0:
                        suffixes = [s.strip().lower() for s in file_suffix.split('|')]
                        if any(item.name.lower().endswith(suffix) for suffix in suffixes):
                            image_paths.append(item.path)
                            relative_image_paths.append(os.path.relpath(item.path, base_directory))
                    elif file_type:
                        mime_type, _ = mimetypes.guess_type(item.path)
                        if mime_type in cls.mime_types_dict.get(file_type, set()):
                            image_paths.append(item.path)
                            relative_image_paths.append(os.path.relpath(item.path, base_directory))
                elif item.is_dir():
                    sub_image_paths, sub_relative_image_paths = cls.recursive_file_paths(
                        item.path, max_depth, file_type, file_suffix, base_directory, current_depth + 1
                    )
                    image_paths.extend(sub_image_paths)
                    relative_image_paths.extend(sub_relative_image_paths)
        return image_paths, relative_image_paths

    def get_paths(self, directory, max_depth, file_type, file_suffix):
        if directory is None or len(directory.strip()) == 0:
            directory = folder_paths.get_input_directory()
        image_paths, relative_image_paths = self.recursive_file_paths(directory, max_depth, file_type, file_suffix)

        return image_paths, len(image_paths), relative_image_paths, directory,


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

    def execute(self, any=None):
        if any is None:
            return True,
        if isinstance(any, (list, tuple)):
            return (True if len(any) == 0 else False,)
        if isinstance(any, str):
            return (True if len(any.strip()) == 0 else False,)
        if isinstance(any, dict):
            return (True if len(any) == 0 else False,)
        return False,


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
    DESCRIPTION = "判断输入any是否为None、空列表、空字符串(trim后判断)、空字典，若为true，返回default的值，否则返回输入值。"
    INPUT_IS_LIST = True
    OUTPUT_IS_LIST = (True,)

    def execute(self, any=None, default=None):
        if any is None or len(any) == 0:
            return default,
        if isinstance(any[0], (list, tuple, dict)):
            return (default if len(any[0]) == 0 else any,)
        if isinstance(any[0], str):
            return (default if len(any[0].strip()) == 0 else any,)
        return (any,)

    def check_lazy_status(self, any=None, default=None):
        if any is None or len(any) == 0:
            return ["default"]
        if isinstance(any[0], (list, tuple, dict)):
            return ["default"] if len(any[0]) == 0 else ["any"]
        if isinstance(any[0], str):
            return ["default"] if len(any[0].strip()) == 0 else ["any"]
        return []


class IfElseForEmptyObject:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "boolean": ("BOOLEAN",),
                "on_true": (any_type, {"lazy": True}),
                "on_false": (any_type, {"lazy": True}),
            },
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("any",)
    FUNCTION = "execute"
    CATEGORY = "EasyApi/Utils"
    INPUT_IS_LIST = True
    OUTPUT_IS_LIST = (True,)

    def check_lazy_status(self, boolean, on_true=None, on_false=None):
        if boolean[0] and (on_true is None or len(on_true) == 0 or (not isinstance(on_true[0], (list, tuple, str, dict)) or len(on_true[0]) > 0)):
            return ["on_true"]
        if not boolean[0] and (on_false is None or len(on_false) == 0 or (not isinstance(on_false[0], (list, tuple, str, dict)) or len(on_false[0]) > 0)):
            return ["on_false"]

    def execute(self, boolean, on_true = None, on_false = None):
        return on_true if boolean[0] else on_false,


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


class SaveTextToFileByImagePath:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_path": ("STRING", {"forceInput": False}),
                "text": ("STRING", {"forceInput": False, "dynamicPrompts": False, "multiline": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text_path",)
    FUNCTION = "execute"
    CATEGORY = "EasyApi/Utils"
    DESCRIPTION = "把文本内容保存到图片路径同名的txt文件中"

    def execute(self, image_path, text):
        # 校验图片路径是否存在
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # 校验文本内容是否为空
        if not text:
            raise ValueError("The text cannot be empty")

        # 获取图片文件名，不包括扩展名
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        # 创建txt文件路径
        dir_name = os.path.dirname(image_path)
        # 创建txt文件路径
        txt_path = os.path.join(dir_name, f"{base_name}.txt")

        # 写入文本内容到txt文件
        with open(txt_path, 'w', encoding='utf-8') as file:
            file.write(text)

        return (txt_path,)


class SaveTextToLocalFile:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_path": ("STRING", {"forceInput": False, "tooltip": "保存的文件全路径，不会自动创建文件目录"}),
                "text": ("STRING", {"forceInput": False, "dynamicPrompts": False, "multiline": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text_path",)
    FUNCTION = "execute"
    CATEGORY = "EasyApi/Utils"
    DESCRIPTION = "把文本内容保存指定文件中"

    def execute(self, text_path, text):
        # 路径需要存在
        dir_name = os.path.dirname(text_path)
        if not os.path.isdir(dir_name):
            raise FileNotFoundError(f"dir not found: {dir_name}")

        # 写入文本内容到文件
        with open(text_path, 'w', encoding='utf-8') as file:
            file.write(text)

        return (text_path,)


class ReadTextFromLocalFile:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_path": ("STRING", {"forceInput": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "execute"
    CATEGORY = "EasyApi/Utils"
    DESCRIPTION = "把文本内容保存到图片路径同名的txt文件中"

    def execute(self, text_path):
        if not os.path.isfile(text_path):
            raise FileNotFoundError(f"file not found: {text_path}")

            # 获取文件的 MIME 类型
        mime_type, _ = mimetypes.guess_type(text_path)

        if mime_type is None or (not mime_type.startswith('text/') and mime_type != 'application/json'):
            raise ValueError(f"Unsupported file type: {mime_type}")

        # 读取文本内容
        try:
            with open(text_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except Exception as e:
            raise ValueError(f"Error reading file: {e}")

        return (text,)


class CopyAndRenameFiles:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "directory": ("STRING", {"forceInput": False, "tooltip": "源目录"}),
                "save_directory": ("STRING", {"default": "", "tooltip": "目标目录，为空时重命名原文件"}),
                "prefix": ("STRING", {"default": "", "tooltip": "新文件名前缀"}),
                "name_to_num": ("BOOLEAN", {"default": True, "tooltip": "后缀是否使用在对应目录的序号"}),
            }
        }

    RETURN_TYPES = ("STRING", )
    RETURN_NAMES = ("save_directory", )
    FUNCTION = "execute"
    CATEGORY = "EasyApi/Utils"
    DESCRIPTION = "把给定目录下的文件复制到指定目录"

    def execute(self, directory, save_directory, prefix, name_to_num):
        """
        递归遍历目录及其子目录中的文件，重命名或复制并重命名文件，添加自定义前缀。
        如果 save_directory 为空，重命名原文件；否则，复制并重命名到目标目录，并保持层级结构，文件名为所在目录的计数编号。

        :param directory: 需要重命名文件的目录路径
        :param prefix: 自定义前缀
        :param save_directory: 保存重命名文件的目录路径（可以为空）
        :param name_to_num: 重命名文件名为数字
        """
        count_dict = defaultdict(int)  # 用于存储每个目录的计数器

        for root, _, files in os.walk(directory):
            for filename in files:
                old_path = os.path.join(root, filename)
                if os.path.isfile(old_path):
                    count_dict[root] += 1  # 增加当前目录的计数器
                    ext = os.path.splitext(filename)[1]
                    if prefix and len(prefix.strip()) > 0:
                        if name_to_num:
                            new_filename = f"{prefix.strip()}_{count_dict[root]}"
                        else:
                            new_filename = f"{prefix.strip()}_{filename}"

                    else:
                        if name_to_num:
                            new_filename = f"{count_dict[root]}{ext}"
                        else:
                            new_filename = filename

                    # 如果 save_directory 不为空，复制并重命名到目标目录，并保持层级结构
                    if save_directory and len(save_directory.strip()) > 0:
                        # 计算保存文件的目标目录
                        relative_path = os.path.relpath(root, directory)
                        target_dir = os.path.join(save_directory, relative_path)
                        if not os.path.exists(target_dir):
                            os.makedirs(target_dir)
                        new_path = os.path.join(target_dir, new_filename)
                        shutil.copyfile(old_path, new_path)
                        print(f"复制并重命名: {old_path} -> {new_path}")
                    else:
                        # 否则重命名原文件
                        new_path = os.path.join(root, new_filename)
                        os.rename(old_path, new_path)
                        print(f"重命名: {old_path} -> {new_path}")

        return (save_directory, )


class TryFreeMemory:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "a": (any_type, {"forceInput": True}),
                "do_gc": ("BOOLEAN", {"default": False, "tooltip": "设置垃圾回收标志，不会立即执行垃圾回收，在本次流运行结束时ComfyUI主体会根据标识自动执行一次垃圾回收（相当于不会缓存结果）"}),
                "unload_models": ("BOOLEAN", {"default": False, "tooltip": "释放显存中已经无效的模型，会立即执行一次"}),
            }
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("a",)
    FUNCTION = "execute"
    CATEGORY = "EasyApi/Utils"
    def execute(self, a, do_gc, unload_models):
        if unload_models:
            mm.unload_all_models()

        PromptServer.instance.prompt_queue.set_flag("unload_models", unload_models)
        PromptServer.instance.prompt_queue.set_flag("free_memory", do_gc)

        return (a,)


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
    "ConvertToJsonStr": ConvertToJsonStr,
    "FilterValueForList": FilterValueForList,
    "LoadLocalFilePath": LoadLocalFilePath,
    "IsNoneOrEmpty": IsNoneOrEmpty,
    "IsNoneOrEmptyOptional": IsNoneOrEmptyOptional,
    "EmptyOutputNode": EmptyOutputNode,
    "SaveTextToFileByImagePath": SaveTextToFileByImagePath,
    "CopyAndRenameFiles": CopyAndRenameFiles,
    "SaveTextToLocalFile": SaveTextToLocalFile,
    "ReadTextFromLocalFile": ReadTextFromLocalFile,
    "TryFreeMemory": TryFreeMemory,
    "IfElseForEmptyObject": IfElseForEmptyObject,
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
    "ConvertToJsonStr": "ConvertToJsonStr",
    "FilterValueForList": "FilterValueForList",
    "LoadLocalFilePath": "LoadLocalFilePath",
    "IsNoneOrEmpty": "IsNoneOrEmpty",
    "IsNoneOrEmptyOptional": "IsNoneOrEmptyOptional",
    "EmptyOutputNode": "EmptyOutputNode",
    "SaveTextToFileByImagePath": "SaveTextToFileByImagePath",
    "CopyAndRenameFiles": "CopyAndRenameFiles",
    "SaveTextToLocalFile": "SaveTextToLocalFile",
    "ReadTextFromLocalFile": "ReadTextFromLocalFile",
    "TryFreeMemory": "TryFreeMemory",
    "IfElseForEmptyObject": "If Else For Empty Object",
}
