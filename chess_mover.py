from stockfish import Stockfish

class ChessMover:
    def __init__(self):
        self.sf = Stockfish("/usr/bin/stockfish")
        self.sf.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")


    def get_best_move(self):
        return self.sf.get_best_move()
    
    def attempt_player_move(self, move: str):
        if self.sf.is_move_correct(move):
            self.sf.make_moves_from_current_position([move])
            return True
        else:
            return False
    
    def get_board(self):
        return self.sf.get_fen_position()
    
    def get_board_visual(self):
        return self.sf.get_board_visual()
    
    def get_eval(self):
        return self.sf.get_evaluation()
    
    def set_sf_path(self, path):
        self.sf = Stockfish(path)

    def get_game_over(self):
        return self.sf.get
    
    def get_move_suggestions(self, num=3):
        return self.sf.get_top_moves(num)
    
    def set_difficulty(self, level):
        self.sf.set_skill_level(level)
    
    
if __name__ == '__main__':
    mover = ChessMover()
    
    while True:
        print(mover.get_board_visual())

        player_move = input("Enter your move: ")
        if not mover.attempt_player_move(player_move):
            print("Invalid move")
            continue

        print(mover.get_board_visual())

        print("Computer move: ", mover.attempt_player_move(mover.get_best_move()))