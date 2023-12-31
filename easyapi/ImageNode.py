import base64
import io
import numpy as np
import torch
from PIL import ImageOps, Image
from nodes import LoadImage
from comfy.cli_args import args
from PIL.PngImagePlugin import PngInfo
import json
from json import JSONEncoder, JSONDecoder
from easyapi.util import tensor_to_pil


class Base64ToImage:
    """
    图片的base64格式还原成图片的张量
    """
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "base64Images": ("STRING", {"forceInput": True}),
        },
        }

    RETURN_TYPES = ("IMAGE",)
    # RETURN_NAMES = ("image", "mask")

    FUNCTION = "convert"

    CATEGORY = "EasyApi/Image"

    # INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (True, False)

    def convert(self, base64Images):
        # print(base64Image)
        base64ImageJson = JSONDecoder().decode(s=base64Images)
        images = []
        for base64Image in base64ImageJson:
            i = base64_to_image(base64Image)
            # 下面代码参考LoadImage
            i = ImageOps.exif_transpose(i)
            image = i.convert("RGB")
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None, ]
            # if 'A' in i.getbands():
            #     mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
            #     mask = 1. - torch.from_numpy(mask)
            # else:
            #     mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            images.append(image)

        return torch.stack(images, dim=0)[None, ]
        # return (torch.stack(images, dim=0)[None, ], mask.unsqueeze(0))


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

            # 创建一个BytesIO对象，用于临时存储图像数据
            image_data = io.BytesIO()
            metadata = None
            if not args.disable_metadata:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            # 将图像保存到BytesIO对象中，格式为PNG
            img.save(image_data, format='PNG', pnginfo=metadata)

            # 将BytesIO对象的内容转换为字节串
            image_data_bytes = image_data.getvalue()

            # 将图像数据编码为Base64字符串
            encoded_image = "data:image/png;base64," + base64.b64encode(image_data_bytes).decode('utf-8')
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
                "base64Images": ("STRING", {"forceInput": True}),
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


def base64_to_image(base64_string):
    # 去除前缀
    prefix, base64_data = base64_string.split(",", 1)

    # 从base64字符串中解码图像数据
    image_data = base64.b64decode(base64_data)

    # 创建一个内存流对象
    image_stream = io.BytesIO(image_data)

    # 使用PIL的Image模块打开图像数据
    image = Image.open(image_stream)

    return image


NODE_CLASS_MAPPINGS = {
    "Base64ToImage": Base64ToImage,
    "ImageToBase64": ImageToBase64,
    # "MaskToBase64": MaskToBase64,
    "Base64ToMask": Base64ToMask,
    "ImageToBase64Advanced": ImageToBase64Advanced,
    "MaskToBase64Image": MaskToBase64Image,
    "MaskImageToBase64": MaskImageToBase64,
    "LoadImageToBase64": LoadImageToBase64,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "Base64ToImage": "Base64 To Image",
    "ImageToBase64": "Image To Base64",
    # "MaskToBase64": "Mask To Base64",
    "Base64ToMask": "Base64 To Mask",
    "ImageToBase64Advanced": "Image To Base64 (Advanced)",
    "MaskToBase64Image": "Mask To Base64 Image",
    "MaskImageToBase64": "Mask Image To Base64",
    "LoadImageToBase64": "Load Image To Base64",
}
