import pygame
import sys


def main():
    pygame.init()
    disp = pygame.display.set_mode((400,300))
    pygame.display.set_caption("Hello World!")
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.update()

if __name__ == "__main__":
    main()
