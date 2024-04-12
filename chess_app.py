from flask import Flask, render_template, request, redirect, url_for, Response
from chess_mover import ChessMover

import cv2

app = Flask(__name__)
cm = ChessMover()

def generate_frames():
    global process_this_frame, known_face_encodings, known_face_names, face_added

    camera = cv2.VideoCapture("test-vid.webm")

    if not camera.isOpened():
        raise Exception("Could not open video device")

    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html')