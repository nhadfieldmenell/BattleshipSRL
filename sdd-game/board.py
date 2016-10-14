"""Library containing board class and functions that manipulate it.
"""
import sys

class board(object):
    """A Battleship game board instance.

    Args:
        dim: The side length of the board.
        boats: An array containing the size for each boat in the game.
            For example [3, 3, 4, 5] will place 2 boats of length 3,
            1 boat of length 4, and 1 boat of length 5 on the board.
    """
    def __init__(self, dim, boats):
        self.dim = dim
        self.board = [[0] * dim] * dim

    def print_board(self):
        sys.stdout.write('   ')
        for i in range(self.dim):
            sys.stdout.write('%d ' % i)
            if i < 10:
                sys.stdout.write(' ')
        print '\n'
        for i in range(self.dim):
            sys.stdout.write('%d ' % i)
            if i < 10:
                sys.stdout.write(' ')
            for j in range(self.dim):
                sys.stdout.write('%d  ' % self.board[i][j])
            print '\n'

def main():
    if len(sys.argv) != 2:
        print "usage: %s [BOARD DIM]" % sys.argv[0]
        exit(1)
    dim = int(sys.argv[1])
    b = board(dim, [])
    b.print_board()


if __name__ == '__main__':
    main()
