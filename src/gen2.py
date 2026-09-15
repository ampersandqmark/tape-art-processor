import pygame
import os
import cv2
import numpy as np
import threading
from tkinter import Tk, filedialog
from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps

# ==========================================
# 1. Image Processing Engine (Backend)
# ==========================================
class ImageProcessor:
    @staticmethod
    def process_image_in_memory(image_path, num_layers=6, g_blur = 0.0, clip_limit=3.0, tile_grid_size=(8, 8)):
        """Processes the image and returns a preview and a list of layer images in memory."""
        # Load Image and Convert to Grayscale
        img = Image.open(image_path)
        img = img.resize((2048, 2048), Image.LANCZOS)
        img = img.convert("L")
        img = ImageOps.autocontrast(img, cutoff=2)
        if g_blur > 0.0:
            img = img.filter(ImageFilter.GaussianBlur(radius=g_blur))

        # Convert PIL Image to uint8 NumPy array
        img_array = np.array(img, dtype=np.uint8)

        # Apply CLAHE directly to the grayscale array
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        enhanced_array = clahe.apply(img_array)

        # Posterization / Quantization Math
        step_size = 256 / num_layers
        layer_indices = (enhanced_array / step_size).astype(np.uint8)

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


# ==========================================
# 2. UI Components
# ==========================================
# Colors
BG_COLOR = (30, 30, 30)
PANEL_COLOR = (45, 45, 45)
TEXT_COLOR = (220, 220, 220)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 150, 200)
SLIDER_BG = (20, 20, 20)
SLIDER_FG = (100, 200, 100)

class Button:
    def __init__(self, x, y, w, h, text, action=None, font=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action
        self.is_hovered = False
        self.font = font

    def draw(self, surface):
        color = BUTTON_HOVER if self.is_hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        text_surf = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.action:
                # print(f"[ACTION] Triggered: {self.action}")
                return self.action
        return None

class Slider:
    def __init__(self, x, y, w, h, label, min_val, max_val, start_val, v_type=None, action=None, font=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.action = action
        self.min_val = min_val
        self.max_val = max_val
        self.val = start_val
        self.v_type = v_type
        self.is_dragging = False
        self.font = font

    def draw(self, surface):
        if self.v_type == "int": 
            self.val = int(self.val)
        label_surf = self.font.render(f"{self.label}: {self.val:.1f}", True, TEXT_COLOR)
        surface.blit(label_surf, (self.rect.x, self.rect.y - 25))
        
        pygame.draw.rect(surface, SLIDER_BG, self.rect, border_radius=3)
        fill_width = int(((self.val - self.min_val) / (self.max_val - self.min_val)) * self.rect.width)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        pygame.draw.rect(surface, SLIDER_FG, fill_rect, border_radius=3)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.is_dragging == True:
            self.is_dragging = False
            # print(self.label)
            return self.action
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                rel_x = max(0, min(event.pos[0] - self.rect.x, self.rect.width))
                ratio = rel_x / self.rect.width
                self.val = self.min_val + ratio * (self.max_val - self.min_val)
        return None

# ==========================================
# 3. Main Application Manager
# ==========================================
class AppUI:
    def __init__(self):
        pygame.init()
        
        self.width, self.height = 1200, 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Tape Art Guide Generator - Prototype")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)

        # Setup UI Elements
        self.btn_import = Button(20, 30, 310, 50, "Import Image", action="import", font=self.font)
        self.slider_layer = Slider(20, 150, 310, 20, "Layer Count", 3, 12, 6, v_type = "int", action="change_val", font=self.font)
        self.slider_blur = Slider(20, 250, 310, 20, "Gaussian Blur", 0, 15, 0, action="change_val", font=self.font)
        self.slider_clip = Slider(20, 350, 310, 20, "CLAHE ClipLimit", 1.0, 10.0, 3.0, action="change_val", font=self.font)
        self.slider_grid = Slider(20, 450, 310, 20, "CLAHE GridSize", 2, 32, 8, v_type ="int", action="change_val", font=self.font)
        self.btn_save = Button(20, 720, 310, 50, "Save Layers", action="save", font=self.font)

        self.ui_elements = [
            self.slider_layer,
            self.btn_import, 
            self.slider_blur, 
            self.slider_clip, 
            self.slider_grid, 
            self.btn_save
        ]

        # Viewport setup
        self.preview_rect = pygame.Rect(370, 20, 810, 760)
        self.preview_surface = None
        
        # Application State
        self.image_path = None
        self.preview_pil = None
        self.layers = []  # Stores PIL images of processed layers in-memory
        
        # Threading State
        self.is_dialog_open = False
        self._pending_image_data = None

    def pre_process_image(self, image_path):
        if image_path is None:
            return None

        # Fetch parameters from sliders (simulating dynamic use for future scalability)
        num_layers = int(self.slider_layer.val)
        g_blur = float(self.slider_blur.val)
        clip_limit = float(self.slider_clip.val)
        grid_size = int(self.slider_grid.val)
        grid_tuple = (grid_size, grid_size)

        # Process image in-memory
        preview_pil, layers = ImageProcessor.process_image_in_memory(
            image_path, num_layers=num_layers, g_blur=g_blur, clip_limit=clip_limit, tile_grid_size=grid_tuple
        )
        # print("Image successfully processed.")

        return (preview_pil, layers, image_path)

    def _open_file_dialog_thread(self):
        """Runs the blocking Tkinter dialog and image processing in the background."""
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        image_path = filedialog.askopenfilename(
            parent=root,
            title="Select an image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"), ("All Files", "*.*")]
        )
        root.destroy()
        
        if image_path:
            try:
                # print(f"Loading and processing: {image_path}")  
                # Store tuple for the main thread to convert into Pygame Surface safely
                self._pending_image_data = self.pre_process_image(image_path)

            except Exception as e:
                print(f"Error processing image: {e}")
                
        self.is_dialog_open = False

    def import_image(self):
        """Spawns background thread instead of blocking the main thread."""
        if self.is_dialog_open:
            return  # Prevent multiple dialog instances
        
        self.is_dialog_open = True

        threading.Thread(target=self._open_file_dialog_thread, daemon=True).start()

    def save_layers(self):
        if not self.layers:
            # print("No image processed yet. Please import an image first.")
            return

        self.preview_pil.save(f"posterize preview.png")
        print(f"Saved posterized preview")
        for i, layer_img in enumerate(self.layers):
            layer_filename = f"layer_{i+1}.png"
            layer_img.save(layer_filename)
            print(f"Saved {layer_filename} (Layer {i+1} of {len(self.layers)})")
        print("\nAll layers saved successfully!")

    def handle_events(self):
        # 1. Check if background thread finished work to finalize Pygame Surface creation
        if self._pending_image_data:
            self.preview_pil, self.layers, self.image_path = self._pending_image_data
            
            raw_surface = pygame.image.fromstring(
                self.preview_pil.tobytes(), self.preview_pil.size, self.preview_pil.mode
            )
            
            self.preview_surface = pygame.transform.smoothscale(
                raw_surface, (self.preview_rect.width, self.preview_rect.height)
            )
            
            # print("Image successfully loaded into viewport.")
            self._pending_image_data = None
            pygame.event.clear() # Dump queue to wipe ghost clicks occurring during load

        # 2. Main Pygame Event Loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Disable UI component interactions whilst the dialog thread runs
            if self.is_dialog_open:
                continue
            
            for element in self.ui_elements:
                action = element.handle_event(event)
                if action == "import":
                    self.import_image()
                elif action == "save":
                    self.save_layers()
                elif action == "change_val":
                    self._pending_image_data = self.pre_process_image(self.image_path)
        return True

    def render(self):
        self.screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()

        # Update hover states (only if dialog isn't blocking UI)
        if not self.is_dialog_open:
            for element in self.ui_elements:
                if isinstance(element, Button):
                    element.check_hover(mouse_pos)

        # Draw Control Panel Side
        pygame.draw.rect(self.screen, PANEL_COLOR, (0, 0, 350, self.height))
        for element in self.ui_elements:
            element.draw(self.screen)

        # Draw Viewport Side
        pygame.draw.rect(self.screen, (20, 20, 20), self.preview_rect)
        
        if self.is_dialog_open:
            wait_text = self.font.render("Waiting for file selection or processing...", True, (150, 150, 250))
            self.screen.blit(wait_text, (self.preview_rect.centerx - 200, self.preview_rect.centery))
        elif self.preview_surface:
            self.screen.blit(self.preview_surface, self.preview_rect.topleft)
        else:
            empty_text = self.font.render("No Preview Available (Import an image)", True, (150, 150, 150))
            self.screen.blit(empty_text, (self.preview_rect.centerx - 180, self.preview_rect.centery))

        pygame.display.flip()
        self.clock.tick(60)

# ==========================================
# 4. Main Execution
# ==========================================
def main():
    app = AppUI()
    running = True

    while running:
        running = app.handle_events()
        if running:
            app.render()

    pygame.quit()

if __name__ == "__main__":
    main()