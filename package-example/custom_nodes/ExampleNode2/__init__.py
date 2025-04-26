"""
Example Text Overlay Node for ComfyUI
"""

import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

class ExampleTextOverlayNode:
    """Example node that adds text overlay to an image."""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "text": ("STRING", {"default": "ComfyUI"}),
                "font_size": ("INT", {
                    "default": 36, 
                    "min": 8, 
                    "max": 128
                }),
                "position_x": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01
                }),
                "position_y": ("FLOAT", {
                    "default": 0.9,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01
                }),
                "color": (["white", "black", "red", "green", "blue", "yellow"], {"default": "white"}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "add_text"
    CATEGORY = "image/text"

    def add_text(self, image, text, font_size, position_x, position_y, color):
        """Add text overlay to the input image."""
        # Convert from torch tensor to PIL Image
        i = 255. * image.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8)[0])
        
        # Create a drawing context
        draw = ImageDraw.Draw(img)
        
        # Try to get a font, or use default
        try:
            font_path = os.path.join(os.path.dirname(__file__), "arial.ttf")
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
            else:
                # Use default font
                font = ImageFont.load_default()
                font_size = 16  # Reset to a safe size for default font
        except Exception:
            # Fallback to default
            font = ImageFont.load_default()
            font_size = 16  # Reset to a safe size for default font
        
        # Calculate position
        width, height = img.size
        x = int(width * position_x)
        y = int(height * position_y)
        
        # Add text with an outline for visibility
        if color != "black":
            # Black outline
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                draw.text((x + dx, y + dy), text, font=font, fill="black")
        else:
            # White outline for black text
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                draw.text((x + dx, y + dy), text, font=font, fill="white")
        
        # Draw the main text
        draw.text((x, y), text, font=font, fill=color)
        
        # Convert back to torch tensor
        result_np = np.array(img).astype(np.float32) / 255.0
        result_tensor = torch.from_numpy(result_np).unsqueeze(0)
        
        return (result_tensor,)

# A dictionary that contains all nodes to be registered
NODE_CLASS_MAPPINGS = {
    "ExampleTextOverlay": ExampleTextOverlayNode
}

# A dictionary that contains the human-readable names for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "ExampleTextOverlay": "Example Text Overlay"
}
