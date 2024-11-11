import torch
from segment_anything import SamAutomaticMaskGenerator
import json
import numpy as np
from segment_anything.utils.amg import area_from_rle, mask_to_rle_pytorch, rle_to_mask, batched_mask_to_box, \
    box_xyxy_to_xywh, coco_encode_rle
from pycocotools import mask as mask_utils

import nodes
from .util import tensor_to_pil


class SamAutoMaskSEGSAdvanced:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "sam_model": ('SAM_MODEL', {}),
                "image": ('IMAGE', {}),
            },
            "optional": {
                "points_per_side": ("INT",
                                    {
                                        "default": 32,
                                        "min": 1,
                                        "max": nodes.MAX_RESOLUTION,
                                        "step": 1,
                                        "tooltip": "沿图像一侧采样的点数。 总点数为points_per_side的平方。优先级盖玉point_grids, 如果为 None，则 'point_grids'采样点必须传"
                                    }),
                "points_per_batch": ("INT",
                                     {
                                         "default": 64,
                                         "min": 1,
                                         "max": nodes.MAX_RESOLUTION,
                                         "step": 1,
                                         "tooltip": "设置模型同时执行的点数。 数字越大，速度越快，但会占用更多的 GPU 内存"
                                     }),
                "pred_iou_thresh": ("FLOAT",
                                    {
                                        "default": 0.88,
                                        "min": 0,
                                        "max": 1.0,
                                        "step": 0.01,
                                        "tooltip": "置信度阈值。 置信度低于此值的掩码将被忽略"
                                    }),
                "stability_score_thresh": ("FLOAT",
                                           {
                                               "default": 0.95,
                                               "min": 0,
                                               "max": 1.0,
                                               "step": 0.01,
                                               "tooltip": "稳定性得分的过滤阈值，范围[0,1]"
                                           }),
                "stability_score_offset": ("FLOAT",
                                           {
                                               "default": 1.0,
                                               "min": 0,
                                               "max": 1.0,
                                               "step": 0.01,
                                               "tooltip": "计算稳定性得分时thresh偏移量。\n公式简单理解成 score= (mask > stability_score_thresh+stability_score_offset) / (mask > stability_score_thresh-stability_score_offset)"
                                           }),
                "box_nms_thresh": ("FLOAT",
                                   {
                                       "default": 0.7,
                                       "min": 0,
                                       "max": 1.0,
                                       "step": 0.01,
                                       "tooltip": "mask的bbox区域置信度阈值"
                                   }),
                "crop_n_layers": ("INT",
                                  {
                                      "default": 0,
                                      "min": 0,
                                      "max": 64,
                                      "step": 1,
                                      "tooltip": "递归重复检测层数，增大此值可以解决多个物体没拆分开的问题，但是速度会变慢"
                                  }),
                "crop_nms_thresh": ("FLOAT",
                                    {
                                        "default": 0.7,
                                        "min": 0,
                                        "max": 1.0,
                                        "step": 0.01,
                                        "tooltip": "crop_box区域置信度阈值"
                                    }),
                "crop_overlap_ratio": ("FLOAT",
                                       {
                                           "default": 512 / 1500,
                                           "min": 0,
                                           "max": 1.0,
                                           "step": 0.01,
                                           "tooltip": "多层检测时，设置裁剪重叠的程度，第一层使用此值。随着层数增加，重叠程度会减小"
                                       }),
                "crop_n_points_downscale_factor": ("INT",
                                                   {
                                                       "default": 1,
                                                       "min": 1,
                                                       "max": nodes.MAX_RESOLUTION,
                                                       "step": 1,
                                                       "tooltip": "用于计算第n层的points_per_side：int(points_per_side/crop_n_points_downscale_factor**n)"
                                                   }),
                "min_mask_region_area": ("INT",
                                         {
                                             "default": 0,
                                             "min": 0,
                                             "max": nodes.MAX_RESOLUTION,
                                             "step": 1,
                                             "tooltip": "最小区域面积。 用于过滤(忽略)小区域"
                                         }),
                "output_mode": (['uncompressed_rle', 'coco_rle'], {"default": "uncompressed_rle"}),
            },
        }

    RETURN_TYPES = ("MASK_RLE",)
    RETURN_NAMES = ("masks_rle",)

    FUNCTION = "generate"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/Detect"

    def generate(self,
                 sam_model,
                 image,
                 points_per_side: int = 32,
                 points_per_batch: int = 64,
                 pred_iou_thresh: float = 0.88,
                 stability_score_thresh: float = 0.95,
                 stability_score_offset: float = 1.0,
                 box_nms_thresh: float = 0.7,
                 crop_n_layers: int = 0,
                 crop_nms_thresh: float = 0.7,
                 crop_overlap_ratio: float = 512 / 1500,
                 crop_n_points_downscale_factor: int = 1,
                 min_mask_region_area: int = 0,
                 output_mode: str = "uncompressed_rle",
                 ):
        """
        # 沿图像一侧采样的点数。 总点数为 points_per_side**2。优先级盖玉point_grids, 如果为 None，则 'point_grids'采样点必须传。
        points_per_side = 32
        # 设置模型同时执行的点数。 数字越大，速度越快，但会占用更多的 GPU 内存。
        points_per_batch = 64
        # 置信度阈值。 置信度低于此值的掩码将被忽略。
        pred_iou_thresh = 0.88
        # 稳定性得分的过滤阈值，范围[0,1]
        stability_score_thresh = 0.95
        # 计算稳定性得分时thresh偏移量
        # 公式简单理解成 score= (mask > stability_score_thresh+stability_score_offset) / (mask > stability_score_thresh-stability_score_offset)
        stability_score_offset = 1.0
        # mask的bbox区域置信度阈值。
        box_nms_thresh = 0.7
        # 递归检测次数，增大此值可以解决多个物体没拆分开的问题，但是速度会变慢。
        crop_n_layers = 0
        # crop_box区域置信度阈值。
        crop_nms_thresh = 0.7
        # 设置裁剪重叠的程度，第一层使用此值。随着层数增加，重叠程度会减小。
        crop_overlap_ratio = 512 / 1500
        # 用于计算第n层的points_per_side：按int(points_per_side/crop_n_points_downscale_factor**n)。
        crop_n_points_downscale_factor = 1
        # 用于采样的点列表，归一化为[0,1]。列表中的第n个点用于第n个裁剪层。points_per_side不为空时不生效。Optional[List[np.ndarray]]
        point_grids = None
        # 最小区域面积。 用于过滤小区域
        min_mask_region_area = 0
        """
        point_grids = None
        # 判断是不是HQ
        encodeClassName = sam_model.image_encoder.__class__.__name__
        if encodeClassName == "ImageEncoderViTHQ":
            from custom_nodes.comfyui_segment_anything.sam_hq.automatic import SamAutomaticMaskGeneratorHQ
            from custom_nodes.comfyui_segment_anything.sam_hq.predictor import SamPredictorHQ
            samHQ = SamPredictorHQ(sam_model, True)
            mask_generator = SamAutomaticMaskGeneratorHQ(samHQ,
                                                         points_per_side,
                                                         points_per_batch,
                                                         pred_iou_thresh,
                                                         stability_score_thresh,
                                                         stability_score_offset,
                                                         box_nms_thresh,
                                                         crop_n_layers,
                                                         crop_nms_thresh,
                                                         crop_overlap_ratio,
                                                         crop_n_points_downscale_factor,
                                                         point_grids,
                                                         min_mask_region_area,
                                                         output_mode=output_mode)
        else:
            mask_generator = SamAutomaticMaskGenerator(sam_model,
                                                       points_per_side,
                                                       points_per_batch,
                                                       pred_iou_thresh,
                                                       stability_score_thresh,
                                                       stability_score_offset,
                                                       box_nms_thresh,
                                                       crop_n_layers,
                                                       crop_nms_thresh,
                                                       crop_overlap_ratio,
                                                       crop_n_points_downscale_factor,
                                                       point_grids,
                                                       min_mask_region_area,
                                                       output_mode=output_mode)
        image_pil = tensor_to_pil(image)
        image_np = np.array(image_pil)
        image_np_rgb = image_np[..., :3]

        masks = mask_generator.generate(image_np_rgb)
        return (masks,)


class SamAutoMaskSEGS(SamAutoMaskSEGSAdvanced):
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "sam_model": ('SAM_MODEL', {}),
                "image": ('IMAGE', {}),
                "output_mode": (['uncompressed_rle', 'coco_rle'], {"default": "uncompressed_rle"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("RLE_SEGS",)

    FUNCTION = "generate"

    OUTPUT_NODE = True
    CATEGORY = "EasyApi/Detect"

    # INPUT_IS_LIST = False
    # OUTPUT_IS_LIST = (False, False)

    def generate(self, sam_model, image, output_mode):
        masks = super().generate(sam_model, image, output_mode=output_mode)
        masksRle = json.JSONEncoder().encode(masks[0])
        return {"ui": {"segsRle": (masksRle,)}, "result": (masksRle,)}


class MaskToRle:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "mask": ('MASK', {}),
                "output_mode": (['uncompressed_rle', 'coco_rle'], {"default": "uncompressed_rle"}),
            },
        }

    RETURN_TYPES = ("MASK_RLE",)
    RETURN_NAMES = ("masks_rle",)

    FUNCTION = "convert"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/Detect"

    def convert(self, mask, output_mode):
        masksRle = []
        b, h, w = mask.shape
        rles = mask_to_rle_pytorch((mask > 0.15).bool())
        for i in range(b):
            single_rle = rles[i]
            area = area_from_rle(single_rle)
            bbox = box_xyxy_to_xywh(batched_mask_to_box(mask.bool())[i]).tolist()
            # stability_scores = calculate_stability_score(mask[i], mask_threshold, threshold_offset)
            if output_mode == "coco_rle":
                single_rle = coco_encode_rle(single_rle)

            masksRle.append(
                {
                    "segmentation": single_rle,
                    # 遮罩区域面积（像素点数）
                    "area": area,
                    # 蒙版矩形区域XYWH
                    "bbox": bbox,
                    # 用于生成此蒙版的图像的裁剪（XYWH格式）
                    "crop_box": [0, 0, w, h],
                    # "predicted_iou":  0.9494854211807251,
                    # 采样点坐标，自动情况下，蒙版区域内的任意一个点就行
                    # "point_coords": [[54.8475,1075.9375]],
                    # "stability_score": stability_scores.item(),
                }
            )
        return (masksRle,)


class RleToMask:
    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "masks_rle": ('MASK_RLE', {}),
                "rle_mode": (['uncompressed_rle', 'coco_rle'], {"default": "uncompressed_rle"}),
            },
        }

    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("masks",)

    FUNCTION = "convert"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/Detect"

    def convert(self, masks_rle, rle_mode='uncompressed_rle'):
        masks = []
        if isinstance(masks_rle, dict):
            list_rle = [masks_rle]
        else:
            list_rle = masks_rle
        for mask_rle in list_rle:
            if rle_mode == "coco_rle":
                mask_np = mask_utils.decode(mask_rle["segmentation"])
            else:
                mask_np = rle_to_mask(mask_rle["segmentation"])

            mask = torch.from_numpy(mask_np).to(torch.float32)

            masks.append(mask.unsqueeze(0))

        if len(masks) > 1:
            # 如果有多个图像，则将它们按维度0拼接在一起
            output_mask = torch.cat(masks, dim=0)
        else:
            output_mask = masks[0]

        return (output_mask,)


NODE_CLASS_MAPPINGS = {
    "SamAutoMaskSEGS": SamAutoMaskSEGS,
    "SamAutoMaskSEGSAdvanced": SamAutoMaskSEGSAdvanced,
    "MaskToRle": MaskToRle,
    "RleToMask": RleToMask,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "SamAutoMaskSEGS": "SamAutoMaskSEGS",
    "SamAutoMaskSEGSAdvanced": "SamAutoMaskSEGSAdvanced",
    "MaskToRle": "MaskToRle",
    "RleToMask": "RleToMask",
}
