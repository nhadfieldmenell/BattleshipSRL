import sys
import operator
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
                if (i, j) in self.hits:
                    sys.stdout.write('X')
                elif (i, j) in self.misses:
                    sys.stdout.write('O')
                else:
                    sys.stdout.write('.')
                sys.stdout.write('  ')
            print '\n'


    def play_full_game(self):
        moves = 0
        while len(self.hits) < self.boats:
            self.move()
            self.print_game()
            moves += 1
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

        #THIS MIGHT BE A LITTLE SKETCHY BUT I THINK NOT
        #IF A POSITION EVER HAS 0 PROBABILITY IT SHOULD NEVER HAVE POSITIVE PROBABILITY IN THE FUTURE
        #STILL MIGHT BE A BIT UNNECESSARY
        for pos in result:
            if not(result[pos]):
                position = extract_position(str(pos))
                self.boat_not_in(position)
                print "no boat in %s" % str(position)

        hit, sunk = self.board.shoot(best_position)

        #ADD LOGIC IN THE PRESENCE OF A SINK
        if hit:
            self.boat_in(best_position)
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
