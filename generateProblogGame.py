import sys


def generate_problog_script(board_size, boats):
    """Writes a ProbLog script that describes a battleship game with specified parameters.

    Args:
        board_size: The integer edge length for the square game board.
        boats: A list of integer boat lengths that are in the game.
            e.g. [2, 2, 3, 4] corresponds to a game with 2 boats of length 2, 1 of length 3,
            and 1 of length 4.
    """
    script_name = "game_%d" % board_size
    for size in boats:
        script_name = "%s_%d" % (script_name, size)
    script_name = "%s.txt" % script_name

    with(open(script_name, 'w')) as outfile:
        for i in range(len(boats)):
            outfile.write("boat(boat_%d).\n" % i)
            outfile.write("size(boat_%d, %d).\n\n" % (i, boats[i]))
        outfile.write("\n")

        outfile.write("0.5::horizontal(B); 0.5::vertical(B) :- boat(B).\n\n\n")

        for size in set(boats):
            possibilities = board_size * (board_size + 1 - size)
            outfile.write("1/%d::loc(B, Row, Col) :- boat(B), between(1, %d, Row), between(1, %d, Col), horizontal(B), size(B, %d).\n"
                    % (possibilities, board_size, board_size + 1 - size, size))
            outfile.write("1/%d::loc(B, Row, Col) :- boat(B), between(1, %d, Row), between(1, %d, Col), vertical(B), size(B, %d).\n\n"
                    % (possibilities, board_size + 1 - size, board_size, size))
        outfile.write("\n")

        outfile.write("occupies(B, Row, Col) :- boat(B), horizontal(B), loc(B, Row, Z), size(B, L), Col-Z < L, Col-Z >= 0, Row > 0, Col > 0.\n")
        outfile.write("occupies(B, Row, Col) :- boat(B), vertical(B), loc(B, Z, Col), size(B, L), Row-Z < L, Row-Z >= 0, Row > 0, Col > 0.\n\n")
        outfile.write("boat_in(Row, Col) :- boat(B), occupies(B, Row, Col).\n\n\n")


        outfile.write("row_col_range(Row, Col) :- between(1, %d, Row), between(1, %d, Col).\n\n" % (board_size, board_size))
        outfile.write("pos_in_range(B, Row1, Col1, Row2, Col2) :- boat(B), horizontal(B), Row1 = Row2, size(B, L), Col1-Col2 < L, Col1-Col2 >= 0.\n")
        outfile.write("pos_in_range(B, Row1, Col1, Row2, Col2) :- boat(B), vertical(B), Col1 = Col2, size(B, L), Row1-Row2 < L, Row1-Row2 >= 0.\n\n")

        outfile.write("double_stacked_constraint :- boat(B), boat(C), not(B = C), row_col_range(Row, Col), occupies(B, Row, Col), occupies(C, Row, Col).\n")
        outfile.write("two_places_constraint :- boat(B), row_col_range(Row1, Col1), row_col_range(Row2, Col2), not(Row1 = Row2), not(Col1 = Col2), loc(B, Row1, Col1), loc(B, Row2, Col2).\n")
        outfile.write("boat_in_unoccupies_constraint :- boat(B), row_col_range(Row, Col), not(boat_in(Row,Col)), occupies(B, Row, Col).\n")
        outfile.write("loc_not_occupies_constraint :- boat(B), row_col_range(Row1, Col1), row_col_range(Row2, Col2), not(occupies(B, Row1, Col1)), loc(B, Row2, Col2), pos_in_range(B, Row1, Col1, Row2, Col2).\n")
        outfile.write("occupies_not_far_constraint :- boat(B), row_col_range(Row1, Col1), row_col_range(Row2, Col2), occupies(B, Row1, Col1), loc(B, Row2, Col2), not(pos_in_range(B, Row1, Col1, Row2, Col2)).\n")
        outfile.write("located_nowhere_constraint :- boat(B)")
        for i in range(1, board_size+1):
            for j in range(1, board_size+1):
                if i == board_size and j == board_size:
                    continue
                outfile.write(", not(loc(B, %d, %d))" % (i,j))
        outfile.write(".\n\n\n")

        outfile.write("evidence(not(double_stacked_constraint)).\n")
        outfile.write("evidence(not(two_places_constraint)).\n")
        outfile.write("evidence(not(boat_in_unoccupies_constraint)).\n")
        outfile.write("evidence(not(loc_not_occupies_constraint)).\n")
        outfile.write("evidence(not(occupies_not_far_constraint)).\n")
        outfile.write("evidence(not(located_nowhere_constraint)).")




def main():
    if len(sys.argv) < 3:
        print "USAGE: [BOARD_SIZE] [BOAT_SIZE1] [BOAT_SIZE2] ..."
        exit(1)

    board_size = int(sys.argv[1])
    boats = map(int, sys.argv[2:])

    generate_problog_script(board_size, boats)


if __name__ == '__main__':
    main()
