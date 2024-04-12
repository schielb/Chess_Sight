import os
from chess_mover import ChessMover
import cv2 as cv


# If games/ folder does not exist, create it
if not os.path.exists("games"):
    os.makedirs("games")

# Create a new ChessMover object
mover = ChessMover()


INIT = 0
READY_TO_PLAY = 1
PLAYER_TURN = 2
VERIFY_PLAYER = 3
COMPUTER_TURN = 4
VERIFY_BOT = 5
GAME_OVER = 6

state = INIT

query = cv.imread

prev_state = []

for i in [1,2,7,8]:
    for j in ["a","b","c","d","e","f","g","h"]:
        prev_state.append(j + str(i))

print(prev_state)



while True:
    if state == INIT:
        print("Welcome to Chess Sight")
        state = READY_TO_PLAY
    elif state == READY_TO_PLAY:
        print(mover.get_board_visual())
        state = PLAYER_TURN
    elif state == PLAYER_TURN:
        player_move = input("Enter your move: ")
        state = VERIFY_PLAYER
    elif state == VERIFY_PLAYER:
        if not mover.attempt_player_move(player_move):
            print("Invalid move")
            state = PLAYER_TURN
        else:
            print(mover.get_board_visual())
            state = COMPUTER_TURN
    elif state == COMPUTER_TURN:
        print("Computer move: ", mover.attempt_player_move(mover.get_best_move()))
        state = VERIFY_BOT
    elif state == VERIFY_BOT:
        print(mover.get_board_visual())
        state = PLAYER_TURN
    elif state == GAME_OVER:
        print("Game Over")
        break
    else:
        print("Invalid state")
        break





query = None # empty board for registration
center, corners = None, None # get_centers(query, plot=False, return_corners=True)
reference = None # filled board with an active game

# ret, reference, diff, occupancy, current_state = get_board(query, reference, centers, corners, plot=False)

# start, end = get_move(prev_state, current_state)