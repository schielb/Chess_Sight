from ultralytics import YOLO

import tensorboard as tb

prefix = 'Team_Projects/Final_Project/Chess_Sight'

# Start tensorboard
tb.notebook.start(f"--logdir {prefix}/runs --host 0.0.0.0")

# model = YOLO("yolov8x.pt")

# model.train(
#     data="/home/christopolise/ECEN_631/Team_Projects/Final_Project/Chess_Sight/pieces6/data.yaml",
#     epochs=100,
#     batch=-1,
#     imgsz=640,
#     device="cuda",
#     project=f"{prefix}/runs/train-chess",
#     name="exp",
# )

model = YOLO(f"{prefix}/runs/train-chess/exp9/weights/best.pt")

print(model.names)

class_limits = {
    "K": 1,
    "Q": 1,
    "R": 2,
    "B": 2,
    "N": 2,
    "P": 8,
    "k": 1,
    "q": 1,
    "r": 2,
    "b": 2,
    "n": 2,
    "p": 8,
}

# for key, value in model.names.items():
#     print(f"Class: {key} - {type(key)}, Label: {value} - {type(value)}, Limit: {class_limits[value]} - {type(class_limits[value])}")
#     results = model.predict(
#         source=f"{prefix}/test-vid.webm",
#         project="runs/train-chess",
#         name="exp",
#         save=True,
#         stream=True,
#         classes=[key],
#         max_det=class_limits[value],
#         device="cuda",
#     )
#     results = list(results)

results = model.predict(
        source=f"{prefix}/test-vid.webm",
        project="runs/train-chess",
        name="exp",
        save=True,
        stream=True,
        device="cuda",
        max_det=32,
    )
results = list(results)