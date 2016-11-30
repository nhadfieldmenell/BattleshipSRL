import sys
import operator
import time
import multiprocessing as mp
import pickle
import pdb
#bypass numpy import error on deduction
try:
    import numpypy
except ImportError:
    pass
import numpy as np
from problog import get_evaluatable
from problog.program import PrologString
import board as b
import random
import generateProblogGame as gpg


class game(object):
    """A game instance.

    Args:
        move_type: A string indicating the move algorithm to be used.
        board_size: An int for the edge length of the board.
        boats: A list of ints corresponding to the boat sizes for the game.
    """
    def __init__(self, move_type, board_size, boats):
        self.move_type = move_type
        self.board_size = board_size
        self.boats = boats[:]
        self.board = b.board(board_size, boats)
        self.knowledge = gpg.generate_problog_string(board_size, boats)
        self.unshot_positions = set((i, j) for i in range(1, board_size+1) for j in range(1, board_size+1))
        self.hits = set()
        self.misses = set()
        self.current_hits = set()
        self.num_sinks = 0
        self.num_no_sink = 0
        self.targets = []
        self.last_hit_position = (0, 0) #dummy initialization value
        self.in_hunt_mode = True #for pdf mode
        self.sunk_ambiguous_boats = []
        self.total_moves = 0
        self.board_states = []

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

    def play_full_game(self, write_data=False, run_number=0):
        start_time = time.time()
        cur_time = time.time()
        while self.boats:
            self.move()
            self.print_game()
            self.total_moves += 1
            print "Made move in %.2fs" % (time.time()-cur_time)
            cur_time = time.time()
            self.board_states.append([self.hits.copy(), self.misses.copy()])
        print "Won the game in %d moves" % self.total_moves
        overall_time = time.time() - start_time
        if write_data:
            with open("run" + str(run_number) + ".data", "wb") as data_file:
                data_file.write('\n'.join(["Number of moves: %s" % str(self.total_moves), "Time taken: %f seconds" %
                                           overall_time]))
        return self.board_states

    def adjacent_positions(self, pos):
        """Determines spaces in all four cardinal directions, regardless of validity of resulting positions.

        Args:
            pos: A tuple of ints corresponding to the position that is to be analyzed.
        """
        north_pos = (pos[0]-1, pos[1])
        east_pos = (pos[0], pos[1]+1)
        south_pos = (pos[0]+1, pos[1])
        west_pos = (pos[0], pos[1]-1)

        possible_targets = [north_pos, south_pos, east_pos, west_pos]
        return possible_targets

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

        new_knowledge = []
        for i in up_potentials:
            new_knowledge.append('\n%s :- boat(B), vertical(B), size(B, %d), loc(B, %d, %d).\n' % (rule, size, (row-i), col))
        for j in left_potentials:
            new_knowledge.append('\n%s :- boat(B), horizontal(B), size(B, %d), loc(B, %d, %d).\n' % (rule, size, row, (col-j)))
        new_knowledge.append('\nevidence(%s).\n' % rule)
        self.knowledge += ''.join(new_knowledge)
        print ''.join(new_knowledge)


    def hit_no_sink(self, pos):
        """Add knowledge when we have a hit but there is no sink.

        Args:
            pos: The position that we just hit.
        """
        #THIS SHIT AINT WORKIN YO!
        row = pos[0]
        col = pos[1]
        #pdb.set_trace()
        for size in set(self.boats):
            for loc in range(row, row - size, -1):
                if loc < 1:
                    break
                impossible_position = True
                for i in range(loc, loc + size):
                    if (i, col) not in self.hits:
                        impossible_position = False
                        break
                if impossible_position:
                    new_knowledge = ['\nno_sink_%d :- boat(B), size(B, %d), vertical(B), loc(B, %d, %d).\n' % (self.num_no_sink, size, loc, col)]
                    new_knowledge.append('evidence(not(no_sink_%d)).\n' % self.num_no_sink)
                    print ''.join(new_knowledge)
                    self.knowledge += ''.join(new_knowledge)
                    self.num_no_sink += 1
            for loc in range(col, col - size, -1):
                if loc < 1:
                    break
                impossible_position = True
                for j in range(loc, loc + size):
                    if (row, j) not in self.hits:
                        impossible_position = False
                        break
                if impossible_position:
                    new_knowledge = ['\nno_sink_%d :- boat(B), size(B, %d), horizontal(B), loc(B, %d, %d).\n' % (self.num_no_sink, size, row, loc)]
                    new_knowledge.append('evidence(not(no_sink_%d)).\n' % self.num_no_sink)
                    self.knowledge += ''.join(new_knowledge) 
                    print ''.join(new_knowledge)
                    self.num_no_sink += 1

    def problog_move(self):
        """Performs a ProbLog-based query in order to determine the next position to shoot at.
        """

        query = self.knowledge[:]
        query += '\n' + '\n'.join(map(lambda x: 'query(boat_in%s).' % str(x), self.unshot_positions))
        result = get_evaluatable().create_from(PrologString(query)).evaluate()
        not_in_list = []
        for pos in result:
            if not(result[pos]):
                position = extract_position(str(pos))
                print "Inferred no boat in %s" % str(position)
                not_in_list.append(position)
        best_position = extract_position(str(max(result.iteritems(), key=operator.itemgetter(1))[0]))
        print str(best_position)
        print str(not_in_list)
        with open("not_in.data", "wb") as ni:
            pickle.dump(not_in_list, ni)
        with open("bp.data", "wb") as bp:
            pickle.dump(best_position, bp)

    def hypothetical_spaces_used(self, boat_size, horizontal, first_space):
        """Determines the positions taken up by a boat, given its size, orientation, and first position.

        Args:
            boat_size: The size of the boat.
            horizontal: Boolean where True indicates horizontal alignment, False indicates vertical alignment.
        """
        spaces = []
        if horizontal:
            for y in range(first_space[1], first_space[1] + boat_size):
                space_to_add = (first_space[0], y)
                spaces.append(space_to_add)
        else: # vertical
            for x in range(first_space[0], first_space[0] + boat_size):
                space_to_add = (x, first_space[1])
                spaces.append(space_to_add)
        return spaces

    def location_score_matrix(self, boat_size):
        """Analyzes the state of the board and provides scores for each position based on likelihood of
            a boat of a given size being there.

        Args:
            boat_size: The size of the boat.
        """
        score_matrix = [[0 for x in range(self.board_size)] for y in range(self.board_size)]
        print self.current_hits
        for i in range(1, self.board_size+1):
            for j in range(1, self.board_size+1):
                cur_boat_spaces_h = self.hypothetical_spaces_used(boat_size, 1, (i, j))
                cur_boat_spaces_v = self.hypothetical_spaces_used(boat_size, 0, (i, j))

                if self.in_hunt_mode:
                    valid_positions = list(self.unshot_positions)

                    h_overlap = [space for space in cur_boat_spaces_h if space in valid_positions]
                    v_overlap = [space for space in cur_boat_spaces_v if space in valid_positions]

                    if cur_boat_spaces_h == h_overlap: #check if all positions valid
                        for position_h in cur_boat_spaces_h:
                            score_matrix[position_h[0]-1][position_h[1]-1] += 1
                    if cur_boat_spaces_v == v_overlap:
                        for position_v in cur_boat_spaces_v:
                            score_matrix[position_v[0]-1][position_v[1]-1] += 1

                else: #target mode

                    valid_positions = list(self.unshot_positions) + list(self.current_hits)

                    h_overlap = [space for space in cur_boat_spaces_h if space in valid_positions]
                    v_overlap = [space for space in cur_boat_spaces_v if space in valid_positions]

                    if cur_boat_spaces_h == h_overlap:
                        hit_overlap = [space for space in cur_boat_spaces_h if space in self.current_hits]
                        for position_h in cur_boat_spaces_h:
                            if hit_overlap:
                                score_matrix[position_h[0]-1][position_h[1]-1] += 100*len(hit_overlap)
                            else:
                                score_matrix[position_h[0]-1][position_h[1]-1] += 1
                    if cur_boat_spaces_v == v_overlap:
                        hit_overlap = [space for space in cur_boat_spaces_v if space in self.current_hits]
                        for position_v in cur_boat_spaces_v:
                            if hit_overlap:
                                score_matrix[position_v[0]-1][position_v[1]-1] += 100*len(hit_overlap)
                            else:
                                score_matrix[position_v[0]-1][position_v[1]-1] += 1
        #print score_matrix
        return score_matrix

    def remove_hits_from_set(self, pos, size):
        """Works to alleviate ambiguity of hits against unknown boats with knowledge of recently sunk boats.
            Used for PDF function.

            Args: pos: The position that received an indication that a boat was sunk.
                  size: The size of the boat that was just sunk.
        """
        self.sunk_ambiguous_boats.append(size)

        if sum(self.sunk_ambiguous_boats) == len(self.current_hits):
            self.current_hits = set()
            self.sunk_ambiguous_boats = []
            return

        #check if this current case isn't ambiguous, remove if this is the case
        possible_orientations = 0
        possible_orientation_spaces = []
        for i in range(pos[0] - size + 1, pos[0] + 1):
            possible_spaces = [(i, pos[1]) for i in range(i, i + size)]
            ch_overlap = [el for el in possible_spaces if el in list(self.current_hits)]
            if possible_spaces == ch_overlap:
                possible_orientations += 1
                possible_orientation_spaces.append(possible_spaces)

        for j in range(pos[1] - size + 1, pos[1] + 1):
            possible_spaces = [(pos[0], j) for j in range(j, j + size)]
            ch_overlap = [el for el in possible_spaces if el in list(self.current_hits)]
            if possible_spaces == ch_overlap:
                possible_orientations += 1
                possible_orientation_spaces.append(possible_spaces)

        if possible_orientations == 1:
            for el in possible_orientation_spaces[0]:
                self.current_hits.remove((el[0], el[1]))
            self.sunk_ambiguous_boats.remove(size)

    def move(self):
        """Determine the optimal move and make it.

        PROBLOG MODE:

        Determine the unguessed position with the highest probability of holding a boat.
        Shoot in that position and update knowledge accordingly.

        RANDOM MODE:

        Randomly select a position on the board from those that have not been shot at yet.

        HUNT AND TARGET MODE:

        First, randomly select a position on the board from those that have not been shot at yet.
        If hit, all positions directly adjacent in all cardinal directions are added to target list.
        If miss, continue shooting randomly until hit.
        Target list takes priority for future shots; return to random mode when target list is empty.

        PDF MODE:

        Create a PDF representation of the likelihood of where the boats can be, given present board state.
        Fire at location with most possible arrangements of a boat.

        Returns:
            A tuple (x, y):
                x: True if hit, False otherwise.
                y: 0 if the shot did not sink a ship. The size of the
                    ship if the shot did sink a ship.
        """
        if self.move_type == "PROBLOG":
            p = mp.Process(target=self.problog_move)
            p.start()
            p.join()
            not_in_boats = pickle.load(open("not_in.data", "rb"))
            for position in not_in_boats:
                self.boat_not_in(position)
            best_position = pickle.load(open("bp.data", "rb"))

        elif self.move_type == "RANDOM":
            best_position = random.sample(self.unshot_positions, 1)[0]

        elif self.move_type == "HT":
            possible_targets = self.adjacent_positions(self.last_hit_position)

            for el in possible_targets:
                if el in self.unshot_positions and el not in self.targets:
                    self.targets.append(el)

            if len(self.targets): #TARGET MODE
                best_position = self.targets[0]
                self.targets.remove(best_position)

            else: #RANDOM MODE
                best_position = random.sample(self.unshot_positions, 1)[0]

        else: #PDF type
            #print self.in_hunt_mode
            prob_sum = [[0 for x in range(self.board_size)] for y in range(self.board_size)]
            for boat in self.boats:
                score_matrix = self.location_score_matrix(boat)
                for i in range(len(score_matrix)):
                    for j in range(len(score_matrix)):
                        if (i+1, j+1) in self.unshot_positions:
                            prob_sum[i][j] += score_matrix[i][j]

            flatten_prob_sum = [el for row in prob_sum for el in row]
            best_position_value = max(flatten_prob_sum)
            #print best_position_value
            best_position_indices = [(index, row.index(best_position_value)) for index, row in enumerate(prob_sum)
                                     if best_position_value in row] #stackoverflow: getting 2d indices
            '''print best_position_indices
            for el in prob_sum:
                print el'''
            best_position_index = random.choice(best_position_indices)
            best_position = (best_position_index[0]+1, best_position_index[1]+1)


        print "Shooting at: %s" % str(best_position)

        hit, sunk = self.board.shoot((best_position[0]-1, best_position[1]-1))
        if hit:
            self.last_hit_position = best_position
            print "HIT"
        else:
             print "MISS"

        #ADD LOGIC IN THE PRESENCE OF A NON-SINK
        if hit:
            if self.move_type == "PDF":
                self.in_hunt_mode = False
            self.current_hits.add(best_position)
            self.boat_in(best_position)
            if sunk:
                if self.move_type == "PDF":
                    self.remove_hits_from_set(best_position, sunk)
                    if not len(self.current_hits): #cleared all unknown hits
                        self.in_hunt_mode = True
                print "SUNK A BOAT WITH SIZE %d" % sunk
                self.potential_sinks(best_position, sunk)
                # CHECK THIS
                self.boats.pop(self.boats.index(sunk))
            else:
                self.hit_no_sink(best_position)
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
    valid_move_types = ["PROBLOG", "RANDOM", "HT", "PDF"]

    if len(sys.argv) < 4:
        print "USAGE: [MOVE_TYPE] [BOARD_SIZE] [BOAT_SIZE1] [BOAT_SIZE2] ..."
        exit(1)

    if sys.argv[1] not in valid_move_types:
        print "EXPECTED [MOVE_TYPE]: 'PROBLOG', 'RANDOM', 'HT', 'PDF'"
        exit(1)

    move_type = sys.argv[1]
    board_size = int(sys.argv[2])
    boats = map(int, sys.argv[3:])

    g = game(move_type, board_size, boats)
    g.board.print_board()
    g.play_full_game()

    #g.move()


if __name__ == '__main__':
    main()
