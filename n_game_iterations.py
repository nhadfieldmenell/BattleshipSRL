from automate_game import game
import sys
import time
import os
import multiprocessing as mp


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

    data_folder = "data"

    if not os.path.isdir(data_folder):
        os.mkdir(data_folder)
    os.chdir(data_folder)

    game_type = move_type + "_" + str(board_size) + "_" + "_".join(str(x) for x in boats)

    if not os.path.isdir(game_type):
        os.mkdir(game_type)
    os.chdir(game_type)

    current_run_folder = str(int(time.time()))
    os.mkdir(current_run_folder)
    os.chdir(current_run_folder)

    start_time = time.time()

    # individual runs
    num_moves = 0
    for i in range(number_of_runs):
        g = game(move_type, board_size, boats)
        g.board.print_board()
        if move_type == "PROBLOG":
            p = mp.Process(target=g.play_full_game, args=(True, i))
            p.start()
            p.join()
        else:
            g.play_full_game(True, i)
        with open("run" + str(i) + ".data", "r") as data_file:
            current_moves = data_file.readline().strip().split(' ')[-1]
            num_moves += int(current_moves)

    total_time = time.time() - start_time
    time_to_completion = "Overall time to completion: %.2f seconds" % total_time
    average_time = total_time / number_of_runs
    average_time_to_completion = "Average time taken: %.2f seconds" % average_time

    moves_taken = "Total moves taken: %d" % num_moves
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
