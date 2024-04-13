from flask import Flask, render_template, request, redirect, url_for, Response
from chess_mover import ChessMover
from Chess_Sight import Chess_Sight
import json
import numpy as np
from arrow import Chess_Arrow

import cv2

app = Flask(__name__)
cs = None
ar = Chess_Arrow()
number_of_moves = 0
move_history = []
eval_num = 50
player_move = False
frame = None
camera = cv2.VideoCapture(0)
game_over = False
bot_move = ""
frame_cnt = 0
player_is_blue = True
rec_moves = []
show_suggestions = True
show_mask = False
show_bound = False

def generate_frames():
    global cs, frame, camera, frame_cnt

    if not camera.isOpened():
        raise Exception("Could not open video device")

    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            if show_mask:
                ret, buffer = cv2.imencode(
                    ".jpg", ar.get_masked(frame)
                )
                bytes_frame = buffer.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + bytes_frame + b"\r\n"
                )
            elif show_bound:
                ret, buffer = cv2.imencode(
                    ".jpg", ar.get_bounded(frame)
                )
                bytes_frame = buffer.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + bytes_frame + b"\r\n"
                )
            else:
                frame_cnt += 1
                if bot_move != "":
                    # print("Arrow frame detected...")
                    ret, buffer = cv2.imencode(
                        ".jpg", ar.get_arrow(frame, [bot_move], blue=not player_is_blue)
                    )
                    # if frame_cnt % 2 == 0:
                    bytes_frame = buffer.tobytes()
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + bytes_frame + b"\r\n"
                    )
                else:
                    if show_suggestions:
                        if len(rec_moves) > 0:
                            ret, buffer = cv2.imencode(
                                ".jpg", ar.get_arrow(frame, [m['Move'] for m in rec_moves], blue=player_is_blue)
                            )
                            bytes_frame = buffer.tobytes()
                            yield (
                                b"--frame\r\n"
                                b"Content-Type: image/jpeg\r\n\r\n" + bytes_frame + b"\r\n"
                            )
                    ret, buffer = cv2.imencode(".jpg", frame)
                    frame_cnt = 0
                bytes_frame = buffer.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + bytes_frame + b"\r\n"
                )


@app.route("/reset", methods=["POST"])
def start_game():
    global number_of_moves, move_history, eval_num, player_move, cs, frame, bot_move, player_is_blue, rec_moves, show_suggestions, show_mask

    print(request.data)

    # Print the request data
    request_data = json.loads(request.data)
    print(request_data)

    cs = Chess_Sight(debug=True)
    print("Initialized Chess Sight")
    number_of_moves = 0
    move_history = []
    eval_num = 50
    player_move = True if request_data["playerColor"] == "blue" else False
    player_is_blue = True if request_data["playerColor"] == "blue" else False
    player_difficulty = request_data["playerDifficulty"]
    view = request_data["view"]

    if view == "aided":
        show_suggestions = True
        show_mask = False
    elif view == 'bounded':
        show_mask = False
    elif view == 'masked':
        show_suggestions = False
        show_mask = True
    elif view == 'none':
        show_suggestions = False
        show_mask = False

    err_msg = ""

    if player_difficulty == "easy":
        player_difficulty = 5
    elif player_difficulty == "medium":
        player_difficulty = 10
    elif player_difficulty == "hard":
        player_difficulty = 15

    status, msg = cs.start_game(player_move, player_difficulty)

    if status:
        if not player_move:
            bot_move = msg
            move_history.append(msg)
        else:
            bot_move = ""
            rec_moves = msg
    else:
        err_msg = msg
    
    print(msg)

    response = {
        "status": status,
        "history": move_history,
        "eval": eval_num,
        "player_move": player_move,
        "err_msg": err_msg,
    }

    print(response)

    return json.dumps(response)


@app.route("/move", methods=["GET"])
def move():
    global number_of_moves, move_history, eval_num, player_move, cs, frame, camera, game_over, bot_move, arrow_frame, rec_moves

    success, frame = camera.read()

    err_msg = ""
    rec_moves = []

    if player_move:
        res = cs.new_player_move(frame)
    else:
        res = cs.new_bot_move(frame)

    if not res:
        print("Turn taking error")
        return
    else:
        status = res[0]
        if status:
            number_of_moves += 1
            eval_num = cs.mover.get_eval()["value"]
            # print(eval_num)
            eval_num = 1.0 / (1.0 + np.exp(-eval_num / 50.0)) * 100
            # print(eval_num)
            if player_move:
                move_history.append(res[1])
                if len(res[2]) == 0:
                    game_over = True
                else:
                    bot_move = res[2]
                    move_history.append(bot_move)
                    game_over = False
            else:
                # move_history.append(bot_move)
                bot_move = ""
                print(res[1])
                if len(res[1]) == 0:
                    game_over = True
                else:
                    game_over = False
                    rec_moves = res[1]
            player_move = not player_move
        else:
            if res[1] is None:
                err_msg = "Invalid move"
            else:
                err_msg = res[1]

    response = {
        "status": status,
        "history": move_history,
        "eval": eval_num,
        "player_move": player_move,
        "game_over": game_over,
        "rec_moves": rec_moves,
        "err_msg": err_msg,
        "bot_move": bot_move,
    }

    print(response)

    return json.dumps(response)

@app.route("/change_view", methods=["POST"])
def change_view():
    global show_suggestions, show_mask, show_bound

    print(request.data)

    # Print the request data
    request_data = json.loads(request.data)
    print(request_data)

    view = request_data["view"]

    if view == "aided":
        show_suggestions = True
        show_mask = False
        show_bound = False
    elif view == 'bounded':
        show_mask = False
        show_suggestions = False
        show_bound = True
    elif view == 'masked':
        show_suggestions = False
        show_mask = True
        show_bound = False
    elif view == 'none':
        show_suggestions = False
        show_mask = False
        show_bound = False

    response = {
        "status": True,
        "show_suggestions": show_suggestions
    }

    print(response)

    return json.dumps(response)

@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/")
def index():
    return render_template("index.html")
