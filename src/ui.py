import os
import pygame
import threading
from tkinter import Tk, filedialog
from processor import ImageProcessor

BG_COLOR = (30, 30, 30)
PANEL_COLOR = (45, 45, 45)
TEXT_COLOR = (220, 220, 220)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 150, 200)
SAVE_COLOR = (80, 170, 90)
SAVE_HOVER = (100, 200, 110)
SLIDER_BG = (20, 20, 20)
SLIDER_FG = (70, 130, 180)
SLIDER_GRAY = (130, 140, 180)

class Button:
    def __init__(
                self, 
                x, y, w, h, 
                text, 
                action=None, 
                font=None
            ):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action
        self.is_hovered = False
        self.font = font

    def draw(self, surface):
        if self.action=="save":
            color = SAVE_HOVER if self.is_hovered else SAVE_COLOR
        else:
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

class Checkbox:
    def __init__(
                self, 
                x, y, w, h, 
                text, 
                checked=False, 
                action=None, 
                font=None
            ):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action
        self.is_hovered = False
        self.font = font
        self.checked = True
        self.val = "CLAHE"

    def draw(self, surface):
        inflate = 5 if self.is_hovered else 2
        
        # Draw the outer checkbox square
        pygame.draw.rect(surface, TEXT_COLOR, self.rect, border_radius=3)
        pygame.draw.rect(surface, BUTTON_COLOR, self.rect, inflate, border_radius=3) # Border outline

        # If checked, draw a smaller inner box or a checkmark indicator inside
        if self.checked:
            inner_rect = self.rect.inflate(-8, -8)
            pygame.draw.rect(surface, BUTTON_COLOR, inner_rect, border_radius=2)

        # Draw the label text next to the checkbox
        if self.font and self.text:
            text_surf = self.font.render(self.text, True, TEXT_COLOR)
            # Position text to the right of the checkbox box with some spacing
            text_rect = text_surf.get_rect(midleft=(self.rect.right + 10, self.rect.centery))
            surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                # print("Ticked")
                self.checked = not self.checked
                self.val = "CLAHE" if self.checked else None
                return self.action
        return None

class Slider:
    def __init__(
                self, 
                x, y, w, h, 
                label, 
                min_val, 
                max_val, 
                start_val, 
                v_type=None, 
                action=None, 
                font=None
            ):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.action = action
        self.min_val = min_val
        self.max_val = max_val
        self.val = start_val
        self.v_type = v_type
        self.is_dragging = False
        self.font = font
        self.is_active = True

    def draw(self, surface):
        label_surf = self.font.render(f"{self.label}: {self.val:.1f}", True, TEXT_COLOR)
        surface.blit(label_surf, (self.rect.x, self.rect.y - 25))

        fill_color = SLIDER_FG if self.is_active else SLIDER_GRAY
        
        pygame.draw.rect(surface, SLIDER_BG, self.rect, border_radius=3)
        fill_width = int(((self.val - self.min_val) / (self.max_val - self.min_val)) * self.rect.width)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        pygame.draw.rect(surface, fill_color, fill_rect, border_radius=3)

    def handle_event(self, event):
        if not self.is_active:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.is_dragging == True:
            self.is_dragging = False
            # print(self.label, self.val)
            return self.action
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                rel_x = max(0, min(event.pos[0] - self.rect.x, self.rect.width))
                ratio = rel_x / self.rect.width
                self.val = self.min_val + ratio * (self.max_val - self.min_val)
                if self.v_type == "int": # snap values if int input
                    self.val = int(self.val)
        return None

class AppUI:
    def __init__(self):
        pygame.init()
        
        self.width, self.height = 1200, 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Tape Art Processor v.1.0")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)

        # Setup UI Elements
        # ======== Buttons ========
        # x, y, w, h, label, action, font
        self.btn_import = Button(
            20, 30, 310, 50, 
            "Import Image", 
            action="import", 
            font=self.font
        )
        self.btn_save = Button(
            20, 720, 310, 50, 
            "Save Layers", 
            action="save", 
            font=self.font
        )

        # ======== Checkboxes ========
        # x, y, w, h, label, start_state, action, font
        self.tick_process = Checkbox(
            20, 450, 30, 30, 
            "CLAHE Processing", 
            checked=True
            action="change_val", 
            font=self.font, 
        )

        # ======== Sliders ========
        # x, y, w, h, label, min, max, start, action, font
        self.slider_blur = Slider(
            20, 350, 310, 20, 
            "Gaussian Blur", 
            0, 32, 0, 
            action="change_val", 
            font=self.font
        )
        self.slider_clip = Slider(
            20, 520, 310, 20, 
            "CLAHE ClipLimit", 
            1.0, 10.0, 3.0, 
            action="change_val", 
            font=self.font
        )
        self.slider_contrast = Slider(
            20, 250, 310, 20, 
            "Contrast", 
            0, 50, 0, 
            action="change_val", 
            font=self.font
        )
        self.slider_grid = Slider(
            20, 600, 310, 20, 
            "CLAHE GridSize", 
            2, 32, 8, 
            v_type ="int", 
            action="change_val", 
            font=self.font
        )
        self.slider_layer = Slider(
            20, 150, 310, 20, 
            "Layer Count", 
            3, 12, 6, 
            v_type = "int", 
            action="change_val", 
            font=self.font
        )

        self.ui_elements = [
            self.btn_import,
            self.slider_layer,
            self.slider_contrast, 
            self.slider_blur, 
            self.tick_process,
            self.slider_clip, 
            self.slider_grid, 
            self.btn_save
        ]

        self.process = str(self.tick_process.val)

        # Viewport setup
        self.preview_rect = pygame.Rect(370, 20, 810, 760)
        self.preview_surface = None
        
        # Application State
        self.image_path = None
        self.preview_pil = None # store processed image
        self.layers = []  # Stores PIL images of processed layers in-memory
        
        # Threading State
        self.is_dialog_open = False
        self._pending_image_data = None

    def pre_process_image(self, image_path):
        """Get the necessary arguments and pass to the main processor. returns processed image data"""
        if image_path is None:
            return None

        # Fetch parameters from sliders
        num_layers = int(self.slider_layer.val)
        contrast = float(self.slider_contrast.val)
        g_blur = float(self.slider_blur.val)

        if self.process == "CLAHE":    
            clip_limit = float(self.slider_clip.val)
            grid_size = int(self.slider_grid.val)
            grid_tuple = (grid_size, grid_size)
        
            # Process image
            preview_pil, layers = ImageProcessor.process_image(
                image_path, 
                num_layers=num_layers, 
                contrast=contrast, 
                g_blur=g_blur, 
                process=self.process,
                clip_limit=clip_limit, 
                tile_grid_size=grid_tuple
            )
        else:
            preview_pil, layers = ImageProcessor.process_image(
                image_path, 
                num_layers=num_layers, 
                contrast=contrast, 
                g_blur=g_blur, 
                process=self.process
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
            print("No image processed yet. Please import an image first.")
            return

        self.preview_pil.save(f"posterize preview.png")
        print(f"Saved posterized preview")
        for i, layer_img in enumerate(self.layers):
            layer_filename = f"layer_{i+1}.png"
            layer_img.save(layer_filename)
            print(f"Saved {layer_filename} (Layer {i+1} of {len(self.layers)})")
        print("\nAll layers saved successfully!")

    def handle_events(self):
        # 1. Check if theres new image data
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

        if self.process != "CLAHE":
            self.slider_grid.is_active = False
            self.slider_clip.is_active = False
        else:
            self.slider_grid.is_active = True
            self.slider_clip.is_active = True

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
                    self.process = self.tick_process.val # check if the val change is process
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
                if isinstance(element, Checkbox):
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