from segment_anything import SamAutomaticMaskGenerator
import json
import numpy as np

from easyapi.util import tensor_to_pil

class SamAutoMaskSEGS:
    @classmethod
    def INPUT_TYPES(self):
        return {"required": {
            "sam_model": ('SAM_MODEL', {}),
            "image": ('IMAGE', {}),
            "output_mode": (['uncompressed_rle', 'coco_rel'], {"default": "uncompressed_rle"}),
        },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("RLE_SEGS", )

    FUNCTION = "generate"

    OUTPUT_NODE = True
    CATEGORY = "EasyApi/Detect"

    # INPUT_IS_LIST = False
    # OUTPUT_IS_LIST = (False, False)

    def generate(self, sam_model, image, output_mode):
        # 判断是不是HQ
        encodeClassName = sam_model.image_encoder.__class__.__name__
        if encodeClassName == "ImageEncoderViTHQ":
            from custom_nodes.comfyui_segment_anything.sam_hq.automatic import SamAutomaticMaskGeneratorHQ
            from custom_nodes.comfyui_segment_anything.sam_hq.predictor import SamPredictorHQ
            samHQ = SamPredictorHQ(sam_model, True)
            mask_generator = SamAutomaticMaskGeneratorHQ(samHQ, output_mode=output_mode)
        else:
            mask_generator = SamAutomaticMaskGenerator(sam_model, output_mode=output_mode)
        image_pil = tensor_to_pil(image)
        image_np = np.array(image_pil)
        image_np_rgb = image_np[..., :3]

        masks = mask_generator.generate(image_np_rgb)
        masksRle = json.JSONEncoder().encode(masks)
        return {"ui": {"segsRle": (masksRle,)}, "result": (masksRle,)}


NODE_CLASS_MAPPINGS = {
    "SamAutoMaskSEGS": SamAutoMaskSEGS,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "SamAutoMaskSEGS": "SamAutoMaskSEGS",
}
