import pygame
import sys

# Configuración del espacio aéreo
width, height = 20, 20
cell_size = 30
grid = [[(255, 255, 255) for _ in range(width)] for _ in range(height)]  # Fondo blanco para cada celda

# Configuración de Pygame
pygame.init()
screen = pygame.display.set_mode((width * cell_size, height * cell_size))

def draw_grid():
    for y, row in enumerate(grid):
        for x, color in enumerate(row):
            pygame.draw.rect(screen, color, (x * cell_size, y * cell_size, cell_size, cell_size))

def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        draw_grid()
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
