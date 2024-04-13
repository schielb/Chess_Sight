import cv2 as cv
import numpy as np
from chess_homography import get_centers, tranform_points

class Chess_Arrow:
    def __init__(self):
        self.centers, self.corners = get_centers(cv.imread('query.jpg'), plot=False, return_corners=True)
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
        

    def get_arrow(self, frame, move, blue=True):
        """Draw an arrow on the frame

        Args:
            frame (np.array): Frame to draw the arrow on
            move (str): Move to draw the arrow; ex: 'e2e4'
            color (str): Color of the arrow ('red' or 'blue')

        Returns:
            np.array: Frame with the arrow drawn
        """

        
        if blue:
            color = (255, 0, 0)
        else:
            color = (0, 0, 255)

        start = (self.letters[move[0]], 8 - (int(move[1])))
        end = (self.letters[move[2]], 8 - (int(move[3])))

        start = (start[1], start[0])
        end = (end[1], end[0])

        ref_ = frame.copy()

        ret, pts1, pts2 = tranform_points(self.query, ref_, self.centers, False)

        pts2_ = np.array(pts2).reshape(-1, 2)

        start_in_ref = (pts2_[start[0] * 8 + start[1]][0], pts2_[start[0] * 8 + start[1]][1])
        end_in_ref = (pts2_[end[0] * 8 + end[1]][0], pts2_[end[0] * 8 + end[1]][1])

        cv.arrowedLine(frame, start, end, color, 2)

        return frame