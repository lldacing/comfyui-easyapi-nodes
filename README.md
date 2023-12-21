# comfyui-easyapi-nodes
针对api接口开发补充的一些自定义节点和功能

## 节点
| 名称  | 说明                                                                                                                                                         |
|-----|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Base64ToImage | 把图片base64字符串转成图片                                                                                                                                           |
| ImageToBase64 | 把图片转成base64字符串                                                                                                                                             |
| LoadImageToBase64 | 加载本地图片转成base64字符串                                                                                                                                          |
| SamAutoMaskSEGS | 得到图片所有语义分割的coco或uncompress_rle格式。<br/>配合ComfyUI-Impact-Pack的SAMLoader或comfyui_segment_anything的SAMModelLoader。<br/>但是如果使用hq模型，必须使用comfyui_segment_anything |

## 功能
- 扩展Save(Api Format)菜单。

   支持保存api格式workflow时，把LoadImage替换成Base64ToImage节点，把PreviewImage和SaveImage替换成ImageToBase64节点

  ![save api extended](docs/menu.gif)