import pygame
import sys
import os
from automate_game import game
import board
import time


def main():
    #set up graphics
    pygame.init()
    h_size = 301
    v_size = 301
    disp = pygame.display.set_mode((h_size, v_size))
    pygame.display.set_caption("Battleship Game")

    water = pygame.image.load(os.path.join(os.getcwd(), "sprites/Water.bmp"))
    hit = pygame.image.load(os.path.join(os.getcwd(), "sprites/Hit.bmp"))
    miss = pygame.image.load(os.path.join(os.getcwd(), "sprites/Miss.bmp"))

    #play game

    move_type = "HT"
    board_size = 6
    boats = [3, 2, 3]

    g = game(move_type, board_size, boats)
    g.board.print_board()
    moves = g.play_full_game()
    moves = [[set(), set()]] + moves

    space_needed = board_size*21 + (board_size-1)*5
    h_start = (h_size - space_needed) / 2
    v_start = (v_size - space_needed) / 2

    move_index = 0
    while True:
        time.sleep(2)
        board_state = moves[move_index]
        hits = board_state[0]
        misses = board_state[1]
        for i in range(1, board_size+1):
            for j in range(1, board_size+1):
                '''credit to "HardVacuum for original sprite:
                http://www.lostgarden.com/2005/03/game-post-mortem-hard-vacuum.html'''
                if (i, j) in hits:
                    disp.blit(hit, (h_start + 25*(i-1), v_start + 25*(j-1)))
                elif (i, j) in misses:
                    disp.blit(miss, (h_start + 25*(i-1), v_start + 25*(j-1)))
                else:
                    disp.blit(water, (h_start + 25*(i-1), v_start + 25*(j-1)))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.update()
        if move_index < len(moves) - 1:
            move_index += 1

if __name__ == "__main__":
    main()
