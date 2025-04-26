"""
Example ComfyUI Custom Node
"""

import torch
import numpy as np
from PIL import Image, ImageFilter

class ExampleBlurNode:
    """Example node that applies a blur effect to an image."""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "blur_radius": ("FLOAT", {
                    "default": 2.0,
                    "min": 0.1,
                    "max": 50.0,
                    "step": 0.1
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "apply_blur"
    CATEGORY = "image/processing"

    def apply_blur(self, image, blur_radius):
        """Apply a blur effect to the input image."""
        # Convert from torch tensor to PIL Image
        i = 255. * image.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8)[0])
        
        # Apply blur
        blurred_img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        # Convert back to torch tensor
        blurred_np = np.array(blurred_img).astype(np.float32) / 255.0
        blurred_tensor = torch.from_numpy(blurred_np).unsqueeze(0)
        
        return (blurred_tensor,)

# A dictionary that contains all nodes to be registered
NODE_CLASS_MAPPINGS = {
    "ExampleBlur": ExampleBlurNode
}

# A dictionary that contains the human-readable names for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "ExampleBlur": "Example Blur Effect"
}
