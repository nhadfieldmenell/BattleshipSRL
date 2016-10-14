"""Library containing board class and functions that manipulate it.
"""
import random
import sys

from collections import defaultdict

class board(object):
    """A Battleship game board instance.

    Args:
        dim: The side length of the board.
        boats_sizes: An array containing the size for each boat in
            the game. For example [3, 3, 4, 5] places 2 boats of 
            length 3, 1 boat of length 4, and 1 boat of length 5 on 
            the board.
    """
    def __init__(self, dim, boat_sizes):
        self.dim = dim

        """Empty spots are marked with a period, occupied and unguessed
        are marked with a O, occupied and guessed is marked with an X.
        """
        self.board = [['.' for i in range(dim)] for i in range(dim)]
        self.boat_index2positions = defaultdict(list)
        self.boat_index2size = {}
        self.position2boat_index = {}
        self.position2hit = set()
        self.place_boats_randomly(boat_sizes)
        

    def shoot(self, position):
        """Perform 1 move of the game.

        Shoot at a board position. Update the board accordingly.

        Args:
            position: A tuple (row, column) to shoot at.

        Returns:
            A tuple (x, y):
                x: True if hit, False otherwise.
                y: 0 if the shot did not sink a ship. The size of the
                    ship if the shot did sink a ship.
        """
        if position not in self.position2boat_index:
            if position in self.position2hit:
                return True, 0
            return False, 0
        self.position2hit.add(position)
        self.board[position[0]][position[1]] = 'X'
        boat_index = self.position2boat_index[position]
        self.boat_index2positions[boat_index].pop(
                self.boat_index2positions[boat_index].index(position))
        self.position2boat_index.pop(position)
        if not self.boat_index2positions[boat_index]:
            return True, self.boat_index2size[boat_index]
        return True, 0


    def place_boat(self, size, horizontal, row, col, boat_index):
        """Place a boat on the board.

        Args:
            size: The size of the boat.
            horizontal: A bool. If true, place boat horizontally with 
                the lefrmost coordinate at (row, col). If false, place
                boat vertically with topmost coordinate at (row, col).
            row: Row index.
            col: Column index.
            boat_index: The index of the boat.
        """
        if horizontal:
            for j in range(col, col + size):
                self.board[row][j] = 'O'
                position = (row, j)
                self.boat_index2positions[boat_index].append(position)
                self.position2boat_index[position] = boat_index

        else:
            for i in range(row, row + size):
                self.board[i][col] = 'O'
                position = (i, col)
                self.boat_index2positions[boat_index].append(position)
                self.position2boat_index[position] = boat_index


    def place_boats_randomly(self, sizes):
        """Place all the boats randomly on the board.

        Args:
            sizes: A list containing the sizes of all the boats to
                place on the board.
        """
        for boat_index in range(len(sizes)):
            size = sizes[boat_index]
            valid_positions = self.valid_positions(size)
            row, col, horizontal = valid_positions[
                    random.randrange(len(valid_positions))] 
            self.place_boat(size, horizontal, row, col, boat_index)
            self.boat_index2size[boat_index] = size


    def valid_positions(self, size):
        """Determine the valid positions for placing a boat.

        Args:
            size: The size of the boat.

        Returns:
            A list of 3-tuples representing valid boat placement positions.
            The first element is the row, the second element is the column,
            and the third element is either True for a horizontal placement
            or False for a vertical placement.
        """
        valid_positions = []
        for i in range(self.dim):
            for j in range(self.dim - size + 1):
                valid = True
                for col in range(j, j + size):
                    if self.board[i][col] != '.':
                        valid = False
                        break
                if valid:
                    valid_positions.append((i, j, True))
        for i in range(self.dim - size + 1):
            for j in range(self.dim):
                valid = True
                for row in range(i, i + size):
                    if self.board[row][j] != '.':
                        valid = False
                        break
                if valid:
                    valid_positions.append((i, j, False))
        return valid_positions


    def valid_start_positions(self, size):
        """Determine the valid starting locations for a boat.

        Args:
            size: The size of the boat.

        Returns:
            A dict that maps 'Horizontal' to the valid board positions
            for placing a horizontal boat and 'Vertical' to the valid
            board positions for placing a vertical boat.
        """
        valid_positions = []
        for i in range(self.dim):
            for j in range(self.dim - size + 1):
                valid_positions.append((i, j, 'Horizontal'))
        for i in range(self.dim - size + 1):
            for j in range(self.dim):
                valid_positions.append((i, j, 'Vertical'))
        return orientation2positions

    def print_board(self):
        sys.stdout.write('   ')
        for i in range(self.dim):
            sys.stdout.write('%s ' % i)
            if i < 10:
                sys.stdout.write(' ')
        print '\n'
        for i in range(self.dim):
            sys.stdout.write('%s ' % i)
            if i < 10:
                sys.stdout.write(' ')
            for j in range(self.dim):
                sys.stdout.write('%s  ' % self.board[i][j])
            print '\n'

def main():
    if len(sys.argv) != 3:
        print "usage: %s [BOARD DIM] [BOAT SIZES]" % sys.argv[0]
        exit(1)
    dim, sizes = (int(sys.argv[1]), map(int, sys.argv[2].split(',')))
    b = board(dim, sizes)
    shots = [(0, 1), (3, 2), (2, 2), (4, 1), (3, 4), (3, 3), (3, 2), (3, 1), (3, 0),
            (2, 0), (2, 1), (2, 2)]
    for shot in shots:
        print shot
        print b.shoot(shot)
        b.print_board()


if __name__ == '__main__':
    main()
