import base64
import copy
import io
import os

import numpy as np
import torch
from PIL import ImageOps, Image, ImageSequence

import folder_paths
import node_helpers
from nodes import LoadImage
from comfy.cli_args import args
from PIL.PngImagePlugin import PngInfo
import json
from json import JSONEncoder, JSONDecoder
from .util import tensor_to_pil, pil_to_tensor, base64_to_image, image_to_base64, read_image_from_url


class LoadImageFromURL:
    """
    从远程地址读取图片
    """
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "urls": ("STRING", {"multiline": True, "default": "", "dynamicPrompts": False}),
        },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("images", "masks")

    FUNCTION = "convert"

    CATEGORY = "EasyApi/Image"

    # INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (True, True,)

    def convert(self, urls):
        urls = urls.splitlines()
        images = []
        masks = []
        for url in urls:
            if not url.strip().isspace():
                i = read_image_from_url(url.strip())
                i = ImageOps.exif_transpose(i)
                if i.mode == 'I':
                    i = i.point(lambda i: i * (1 / 255))
                image = i.convert("RGB")
                image = pil_to_tensor(image)
                images.append(image)
                if 'A' in i.getbands():
                    mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                    mask = 1. - torch.from_numpy(mask)
                else:
                    mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
                masks.append(mask.unsqueeze(0))

        return (images, masks, )


class LoadMaskFromURL:
    """
    从远程地址读取图片
    """
    _color_channels = ["red", "green", "blue", "alpha"]

    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "urls": ("STRING", {"multiline": True, "default": "", "dynamicPrompts": False}),
                "channel": (self._color_channels, {"default": self._color_channels[0]}),
            },
        }

    RETURN_TYPES = ("MASK", )
    RETURN_NAMES = ("masks", )

    FUNCTION = "convert"

    CATEGORY = "EasyApi/Image"

    # INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (True, True,)

    def convert(self, urls, channel=_color_channels[0]):
        urls = urls.splitlines()
        masks = []
        for url in urls:
            if not url.strip().isspace():
                i = read_image_from_url(url.strip())
                # 下面代码参考LoadImage
                i = ImageOps.exif_transpose(i)
                if i.getbands() != ("R", "G", "B", "A"):
                    i = i.convert("RGBA")
                c = channel[0].upper()
                if c in i.getbands():
                    mask = np.array(i.getchannel(c)).astype(np.float32) / 255.0
                    mask = torch.from_numpy(mask)
                    if c == 'A':
                        mask = 1. - mask
                else:
                    mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
                masks.append(mask.unsqueeze(0))
        return (masks,)


class Base64ToImage:
    """
    图片的base64格式还原成图片的张量
    """
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "base64Images": ("STRING", {"multiline": True, "default": "[\"\"]", "dynamicPrompts": False}),
        },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    # RETURN_NAMES = ("image", "mask")

    FUNCTION = "convert"

    CATEGORY = "EasyApi/Image"

    # INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (True, True)

    def convert(self, base64Images):
        # print(base64Image)
        base64ImageJson = JSONDecoder().decode(s=base64Images)
        images = []
        masks = []
        for base64Image in base64ImageJson:
            i = base64_to_image(base64Image)
            # 下面代码参考LoadImage
            i = ImageOps.exif_transpose(i)
            image = i.convert("RGB")
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None, ]
            if 'A' in i.getbands():
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            images.append(image)
            masks.append(mask.unsqueeze(0))

        return (images, masks,)


class ImageToBase64Advanced:
    def __init__(self):
        self.imageType = "image"

    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "images": ("IMAGE",),
            "imageType": (["image", "mask"], {"default": "image"}),
        },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("base64Images",)

    FUNCTION = "convert"
    # 作为输出节点，返回数据格式是{"ui": {output_name:value}, "result": (value,)}
    # ui中是websocket返回给前端的内容，result是py执行传给下个节点用的
    OUTPUT_NODE = True

    CATEGORY = "EasyApi/Image"

    # INPUT_IS_LIST = False
    # OUTPUT_IS_LIST = (False,False,)

    def convert(self, images, imageType=None, prompt=None, extra_pnginfo=None):
        if imageType is None:
            imageType = self.imageType

        result = list()
        for i in images:
            img = tensor_to_pil(i)
            metadata = None
            if not args.disable_metadata:
                metadata = PngInfo()
                if prompt is not None:
                    newPrompt = copy.deepcopy(prompt)
                    for idx in newPrompt:
                        node = newPrompt[idx]
                        if node['class_type'] == 'Base64ToImage' or node['class_type'] == 'Base64ToMask':
                            node['inputs']['base64Images'] = ""
                    metadata.add_text("prompt", json.dumps(newPrompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            # 将图像数据编码为Base64字符串
            encoded_image = image_to_base64(img, pnginfo=metadata)
            result.append(encoded_image)
        base64Images = JSONEncoder().encode(result)
        # print(images)
        return {"ui": {"base64Images": result, "imageType": [imageType]}, "result": (base64Images,)}


class ImageToBase64(ImageToBase64Advanced):
    def __init__(self):
        self.imageType = "image"

    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "images": ("IMAGE",),
        },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }


class MaskImageToBase64(ImageToBase64):
    def __init__(self):
        self.imageType = "mask"


class MaskToBase64Image(MaskImageToBase64):
    @classmethod
    def INPUT_TYPES(s):
        return {
                "required": {
                    "mask": ("MASK",),
                }
        }

    CATEGORY = "EasyApi/Image"

    RETURN_TYPES = ("STRING",)
    FUNCTION = "mask_to_base64image"

    def mask_to_base64image(self, mask):
        """将一个二维的掩码张量扩展为一个四维的彩色图像张量。具体的步骤如下：

        第一行，使用 torch.reshape 函数，将掩码张量的形状改变为(-1, 1, mask.shape[-2], mask.shape[-1])，
        其中 - 1 表示自动推断该维度的大小，1 表示增加一个新的维度，mask.shape[-2] 和 mask.shape[-1] 表示保持原来的最后两个维度不变。
        这样，掩码张量就变成了一个四维的张量，其中第二个维度只有一个通道。

        第二行，使用 torch.movedim 函数，将掩码张量的第二个维度（通道维度）移动到最后一个维度的位置，即将形状为(-1, 1, mask.shape[-2], mask.shape[-1])
        的张量变为(-1, mask.shape[-2], mask.shape[-1], 1) 的张量。这样，掩码张量就变成了一个符合图像格式的张量，其中最后一个维度表示通道数。

        第三行，使用 torch.Tensor.expand 函数，将掩码张量的最后一个维度（通道维度）扩展为 3，即将形状为(-1, mask.shape[-2], mask.shape[-1], 1) 的张量变为(-1, mask.shape[-2], mask.shape[-1], 3) 的张量。这样，掩码张量就变成了一个彩色图像张量，其中最后一个维度表示红、绿、蓝三个通道。

        这段代码的结果是一个与原来的掩码张量相同元素的彩色图像张量，表示掩码的颜色
        """
        images = mask.reshape((-1, 1, mask.shape[-2], mask.shape[-1])).movedim(1, -1).expand(-1, -1, -1, 3)
        return super().convert(images)


class MaskToBase64(MaskImageToBase64):
    @classmethod
    def INPUT_TYPES(s):
        return {
                "required": {
                    "mask": ("MASK",),
                }
        }

    CATEGORY = "EasyApi/Image"

    RETURN_TYPES = ("STRING",)
    FUNCTION = "mask_to_base64image"

    def mask_to_base64image(self, mask):
        return super().convert(mask)


class Base64ToMask:
    """
    mask的base64图片还原成mask的张量
    """
    _color_channels = ["red", "green", "blue", "alpha"]
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # "base64Images": ("STRING", {"forceInput": True}),
                "base64Images": ("STRING", {"multiline": True, "default": "[\"\"]", "dynamicPrompts": False}),
                "channel": (s._color_channels, {"default": s._color_channels[0]}), }
        }

    CATEGORY = "EasyApi/Image"

    RETURN_TYPES = ("MASK",)
    FUNCTION = "base64image_to_mask"

    def base64image_to_mask(self, base64Images, channel=_color_channels[0]):
        base64ImageJson = JSONDecoder().decode(s=base64Images)
        for base64Image in base64ImageJson:
            i = base64_to_image(base64Image)
            # 下面代码参考LoadImage
            i = ImageOps.exif_transpose(i)
            if i.getbands() != ("R", "G", "B", "A"):
                i = i.convert("RGBA")
            mask = None
            c = channel[0].upper()
            if c in i.getbands():
                mask = np.array(i.getchannel(c)).astype(np.float32) / 255.0
                mask = torch.from_numpy(mask)
                if c == 'A':
                    mask = 1. - mask
            else:
                mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")

        return (mask.unsqueeze(0),)


class LoadImageToBase64(LoadImage):
    RETURN_TYPES = ("STRING", "IMAGE", "MASK", )
    RETURN_NAMES = ("base64Images", "IMAGE", "MASK", )

    FUNCTION = "convert"
    OUTPUT_NODE = True

    CATEGORY = "EasyApi/Image"

    # INPUT_IS_LIST = False
    # OUTPUT_IS_LIST = (False,False,)

    def convert(self, image):
        img, mask = self.load_image(image)

        i = tensor_to_pil(img)
        # 创建一个BytesIO对象，用于临时存储图像数据
        image_data = io.BytesIO()

        # 将图像保存到BytesIO对象中，格式为PNG
        i.save(image_data, format='PNG')

        # 将BytesIO对象的内容转换为字节串
        image_data_bytes = image_data.getvalue()

        # 将图像数据编码为Base64字符串
        encoded_image = "[\"data:image/png;base64," + base64.b64encode(image_data_bytes).decode('utf-8') + "\"]"
        return encoded_image, img, mask


class LoadImageFromLocalPath:
    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {
                        "image_path": ("STRING", {"default": ""},)
                    },
                }

    CATEGORY = "EasyApi/Image"

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"
    def load_image(self, image_path):

        img = node_helpers.pillow(Image.open, image_path)

        output_images = []
        output_masks = []
        w, h = None, None

        excluded_formats = ['MPO']
        # 遍历图像的每一帧
        for i in ImageSequence.Iterator(img):
            # 旋转图像
            i = node_helpers.pillow(ImageOps.exif_transpose, i)

            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))
            # 将图像转换为RGB格式
            image = i.convert("RGB")

            if len(output_images) == 0:
                w = image.size[0]
                h = image.size[1]

            if image.size[0] != w or image.size[1] != h:
                continue

            # 将图像转换为浮点数组 (H,W,Channel)
            image = np.array(image).astype(np.float32) / 255.0
            # 先把图片转成3维张量，并再在最前面添加一个维度，变成4维(1, H, W,Channel)
            image = torch.from_numpy(image)[None,]
            # 如果图像包含alpha通道，则将其转换为掩码
            if 'A' in i.getbands():
                # 计算后结果数组中透明像素会是0
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                # 把数组中透明像素设为1
                mask = 1. - torch.from_numpy(mask)
            else:
                # 否则，创建一个64x64的零张量作为掩码
                mask = torch.zeros((64, 64,), dtype=torch.float32, device="cpu")
            # 将图像和掩码添加到输出列表中
            output_images.append(image)
            output_masks.append(mask.unsqueeze(0))

        if len(output_images) > 1 and img.format not in excluded_formats:
            # 如果有多个图像，则将它们按维度0拼接在一起
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)
        # 否则，返回单个图像和掩码
        else:
            output_image = output_images[0]
            output_mask = output_masks[0]
        # 返回输出图像和掩码
        return (output_image, output_mask)


class LoadMaskFromLocalPath:
    _color_channels = ["alpha", "red", "green", "blue"]
    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {
                        "image_path": ("STRING", {"default": ""}),
                        "channel": (s._color_channels, ),
                    }
                }

    CATEGORY = "EasyApi/Image"

    RETURN_TYPES = ("MASK",)
    FUNCTION = "load_mask"
    def load_mask(self, image_path, channel):
        i = node_helpers.pillow(Image.open, image_path)
        i = node_helpers.pillow(ImageOps.exif_transpose, i)
        if i.getbands() != ("R", "G", "B", "A"):
            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))
            i = i.convert("RGBA")
        mask = None
        c = channel[0].upper()
        if c in i.getbands():
            mask = np.array(i.getchannel(c)).astype(np.float32) / 255.0
            mask = torch.from_numpy(mask)
            if c == 'A':
                mask = 1. - mask
        else:
            mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
        return (mask.unsqueeze(0),)


class SaveImagesWithoutOutput:
    """
    保存图片，非输出节点
    """

    def __init__(self):
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "ComfyUI",
                                               "tooltip": "要保存的文件的前缀。支持的占位符：%width% %height% %year% %month% %day% %hour% %minute% %second%"}),
                "output_dir": ("STRING", {"default": "", "tooltip": "若为空，存放到output目录"}),
            },
            "optional": {
                "addMetadata": ("BOOLEAN", {"default": False, "label_on": "True", "label_off": "False"}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("STRING", )
    RETURN_NAMES = ("file_paths",)
    OUTPUT_TOOLTIPS = ("保存的图片路径列表",)

    FUNCTION = "save_images"

    CATEGORY = "EasyApi/Image"

    DESCRIPTION = "保存图像到指定目录，可根据返回的文件路径进行后续操作，此节点为非输出节点，适合批量处理和用于惰性求值的前置节点"
    OUTPUT_NODE = False

    def save_images(self, images, output_dir, filename_prefix="ComfyUI", addMetadata=False, prompt=None, extra_pnginfo=None):
        imageList = list()
        if not isinstance(images, list):
            imageList.append(images)
        else:
            imageList = images

        if output_dir is None or len(output_dir.strip()) == 0:
            output_dir = folder_paths.get_output_directory()

        results = list()
        for (index, images) in enumerate(imageList):
            for (batch_number, image) in enumerate(images):
                full_output_folder, filename, counter, subfolder, curr_filename_prefix = folder_paths.get_save_image_path(
                    filename_prefix, output_dir, image.shape[1], image.shape[0])
                img = tensor_to_pil(image)
                metadata = None
                if not args.disable_metadata and addMetadata:
                    metadata = PngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for x in extra_pnginfo:
                            metadata.add_text(x, json.dumps(extra_pnginfo[x]))

                filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
                file = f"{filename_with_batch_num}_{counter:05}_.png"
                image_save_path = os.path.join(full_output_folder, file)
                img.save(image_save_path, pnginfo=metadata, compress_level=self.compress_level)
                results.append(image_save_path)
                counter += 1

        return (results,)


class SaveSingleImageWithoutOutput:
    """
    保存图片，非输出节点
    """

    def __init__(self):
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "ComfyUI", "tooltip": "要保存的文件的前缀。可以使用格式化信息，如%date:yyyy-MM-dd%或%Empty Latent Image.width%"}),
                "full_file_name": ("STRING", {"default": "", "tooltip": "完整的相对路径文件名，包括扩展名。若为空，则使用filename_prefix生成带序号的文件名"}),
                "output_dir": ("STRING", {"default": "", "tooltip": "目标目录(绝对路径)，不会自动创建。若为空，存放到output目录"}),
            },
            "optional": {
                "addMetadata": ("BOOLEAN", {"default": False, "label_on": "True", "label_off": "False"}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("STRING", )
    RETURN_NAMES = ("file_path",)

    FUNCTION = "save_image"

    CATEGORY = "EasyApi/Image"

    DESCRIPTION = "保存图像到指定目录，可根据返回的文件路径进行后续操作，此节点为非输出节点，适合循环批处理和用于惰性求值的前置节点。只会处理一个"
    OUTPUT_NODE = False

    def save_image(self, image, full_file_name, output_dir, filename_prefix="ComfyUI", addMetadata=False, prompt=None, extra_pnginfo=None):
        imageList = list()
        if not isinstance(image, list):
            imageList.append(image)
        else:
            imageList = image

        if output_dir is None or len(output_dir.strip()) == 0:
            output_dir = folder_paths.get_output_directory()

        if not os.path.isdir(output_dir) or not os.path.isabs(output_dir):
            raise RuntimeError(f"目录 {output_dir} 不存在")

        if len(imageList) > 0:
            image = imageList[0]
            for (batch_number, image) in enumerate(image):
                img = tensor_to_pil(image)
                metadata = None
                if not args.disable_metadata and addMetadata:
                    metadata = PngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for x in extra_pnginfo:
                            metadata.add_text(x, json.dumps(extra_pnginfo[x]))

                if full_file_name is not None and len(full_file_name.strip()) > 0:
                    # full_file_name是相对路径，添加校验，并自动创建子目录
                    full_path = os.path.join(output_dir, full_file_name)
                    full_normpath_name = os.path.normpath(full_path)
                    file_dir = os.path.dirname(full_normpath_name)
                    # 确保路径是out_dir 的子目录
                    if not os.path.isabs(file_dir) or not file_dir.startswith(output_dir):
                        raise RuntimeError(f"文件 {full_file_name} 不在 {output_dir} 目录下")
                    if not os.path.isdir(file_dir):
                        os.makedirs(file_dir, exist_ok=True)
                    image_save_path = full_normpath_name
                else:
                    full_output_folder, filename, counter, subfolder, curr_filename_prefix = folder_paths.get_save_image_path(
                        filename_prefix, output_dir, image.shape[1], image.shape[0])
                    filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
                    file = f"{filename_with_batch_num}_{counter:05}_.png"
                    image_save_path = os.path.join(full_output_folder, file)

                img.save(image_save_path, pnginfo=metadata, compress_level=self.compress_level)
                return image_save_path,

        return (None,)


NODE_CLASS_MAPPINGS = {
    "Base64ToImage": Base64ToImage,
    "LoadImageFromURL": LoadImageFromURL,
    "LoadMaskFromURL": LoadMaskFromURL,
    "ImageToBase64": ImageToBase64,
    # "MaskToBase64": MaskToBase64,
    "Base64ToMask": Base64ToMask,
    "ImageToBase64Advanced": ImageToBase64Advanced,
    "MaskToBase64Image": MaskToBase64Image,
    "MaskImageToBase64": MaskImageToBase64,
    "LoadImageToBase64": LoadImageToBase64,
    "LoadImageFromLocalPath": LoadImageFromLocalPath,
    "LoadMaskFromLocalPath": LoadMaskFromLocalPath,
    "SaveImagesWithoutOutput": SaveImagesWithoutOutput,
    "SaveSingleImageWithoutOutput": SaveSingleImageWithoutOutput,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "Base64ToImage": "Base64 To Image",
    "LoadImageFromURL": "Load Image From Url",
    "LoadMaskFromURL": "Load Image From Url (As Mask)",
    "ImageToBase64": "Image To Base64",
    # "MaskToBase64": "Mask To Base64",
    "Base64ToMask": "Base64 To Mask",
    "ImageToBase64Advanced": "Image To Base64 (Advanced)",
    "MaskToBase64Image": "Mask To Base64 Image",
    "MaskImageToBase64": "Mask Image To Base64",
    "LoadImageToBase64": "Load Image To Base64",
    "LoadImageFromLocalPath": "Load Image From Local Path",
    "LoadMaskFromLocalPath": "Load Mask From Local Path",
    "SaveImagesWithoutOutput": "Save Images Without Output",
    "SaveSingleImageWithoutOutput": "Save Single Image Without Output",
}
