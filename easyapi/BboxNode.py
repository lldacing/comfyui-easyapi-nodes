from json import JSONDecoder

import torch

import nodes
from .util import any_type


class BboxToCropData:
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "bbox": ("BBOX", {"forceInput": True}),
        },
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("crop_data", )

    FUNCTION = "convert"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/Bbox"

    INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (False, )
    DESCRIPTION = "可以把bbox(x,y,w,h)转换为crop_data((w,h),(x,y,x+w,y+w)，配合was节点使用"

    def convert(self, bbox):
        x, y, w, h = bbox
        return (((w, h), (x, y, x+w, y+h),),)


class BboxToCropData:
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "bbox": ("BBOX", {"forceInput": True}),
            },
            "optional": {
            "is_xywh": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("crop_data", )

    FUNCTION = "convert"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/Bbox"

    INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (False, )
    DESCRIPTION = "可以把bbox(x,y,w,h)转换为crop_data((w,h),(x,y,x+w,y+w)，配合was节点使用\nis_xywh表示bbox的格式是(x,y,w,h)还是(x,y,x1,y1)。"

    def convert(self, bbox, is_xywh=False):
        if is_xywh:
            x, y, w, h = bbox
        else:
            x, y, x_1, y_1 = bbox
            w = x_1 - x
            h = y_1 - y
        return (((w, h), (x, y, x+w, y+h),),)


class BboxToBbox:
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
                "bbox": ("BBOX", {"forceInput": True}),
            },
            "optional": {
                "is_xywh": ("BOOLEAN", {"default": False}),
                "to_xywh": ("BOOLEAN", {"default": False})
            }
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("bbox", )

    FUNCTION = "convert"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/Bbox"

    INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (False, )
    DESCRIPTION = "可以把bbox转换为(x1,y1,x2,y2)或(x,y,w,h)，返回任意类型，配合其它bbox节点使用\n is_xywh表示输入的bbox的格式是(x,y,w,h)还是(x,y,x1,y1)。\n to_xywh表示返回的bbox的格式是(x,y,w,h)还是(x,y,x1,y1)。"

    def convert(self, bbox, is_xywh=False, to_xywh=False):
        if is_xywh:
            x, y, w, h = bbox
        else:
            x, y, x_1, y_1 = bbox
            w = x_1 - x
            h = y_1 - y
        if to_xywh:
            return ((x, y, w, h),)
        else:
            return ((x, y, x+w, y+h),)


class BboxesToBboxes:
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
                "bboxes": ("BBOX", {"forceInput": True}),
            },
            "optional": {
                "is_xywh": ("BOOLEAN", {"default": False}),
                "to_xywh": ("BOOLEAN", {"default": False})
            }
        }

    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ("bbox", )

    FUNCTION = "convert"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/Bbox"

    INPUT_IS_LIST = False
    OUTPUT_IS_LIST = (False, )
    DESCRIPTION = "可以把bbox转换为(x1,y1,x2,y2)或(x,y,w,h)，返回任意类型，配合其它bbox节点使用\n is_xywh表示输入的bbox的格式是(x,y,w,h)还是(x,y,x1,y1)。\n to_xywh表示返回的bbox的格式是(x,y,w,h)还是(x,y,x1,y1)。"

    def convert(self, bboxes, is_xywh=False, to_xywh=False):
        new_bboxes = list()
        for bbox in bboxes:
            if is_xywh:
                x, y, w, h = bbox
            else:
                x, y, x_1, y_1 = bbox
                w = x_1 - x
                h = y_1 - y
            if to_xywh:
                new_bboxes.append((x, y, w, h))
            else:
                new_bboxes.append((x, y, x+w, y+h))
        return (new_bboxes,)


class SelectBbox:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "index": ('INT', {'default': 0, 'step': 1, 'min': 0, 'max': 50}),
            },
            "optional": {
                "bboxes": ('BBOX', {'forceInput': True}),
                "bboxes_json": ('STRING', {'forceInput': True}),
            }
        }

    RETURN_TYPES = ("BBOX",)
    RETURN_NAMES = ("bbox",)

    FUNCTION = "select"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/Bbox"

    # INPUT_IS_LIST = False
    # OUTPUT_IS_LIST = (False, False)
    DESCRIPTION = "根据索引过滤"

    def select(self, index, bboxes=None, bboxes_json=None):
        if bboxes is None:
            if bboxes_json is not None:
                _bboxes = JSONDecoder().decode(bboxes_json)
                if len(_bboxes) > index:
                    return (_bboxes[index], )
        if isinstance(bboxes, list) and len(bboxes) > index:
            return (bboxes[index], )
        return (None, )


class SelectBboxes:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "index": ('STRING', {'default': "0"}),
            },
            "optional": {
                "bboxes": ('BBOX', {'forceInput': True}),
                "bboxes_json": ('STRING', {'forceInput': True}),
            }
        }

    RETURN_TYPES = ("BBOX",)
    RETURN_NAMES = ("bboxes",)

    FUNCTION = "select"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/Bbox"

    # INPUT_IS_LIST = False
    # OUTPUT_IS_LIST = (False, False)
    DESCRIPTION = "根据索引(支持逗号分隔)过滤"

    def select(self, index, bboxes=None, bboxes_json=None):
        indices = [int(i) for i in index.split(",")]
        if bboxes is None:
            if bboxes_json is not None:
                _bboxes = JSONDecoder().decode(bboxes_json)
                filtered_bboxes = [_bboxes[i] for i in indices if 0 <= i < len(_bboxes)]
                return (filtered_bboxes, )
        if isinstance(bboxes, list):
            filtered_bboxes = [bboxes[i] for i in indices if 0 <= i < len(bboxes)]
            return (filtered_bboxes,)
        return (None, )


class CropImageByBbox:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "bbox": ("BBOX",),
                "margin": ("INT", {"default": 16, "tooltip": "bbox矩形区域向外扩张的像素距离"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "BBOX", "INT", "INT")
    RETURN_NAMES = ("crop_image", "mask", "crop_bbox", "w", "h")
    FUNCTION = "crop"
    CATEGORY = "EasyApi/Bbox"
    DESCRIPTION = "根据bbox区域裁剪图片。 bbox的格式是左上角和右下角坐标： [x,y,x1,y1]"

    def crop(self, image: torch.Tensor, bbox, margin):
        x, y, x1, y1 = bbox
        w = x1 - x
        h = y1 - y
        image_height = image.shape[1]
        image_width = image.shape[2]
        # 左上角坐标
        x = min(x, image_width)
        y = min(y, image_height)
        # 右下角坐标
        to_x = min(w + x + margin, image_width)
        to_y = min(h + y + margin, image_height)
        # 防止越界
        x = max(0, x - margin)
        y = max(0, y - margin)
        to_x = max(0, to_x)
        to_y = max(0, to_y)
        # 按区域截取图片
        crop_img = image[:, y:to_y, x:to_x, :]
        new_bbox = (x, y, to_x, to_y)
        # 创建与image相同大小的全零张量作为遮罩
        mask = torch.zeros((image_height, image_width), dtype=torch.uint8)  # 使用uint8类型
        # 在mask上设置new_bbox区域为1
        mask[new_bbox[1]:new_bbox[3], new_bbox[0]:new_bbox[2]] = 1
        # 如果需要转换为浮点数，并且增加一个通道维度, 形状变为 (1, height, width)
        mask_tensor = mask.unsqueeze(0)
        return crop_img, mask_tensor, new_bbox, to_x - x, to_y - y,


class CropTargetSizeImageByBbox:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "bbox": ("BBOX",{"forceInput": True, "tooltip": "参考区域坐标"}),
                "width": ("INT", {"default": 512, "min": 1, "max": nodes.MAX_RESOLUTION, "step": 1,  "tooltip": "目标宽度"}),
                "height": ("INT", {"default": 512, "min": 1, "max": nodes.MAX_RESOLUTION, "step": 1, "tooltip": "目标高度"}),
                "contain": ("BOOLEAN", {"default": False, "tooltip": "是否始终包含bbox完整区域"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "BBOX", "INT", "INT")
    RETURN_NAMES = ("crop_image", "mask", "crop_bbox", "w", "h")
    FUNCTION = "crop"
    CATEGORY = "EasyApi/Bbox"
    DESCRIPTION = "根据bbox区域中心裁剪指定大小图片。 bbox的格式是左上角和右下角坐标： [x,y,x1,y1]"

    def calc_area(self, image_width, image_height, rect_top_left, rect_bottom_right, w, h):
        """
        以给定的矩形中心点为中心计算指定宽高的矩形框坐标
        Args:
            image_width: 图片高度
            image_height: 图片宽度
            rect_top_left: 矩形框左上角坐标
            rect_bottom_right: 矩形框右下角坐标
            w: 目标宽度
            h: 目标高度

        Returns:

        """
        # 计算矩形的宽和高
        x, y = rect_top_left
        x1, y1 = rect_bottom_right

        # 否则，计算矩形的中心(取整)
        center_x = (x + x1) // 2
        center_y = (y + y1) // 2
        left_w = w // 2
        right_w = w - left_w
        top_h = h // 2
        bottom_h = h - top_h

        # 计算新的坐标
        new_top_left_x = max(0, center_x - left_w)
        new_top_left_y = max(0, center_y - top_h)
        new_bottom_right_x = min(image_width, center_x + right_w)
        new_bottom_right_y = min(image_height, center_y + bottom_h)

        # 如果坐标越界，调整坐标
        if new_top_left_x == 0:
            # 左边可能超过边界了，尝试把左边超出部分加到右边
            new_bottom_right_x = min(image_width, new_bottom_right_x + (left_w - center_x))
        elif new_bottom_right_x == image_width:
            # 右边可能超过边界了，尝试把右边超出部分加到左边
            new_top_left_x = max(0, new_top_left_x - (center_x + left_w - image_width))

        if new_top_left_y == 0:
            # 上边可能超过边界了，尝试把上边超出部分加到下边
            new_bottom_right_y = min(image_height, new_bottom_right_y + (top_h - center_y))
        elif new_bottom_right_y == image_height:
            # 下边可能超过边界了，尝试把下边超出部分加到上边
            new_top_left_y = max(0, new_top_left_y - (center_y + top_h - image_height))

        return new_top_left_x, new_top_left_y, new_bottom_right_x, new_bottom_right_y

    def crop(self, image: torch.Tensor, bbox, width, height, contain):
        x, y, x1, y1 = bbox
        image_height = image.shape[1]
        image_width = image.shape[2]

        new_x, new_y, to_x, to_y = self.calc_area(image_width, image_height, (x, y), (x1, y1), width, height)

        if contain:
            new_x = min(new_x, x)
            new_y = min(new_y, y)
            to_x = max(to_x, x1)
            to_y = max(to_y, y1)
        # 按区域截取图片
        crop_img = image[:, new_y:to_y, new_x:to_x, :]
        new_bbox = (new_x, new_y, to_x, to_y)
        # 创建与image相同大小的全零张量作为遮罩
        mask = torch.zeros((image_height, image_width), dtype=torch.uint8)  # 使用uint8类型
        # 在mask上设置new_bbox区域为1
        mask[new_bbox[1]:new_bbox[3], new_bbox[0]:new_bbox[2]] = 1
        # 如果需要转换为浮点数，并且增加一个通道维度, 形状变为 (1, height, width)
        mask_tensor = mask.unsqueeze(0)
        return crop_img, mask_tensor, new_bbox, to_x - new_x, to_y - new_y,


class MaskByBboxes:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "bboxes": ("BBOX",),
            }
        }

    RETURN_TYPES = ("MASK", )
    RETURN_NAMES = ("mask", )
    FUNCTION = "crop"
    CATEGORY = "EasyApi/Bbox"
    DESCRIPTION = "根据bboxes生成遮罩, bboxes格式是(x, y, w, h)"

    def crop(self, image: torch.Tensor, bboxes):
        image_height = image.shape[1]
        image_width = image.shape[2]

        # 创建与image相同大小的全零张量作为遮罩
        mask = torch.zeros((image_height, image_width), dtype=torch.uint8)
        # 在mask上设置new_bbox区域为1
        for bbox in bboxes:
            x, y, w, h = bbox
            mask[y:y+h, x:x+w] = 1
        # 如果需要转换为浮点数，并且增加一个通道维度, 形状变为 (1, height, width)
        mask_tensor = mask.unsqueeze(0)
        return mask_tensor,


NODE_CLASS_MAPPINGS = {
    "BboxToCropData": BboxToCropData,
    "BboxToBbox": BboxToBbox,
    "BboxesToBboxes": BboxesToBboxes,
    "SelectBbox": SelectBbox,
    "SelectBboxes": SelectBboxes,
    "CropImageByBbox": CropImageByBbox,
    "MaskByBboxes": MaskByBboxes,
    "CropTargetSizeImageByBbox": CropTargetSizeImageByBbox,
}


NODE_DISPLAY_NAME_MAPPINGS = {
    "BboxToCropData": "BboxToCropData",
    "BboxToBbox": "BboxToBbox",
    "BboxesToBboxes": "BboxesToBboxes",
    "SelectBbox": "SelectBbox",
    "SelectBboxes": "SelectBboxes",
    "CropImageByBbox": "CropImageByBbox",
    "MaskByBboxes": "MaskByBboxes",
    "CropTargetSizeImageByBbox": "CropTargetSizeImageByBbox",
}
