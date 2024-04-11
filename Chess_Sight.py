import os
from chess_mover import ChessMover


# If games/ folder does not exist, create it
if not os.path.exists("games"):
    os.makedirs("games")

# Create a new ChessMover object
mover = ChessMover()

