import os

from PIL import Image
from json import JSONEncoder, JSONDecoder
import numpy as np

from .util import tensor_to_pil, pil_to_tensor, hex_to_rgba

import folder_paths


class InsightFaceBBOXDetect:
    def __init__(self):
        self.models = {}

    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "image": ('IMAGE', {}),
                "shape": (['rectangle', 'circle', ], {'default': 'rectangle'}),
                "shape_color": ('STRING', {'default': '#FF0000'}),
                "show_num": ("BOOLEAN", {'default': False}),
            },
            "optional": {
                "num_color": ('STRING', {'default': '#FF0000'}),
                "num_pos": (['center', 'left-top', 'right-top', 'left-bottom', 'right-bottom', ], {}),
                "num_sort": (['origin', 'left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small'], {}),
                "INSIGHTFACE": ('INSIGHTFACE', {})
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT", "INSIGHTFACE",)
    RETURN_NAMES = ("bbox_image", "bbox", "face_size", "INSIGHTFACE",)

    FUNCTION = "detect"

    OUTPUT_NODE = False
    CATEGORY = "EasyApi/Detect"

    # INPUT_IS_LIST = False
    # OUTPUT_IS_LIST = (False, False)

    def detect(self, image, shape, shape_color, show_num, num_color='#FF0000', num_pos=None, num_sort=None,
               INSIGHTFACE=None):
        model = INSIGHTFACE
        import cv2
        if model is None:
            if 'insightface' not in self.models:
                from insightface.app import FaceAnalysis
                INSIGHTFACE_DIR = os.path.join(folder_paths.models_dir, "insightface")
                model = FaceAnalysis(name="buffalo_l", root=INSIGHTFACE_DIR,
                                     providers=['CUDAExecutionProvider', 'CPUExecutionProvider', ])
                model.prepare(ctx_id=0, det_size=(640, 640))
                self.models['insightface'] = model
            else:
                model = self.models['insightface']

        img = cv2.cvtColor(np.array(tensor_to_pil(image)), cv2.COLOR_RGB2BGR)
        faces = model.get(img)
        if num_sort == 'reactor' or num_sort == 'left-right':
            faces = sorted(faces, key=lambda x: x.bbox[0])
        if num_sort == "right-left":
            faces = sorted(faces, key=lambda x: x.bbox[0], reverse=True)
        if num_sort == "top-bottom":
            faces = sorted(faces, key=lambda x: x.bbox[1])
        if num_sort == "bottom-top":
            faces = sorted(faces, key=lambda x: x.bbox[1], reverse=True)
        if num_sort == "small-large":
            faces = sorted(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
        if num_sort == "large-small":
            faces = sorted(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]), reverse=True)

        r, g, b, a = hex_to_rgba(shape_color)
        n_r, n_g, n_b, n_a = hex_to_rgba(num_color)

        img_with_bbox, bbox = draw_on(img, faces, shape=shape, show_num=show_num, num_pos=num_pos, shape_color=(b, g, r), font_color=(n_b, n_g, n_r))
        img_with_bbox = Image.fromarray(cv2.cvtColor(img_with_bbox, cv2.COLOR_BGR2RGB))

        bbox_json = JSONEncoder().encode(bbox)
        return pil_to_tensor(img_with_bbox), bbox_json, len(bbox), model


def draw_on(img, faces, shape=None, show_num=False, num_pos=None, shape_color=(0, 0, 255), font_color=(0, 255, 0), font_scale=1):
    import cv2
    dimg = img.copy()
    bbox = []
    for i in range(len(faces)):
        face = faces[i]
        box = face.bbox.astype(int)
        s_x = box[0]
        s_y = box[1]
        e_x = box[2]
        e_y = box[3]
        bbox.append(box.tolist())
        if shape == 'rectangle':
            # （图片，长方形框左上角坐标, 长方形框右下角坐标， 颜色(BGR)，粗细）
            cv2.rectangle(dimg, (s_x, s_y), (e_x, e_y), shape_color, 2)
        elif shape == 'circle':
            # img：输入的图片data
            # center：圆心位置
            # radius：圆的半径
            # color：圆的颜色
            # thickness：圆形轮廓的粗细（如果为正）。负厚度表示要绘制实心圆。
            # lineType： 圆边界的类型。cv2.LINE_AA--更平滑
            # shift：中心坐标和半径值中的小数位数。
            c_x = s_x + round((e_x - s_x) / 2)
            c_y = s_y + round((e_y - s_y) / 2)
            radius = round(pow(pow(e_x - s_x, 2) + pow(e_y - s_y, 2), 0.5)/2)
            cv2.circle(dimg, (c_x, c_y), radius, shape_color, thickness=2, lineType=cv2.LINE_AA)

        # if face.kps is not None:
        #     kps = face.kps.astype(int)
        #     #print(landmark.shape)
        #     for l in range(kps.shape[0]):
        #         color = (0, 0, 255)
        #         if l == 0 or l == 3:
        #             color = (0, 255, 0)
        #         cv2.circle(dimg, (kps[l][0], kps[l][1]), 1, color, 2)
        if show_num is True:
            # 图片, 要添加的文字, 文字添加到图片上的位置, 字体的类型, 字体大小(font scale), 字体颜色, 字体粗细,
            # font_scale = 2
            thickness = 2
            # BGR
            # width和height是基于字体base line位置的长高，bottom是base line下方字体的高度，按css中文字对齐方式的思想理解
            text = '%d' % i
            (width, height), bottom = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            offset_top_y = height + 4
            offset_bottom_y = bottom + 2
            offset_x = 2
            if num_pos == 'center':
                c_x = s_x + round((e_x - s_x) / 2)
                c_y = s_y + round((e_y - s_y) / 2)
                cv2.putText(dimg, text, (c_x - round(width / 2), c_y + round((height + bottom) / 2)),
                            cv2.FONT_HERSHEY_COMPLEX, font_scale, font_color, thickness)
            elif num_pos == 'left-top':
                cv2.putText(dimg, text, (s_x + offset_x, s_y + offset_top_y), cv2.FONT_HERSHEY_COMPLEX, font_scale,
                            font_color, thickness)
                pass
            elif num_pos == 'right-top':
                cv2.putText(dimg, text, (e_x - width - offset_x, s_y + offset_top_y), cv2.FONT_HERSHEY_COMPLEX,
                            font_scale,
                            font_color, thickness)
            elif num_pos == 'left-bottom':
                cv2.putText(dimg, text, (s_x + offset_x, e_y - offset_bottom_y), cv2.FONT_HERSHEY_COMPLEX, font_scale,
                            font_color, thickness)
            elif num_pos == 'right-bottom':
                cv2.putText(dimg, text, (e_x - width - offset_x, e_y - offset_bottom_y), cv2.FONT_HERSHEY_COMPLEX,
                            font_scale, font_color, thickness)

            # cv2.putText(dimg, '%s,%d' % (face.sex, face.age), (box[0], box[1]), cv2.FONT_HERSHEY_COMPLEX, 0.7,
            #             (0, 255, 0), 1)

        # for key, value in face.items():
        #    if key.startswith('landmark_3d'):
        #        # print(key, value.shape)
        #        # print(value[0:10,:])
        #        lmk = np.round(value).astype(int)
        #        for l in range(lmk.shape[0]):
        #            color = (255, 0, 0)
        #            cv2.circle(dimg, (lmk[l][0], lmk[l][1]), 1, color, 2)
    return dimg, bbox


NODE_CLASS_MAPPINGS = {
    "InsightFaceBBOXDetect": InsightFaceBBOXDetect,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "InsightFaceBBOXDetect": "InsightFaceBBOXDetect",
}
