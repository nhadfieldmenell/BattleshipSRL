import sys
import operator
import time
import numpy as np
from problog import get_evaluatable
from problog.program import PrologString
import board as b
import generateProblogGame as gpg


class game(object):
    """A game instance.

    Args:
        board_size: An int for the edge length of the board.
        boats: A list of ints corresponding to the boat sizes for the game.
    """
    def __init__(self, board_size, boats):
        self.board_size = board_size
        self.boats = boats
        self.board = b.board(board_size, boats)
        self.knowledge = gpg.generate_problog_string(board_size, boats)
        self.unshot_positions = set((i, j) for i in range(1, board_size+1) for j in range(1, board_size+1))
        self.hits = set()
        self.misses = set()
        self.num_sinks = 0

    def print_game(self):
        sys.stdout.write('   ')
        for i in range(self.board_size):
            sys.stdout.write('%d ' % (i+1))
            if i < 10:
                sys.stdout.write(' ')
        print '\n'
        for i in range(self.board_size):
            sys.stdout.write('%d ' % (i+1))
            if i < 10:
                sys.stdout.write(' ')
            for j in range(self.board_size):
                if (i+1, j+1) in self.hits:
                    sys.stdout.write('X')
                elif (i+1, j+1) in self.misses:
                    sys.stdout.write('O')
                else:
                    sys.stdout.write('.')
                sys.stdout.write('  ')
            print '\n'


    def play_full_game(self):
        moves = 0
        cur_time = time.time()
        while len(self.hits) < sum(self.boats):
            self.move()
            self.print_game()
            moves += 1
            print "Made move in %.2fs" % (time.time()-cur_time)
            cur_time = time.time()
        print "Won the game in %d moves" % moves


    def boat_in(self, pos):
        """Update game when we know there is a boat in a specific position.

        Args:
            pos: A tuple of ints corresponding to the position that there is a boat in.
        """
        self.unshot_positions.remove(pos)
        self.hits.add(pos)
        self.knowledge += '\nevidence(boat_in%s).\n' % str(pos)


    def boat_not_in(self, pos):
        """Update game when we know there is no boat in a specific position.

        Args:
            pos: A tuple of ints corresponding to the position that there is no boat in.
        """
        self.unshot_positions.remove(pos)
        self.misses.add(pos)
        self.knowledge += '\nevidence(not(boat_in%s)).\n' % str(pos)


    def potential_sinks(self, pos, size):
        """Determine the potential places a boat could have been when you sink it.

        Update game knowledge to reflect these possibilities.

        Args:
            pos: The position of the hit that caused a sink.
            size: The size of the boat that was sunk.
        """
        up_potentials = np.arange(size)
        row = pos[0]
        col = pos[1]
        lower = 0
        upper = size
        for i in range(row + 1, row + size):
            if i > self.board_size or (i, col) not in self.hits:
                lower = size - i + row
                break
        for i in range(row - 1, row - size, -1):
            if i < 1 or (i, col) not in self.hits:
                upper = row - i
                break
        up_potentials = up_potentials[lower:upper]
        lower = 0
        upper = size
        left_potentials = np.arange(size)
        for j in range(col + 1, col + size):
            if j > self.board_size or (row, j) not in self.hits:
                lower = size - j + col
                break
        for j in range(col - 1, col - size, -1):
            if j < 1 or (row, j) not in self.hits:
                upper = col - j
                break
        left_potentials = left_potentials[lower:upper]
        rule = 'sunk_%d' % self.num_sinks
        self.num_sinks += 1
        print "UP POTENTIALS"
        print up_potentials
        print "left POTENTIALS"
        print left_potentials

        for i in up_potentials:
            self.knowledge += '\n%s :- boat(B), vertical(B), size(B, %d), loc(B, %d, %d).\n' % (rule, size, (row-i), col)
        for j in left_potentials:
            self.knowledge += '\n%s :- boat(B), horizontal(B), size(B, %d), loc(B, %d, %d).\n' % (rule, size, row, (col-j))
        self.knowledge += '\nevidence(%s).\n' % rule



    def move(self):
        """Determine the optimal move and make it.

        Determine the unguessed position with the highest probability of holding a boat.
        Shoot in that position and update knowledge accordingly.

        Returns:
            A tuple (x, y):
                x: True if hit, False otherwise.
                y: 0 if the shot did not sink a ship. The size of the
                    ship if the shot did sink a ship.
        """
        query = self.knowledge[:]
        query += '\n' + '\n'.join(map(lambda x: 'query(boat_in%s).' % str(x), self.unshot_positions))
        result = get_evaluatable().create_from(PrologString(query)).evaluate()

        best_position = extract_position(str(max(result.iteritems(), key=operator.itemgetter(1))[0]))
        print "Shooting at: %s" % str(best_position)

        for pos in result:
            if not(result[pos]):
                position = extract_position(str(pos))
                self.boat_not_in(position)
                print "Inferred no boat in %s" % str(position)

        hit, sunk = self.board.shoot((best_position[0]-1, best_position[1]-1))

        #ADD LOGIC IN THE PRESENCE OF A SINK
        if hit:
            self.boat_in(best_position)
            if sunk:
                self.potential_sinks(best_position, sunk)
                print "SUNK A BOAT WITH SIZE %d" % sunk
                print self.knowledge
            return True, sunk

        else:
            self.boat_not_in(best_position)
            return False, sunk




def extract_position(s):
    """Extract the coordinates from a string of the form 'boat_in(x,y)'.

    Args:
        s: A string of the form 'boat_in(x,y)'

    Returns:
        A tuple of ints - (x, y)
    """
    return tuple(map(int, s[8:-1].split(',')))


def play_game(board_size, boats):
    """Set up a board and automate a game.

    Args:
        board_size: An int for the edge length of the board.
        boats: A list of ints corresponding to the boat sizes for the game.
    """
    board = b.board(board_size, boats)
    knowledge = gpg.generate_problog_string(board_size, boats)
    print board.boat_index2positions


def practice_query(board_size, boats):
    script_name = "game_%d" % board_size
    for size in boats:
        script_name = "%s_%d" % (script_name, size)
    script_name = "%s.txt" % script_name

    with(open(script_name, 'r')) as infile:
        game_state =  ''.join(infile.readlines())

    game_state += '\n\n' + '\n'.join(['query(boat_in(%d, %d)).' % (i, j) for i in range(1, board_size+1) for j in range(1, board_size+1)])

    result = get_evaluatable().create_from(PrologString(game_state)).evaluate()
    print game_state, '\n\n'
    print result
    print result.keys()[0]

def main():
    if len(sys.argv) < 3:
        print "USAGE: [BOARD_SIZE] [BOAT_SIZE1] [BOAT_SIZE2] ..."
        exit(1)

    board_size = int(sys.argv[1])
    boats = map(int, sys.argv[2:])

    g = game(board_size, boats)

    g.board.print_board()

    g.play_full_game()
    #g.move()



if __name__ == '__main__':
    main()
