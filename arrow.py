import cv2 as cv
import numpy as np
from chess_homography import get_centers, tranform_points, get_red_n_blue
from ultralytics import YOLO

class Chess_Arrow:
    def __init__(self):
        self.query = cv.imread('query.jpg')
        self.centers, self.corners = get_centers(self.query, plot=False, return_corners=True)
        self.letters = {
            'a': 0,
            'b': 1,
            'c': 2,
            'd': 3,
            'e': 4,
            'f': 5,
            'g': 6,
            'h': 7
        }
        self.model = YOLO('best.pt')
        

    def get_arrow(self, frame, moves, blue=True):
        """Draw an arrow on the frame

        Args:
            frame (np.array): Frame to draw the arrow on
            moves (list(str)): Move to draw the arrow; ex: ['e2e4', '...']
            blue (bool): Is arrow blue ('True' or 'False')

        Returns:
            np.array: Frame with the arrow drawn
        """

        
        if blue:
            color = (255, 0, 0)
        else:
            color = (0, 0, 255)

        ref_ = frame.copy()

        ret, pts1, pts2 = tranform_points(self.query, ref_, self.centers, False)

        pts2_ = np.array(pts2).reshape(-1, 2)

        thickness = (2 * len(moves)) + 1

        for move in moves:
            start = (self.letters[move[0]], 8 - (int(move[1])))
            end = (self.letters[move[2]], 8 - (int(move[3])))

            start = (start[1], start[0])
            end = (end[1], end[0])

            start_in_ref = (pts2_[start[0] * 8 + start[1]][0], pts2_[start[0] * 8 + start[1]][1])
            end_in_ref = (pts2_[end[0] * 8 + end[1]][0], pts2_[end[0] * 8 + end[1]][1])

            cv.arrowedLine(frame, (int(start_in_ref[0]), int(start_in_ref[1])), (int(end_in_ref[0]), int(end_in_ref[1])), color, thickness)

            thickness -= 2

        return frame
    
    def get_masked(self, frame):
        blue, red = get_red_n_blue(frame, False)

        img = np.concatenate(
            (np.expand_dims(red, axis=0),
             np.zeros((1, *red.shape)),
             np.expand_dims(blue, axis=0)),
            axis=0
        )
        img = img.transpose(1,2,0)

        return img
    
    def get_bounded(self, frame):
        result = self.model.predict(
            frame,
            # conf_thres=0.5,
            iou=0.5,
            show_labels=False,
            show_conf=False,
        )

        # print(len(result))

        for data in result[0].boxes.xyxy:
            # print(data)

            cv.rectangle(frame, (int(data[0].item()), int(data[1].item())), (int(data[2].item()), int(data[3].item())), (0, 255, 0), 2)

        return frame
