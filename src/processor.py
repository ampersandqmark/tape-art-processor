import cv2
import numpy as np
from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps

class ImageProcessor:
    @staticmethod
    def process_CLAHE():
        pass

    def process_image(
                image_path, 
                num_layers=6, 
                contrast=0.0, 
                g_blur = 0.0, 
                process="CLAHE", 
                clip_limit=3.0, 
                tile_grid_size=(8, 8)
            ):
        """Processes the image and returns a preview and a list of layer images in memory."""
        # Load Image and Convert to Grayscale
        img = Image.open(image_path)
        img = img.resize((2048, 2048), Image.LANCZOS)
        img = img.convert("L")
        
        # contrast and gaussian blur
        if contrast > 0.0:
            img = ImageOps.autocontrast(img, cutoff=contrast)
        if g_blur > 0.0:
            img = img.filter(ImageFilter.GaussianBlur(radius=g_blur))

        # Convert PIL Image to uint8 NumPy array
        img_array = np.array(img, dtype=np.uint8)

        # Apply CLAHE to the grayscale array
        if process == "CLAHE":
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            img_array = clahe.apply(img_array)

        # Posterization / Quantization Math
        step_size = 256 / num_layers
        layer_indices = (img_array / step_size).astype(np.uint8)

        # Reconstruct posterized array for visualization
        posterized_array = (layer_indices * (255 / (num_layers - 1))).astype(np.uint8)
        
        # We convert to RGB here so Pygame can easily digest it later
        posterized_img = Image.fromarray(posterized_array).convert("RGB")

        # Generate Cumulative Layer Stencils
        layers = []
        for i in range(1, num_layers + 1):
            threshold_index = num_layers - i
            mask = layer_indices <= threshold_index

            stencil = np.full_like(img_array, fill_value=255, dtype=np.uint8)
            stencil[mask] = 0  # Black represents cut-out tape area
            layers.append(Image.fromarray(stencil))

        return posterized_img, layers