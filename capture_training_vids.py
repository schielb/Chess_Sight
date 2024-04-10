import cv2 as cv

# Set up the camera
cap = cv.VideoCapture(4)  # Try changing the camera index if necessary

# Set the resolution
cap.set(cv.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 1080)

# Set the brightness
# cap.set(cv.CAP_PROP_BRIGHTNESS, 100)

# Set the FPS
# cap.set(cv.CAP_PROP_FPS, 30)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Set up the video writer
writer = cv.VideoWriter("output-3.mp4", cv.VideoWriter_fourcc(*"mp4v"), 15, (1920, 1080))

# Check if the video writer opened successfully
if not writer.isOpened():
    print("Error: Could not open video writer.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    writer.write(frame)
    cv.imshow('frame', frame)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break

# Release the resources
cap.release()
writer.release()
cv.destroyAllWindows()
