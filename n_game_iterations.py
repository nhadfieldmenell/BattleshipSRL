from automate_game import game
import sys
import time
import os
import gc


def main():
    valid_move_types = ["PROBLOG", "RANDOM", "HT", "PDF"]

    if len(sys.argv) < 5:
        print "USAGE: [NUMBER_OF_RUNS] [MOVE_TYPE] [BOARD_SIZE] [BOAT_SIZE1] [BOAT_SIZE2] ..."
        exit(1)

    if sys.argv[2] not in valid_move_types:
        print "EXPECTED [MOVE_TYPE]: 'PROBLOG', 'RANDOM', 'HT', 'PDF'"
        exit(1)

    number_of_runs = int(sys.argv[1])
    move_type = sys.argv[2]
    board_size = int(sys.argv[3])
    boats = map(int, sys.argv[4:])

    # setup folder for data collection

    if not os.path.isdir("data"):
        os.mkdir("data")
    os.chdir("data")

    game_type = move_type + "_" + str(board_size) + "_" + "_".join(str(x) for x in boats)

    if not os.path.isdir(game_type):
        os.mkdir(game_type)
    os.chdir(game_type)

    current_run_folder = str(int(time.time()))
    os.mkdir(current_run_folder)
    os.chdir(current_run_folder)

    start_time = time.time()
    num_moves = 0

    # individual run data files

    for i in range(number_of_runs):

        iteration_start = time.time()
        g = game(move_type, board_size, boats)
        g.board.print_board()
        current_num_moves = g.play_full_game()
        num_moves += current_num_moves

        with open("run" + str(i) + ".data", "wb") as data_file:
            data_file.write("Number of moves: " + str(current_num_moves) + "\nTime taken: " + str(time.time()-iteration_start))
        if move_type == "PROBLOG":
            gc.collect()

    total_time = time.time() - start_time
    time_to_completion = "Overall time to completion: %.2f seconds" % total_time
    average_time = total_time / number_of_runs
    average_time_to_completion = "Average time taken: %.2f" % average_time
    moves_taken = "Total moves taken: %.2f" % num_moves
    average_moves = float(num_moves) / number_of_runs
    average_moves_taken = "Average moves taken: %.2f" % average_moves

    print time_to_completion
    print average_time_to_completion
    print moves_taken
    print average_moves_taken

    with open("summary.data", "wb") as summary_file:
        summary_file.write('\n'.join([time_to_completion, average_time_to_completion, moves_taken, average_moves_taken]))


if __name__ == '__main__':
    main()
