import pygame
from ui import AppUI

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