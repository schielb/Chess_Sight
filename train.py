from ultralytics import YOLO

model = YOLO("yolov8n.pt")

model.train(
    data="/home/christopolise/dev/ECEN_631/Team_Projects/Final_Project/Chess_Sight/pieces/data.yaml",
    epochs=10,
    batch=16,
    imgsz=640,
    # device="cuda",
    project="runs/train-chess",
    name="exp",
)

model.predict(
    source="test-vid.webm",
    project="runs/train-chess",
    name="exp",
    save=True
)