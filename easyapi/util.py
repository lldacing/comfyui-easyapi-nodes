import base64
import io

import numpy as np
import torch
from PIL import Image


# Tensor to PIL
def tensor_to_pil(image):
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))


# Convert PIL to Tensor
def pil_2_tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


def base64_to_image(base64_string):
    # 去除前缀
    base64_list = base64_string.split(",", 1)
    if len(base64_list) == 2:
        prefix, base64_data = base64_list
    else:
        base64_data = base64_list[0]

    # 从base64字符串中解码图像数据
    image_data = base64.b64decode(base64_data)

    # 创建一个内存流对象
    image_stream = io.BytesIO(image_data)

    # 使用PIL的Image模块打开图像数据
    image = Image.open(image_stream)

    return image


def image_to_base64(pli_image, pnginfo=None):
    # 创建一个BytesIO对象，用于临时存储图像数据
    image_data = io.BytesIO()

    # 将图像保存到BytesIO对象中，格式为PNG
    pli_image.save(image_data, format='PNG', pnginfo=pnginfo)

    # 将BytesIO对象的内容转换为字节串
    image_data_bytes = image_data.getvalue()

    # 将图像数据编码为Base64字符串
    encoded_image = "data:image/png;base64," + base64.b64encode(image_data_bytes).decode('utf-8')

    return encoded_image
