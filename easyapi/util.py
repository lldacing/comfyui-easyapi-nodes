import numpy as np
import torch
from PIL import Image

# Tensor to PIL
def tensor_to_pil(image):
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))


# Convert PIL to Tensor
def pil_2_tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

