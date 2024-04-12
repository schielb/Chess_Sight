import os
from chess_mover import ChessMover
import cv2 as cv
from chess_homography import get_centers, get_board, get_move



INIT = 0
READY_TO_PLAY = 1
PLAYER_TURN = 2
COMPUTER_TURN = 3
GAME_OVER = 4




class Chess_Sight:
    def __init__(self, debug=False):
        self.mover = ChessMover()
        self.state = INIT
        self.player_first = True
        self.debug = debug

        self.sig_start_game = False
        self.sig_player_moved = False
        self.sig_bot_moved = False
        self.sig_end_game = False

        self.out_stat_player_move = False
        self.out_stat_bot_move = False
        self.out_stat_bot_obeyed = False

        self.out_str_bot_move = None
        self.out_str_suggest = None

        self.query = cv.imread('query.jpg')
        self.centers, self.corners = get_centers(self.query, plot=False, return_corners=True)
        self.reference = None
        self.prev_state = [
            'a1', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1', 
            'a2', 'b2', 'c2', 'd2', 'e2', 'f2', 'g2', 'h2', 
            'a7', 'b7', 'c7', 'd7', 'e7', 'f7', 'g7', 'h7', 
            'a8', 'b8', 'c8', 'd8', 'e8', 'f8', 'g8', 'h8'
        ]

        self.__run()

    def start_game(self, player_first=True, difficulty=10):
        """Start the game

        Args:
            player_first (bool, optional): If True, player starts first. Defaults to True.
            difficulty (int, optional): Difficulty level of the bot. Defaults to 10.

        Returns:
            list: [status, message]
            - [False, "Game not ready yet"] -> If the game is not ready yet
            - [False, "Game already started"] -> If the game is already started
            - [True, "Game starting"] -> If the game started successfully
        """
        if self.state == INIT:
            return [False, "Game not ready yet"]
        
        if self.state != READY_TO_PLAY:
            return [False, "Game already started"]

        
        self.player_first = player_first
        self.sig_start_game = True

        self.mover.set_difficulty(difficulty)

        self.__run()

        return [True, "Game starting"]

    
    def new_player_move(self, player_move_frame):
        """Push a new player move to the game

        Args:
            player_move_frame (np.array): Frame of the player's move

        Returns:
            list: [status, message]
            - [False, "Not player's turn"] -> If it's not the player's turn
            - [True, <move>] -> If the move was successful
            - [False, None] -> If the move was invalid
            - [True, None] -> If the move was successful and the player wins with checkmate
        """
        if self.state != PLAYER_TURN:
            return [False, "Not player's turn"]
        
        self.reference = player_move_frame
        self.sig_player_moved = True

        self.__run()

        return [self.out_stat_player_move, self.out_str_bot_move]


    def new_bot_move(self, bot_move_frame):
        """Push a new bot move to the game

        Args:
            bot_move_frame (np.array): Frame of the bot's move

        Returns:
            list: [status, message]
            - [False, "Not computer's turn"] -> If it's not the computer's turn
            - [True, <list_of_suggestions>] -> If the move was obeyed, offering suggestions for player
            - [False, None] -> If the move was not obeyed
            - [True, None] -> If the move was successful and the computer wins with checkmate

        """
        if self.state != COMPUTER_TURN:
            return [False, "Not computer's turn"]
        
        self.reference = bot_move_frame
        self.sig_bot_moved = True

        self.__run()

        return [self.out_stat_bot_obeyed, self.out_str_suggest]


    def __run(self):
        while True:
            if self.state == INIT:
                # Reset incoming signals
                self.sig_start_game = False
                self.sig_player_moved = False
                self.sig_bot_moved = False

                # Reset outgoing signals
                self.out_stat_player_move = False
                self.out_stat_bot_move = False
                self.out_stat_bot_obeyed = False
                self.out_str_bot_move = None
                self.out_str_suggest = None



                print("Welcome to Chess Sight")
                self.state = READY_TO_PLAY


            elif self.state == READY_TO_PLAY:
                if self.sig_start_game:
                    self.sig_start_game = False

                    if self.player_first:
                        self.state = PLAYER_TURN
                        if self.debug: print("STATE: READY_TO_PLAY -> PLAYER_TURN")
                    else:
                        self.state = COMPUTER_TURN
                        if self.debug: print("STATE: READY_TO_PLAY -> COMPUTER_TURN")


            elif self.state == PLAYER_TURN:
                if self.sig_player_moved:
                    self.sig_player_moved = False

                    ret, reference, diff, occupancy, current_state = get_board(self.query, reference, self.centers, self.corners, plot=False)

                    if ret:
                        start, end = get_move(self.prev_state, current_state)
                        move = start + end

                        self.out_stat_player_move = self.mover.attempt_player_move(move)

                        if self.out_stat_player_move:
                            self.out_str_bot_move = self.mover.get_best_move()
                            # self.out_str_suggest = self.mover.get_eval()
                            self.prev_state = current_state
                            self.state = COMPUTER_TURN
                            if self.debug: print("STATE: PLAYER_TURN -> VERIFY_PLAYER")
                        else:
                            print("Invalid move")
                            self.state = PLAYER_TURN
                            if self.debug: print("STATE: PLAYER_TURN -> PLAYER_TURN")


            elif self.state == COMPUTER_TURN:
                if self.sig_bot_moved:
                    self.sig_bot_moved = False

                    ret, reference, diff, occupancy, current_state = get_board(self.query, reference, self.centers, self.corners, plot=False)

                    self.out_stat_bot_move = ret

                    if ret:
                        start, end = get_move(self.prev_state, current_state)
                        move = start + end

                        self.out_stat_bot_obeyed = move == self.out_str_bot_move
                        
                        if self.out_stat_bot_obeyed:
                            self.prev_state = current_state
                            self.state = PLAYER_TURN
                            if self.debug: print("STATE: COMPUTER_TURN -> PLAYER_TURN")
                        else:
                            print("Bot move not followed!")
                            self.state = COMPUTER_TURN
                            if self.debug: print("STATE: COMPUTER_TURN -> COMPUTER_TURN")


            elif self.state == GAME_OVER:
                print("Game Over")
                break
            else:
                print("Invalid state")
                break

