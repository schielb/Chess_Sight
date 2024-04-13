import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import matplotlib
from PIL import Image

MIN_MATCH_COUNT = 4
SQUARE_THRESHOLD = 100000
font_args = dict(
    fontFace=cv.FONT_HERSHEY_SIMPLEX,
    fontScale = 1.5,
    thickness = 4,
    color = (255, 0, 0),
    bottomLeftOrigin=False,
)

# The Function to warp points
def tranform_points(query, setting, query_pts=None, plot:bool=True, k:int=2):
    # STEP 1. Initiate SIFT detector
    sift = cv.SIFT_create()

    # STEP 2. : Calculate descriptors (feature vectors)
    kp1, des1 = sift.detectAndCompute(query,None)
    kp2, des2 = sift.detectAndCompute(setting,None)
    if isinstance(des1, type(None)) or len(des1) <= k or isinstance(des2, type(None)) or len(des2)<=k:
        return False, None, None

    # Step 3. Matching descriptor vectors using FLANN matcher
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks = 50)
    flann = cv.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1,des2,k=k)

    # store all the good matches as per Lowe's ratio test.
    good = []
    for m,n in matches:
        if m.distance < 0.7*n.distance:
            good.append(m)

    # Step 4. Draw only good features that the distance (between matched points) is smaller than a threshold
    if plot:
        plt.figure(figsize=(20, 10))
        img3 = cv.drawMatches(query,kp1,setting,kp2,good,None, flags = 2)
        plt.imshow(img3, 'gray'),plt.show()

    if len(good)>MIN_MATCH_COUNT:
        # Step 5. Localize the Object
        src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)

        # Step 6. Find Homography
        M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC,5.0)
        matchesMask = mask.ravel().tolist()
        if np.sum(mask) < MIN_MATCH_COUNT:
            print( "Not enough good matches are found - {}/{}".format(np.sum(mask), MIN_MATCH_COUNT) )
            return False, None, None
        h,w = query.shape[:2]
        if isinstance(M, type(None)):
            print("No Homography was found")
            return False, None, None

        # Step 7. Get the four corners of the object to be detected from theimage_1
        if isinstance(query_pts, type(None)):
            pts1 = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)
        else:
            pts1 = np.float32(query_pts).reshape(-1,1,2)

        # Step 8. Using homography to transform corner points
        pts2 = cv.perspectiveTransform(pts1,M)

        # Step 9. Draw mapped corners in the second image
        setting = cv.polylines(setting,[np.int32(pts2)],True,(255, 0, 0),1, cv.LINE_AA)

        # Plotting Final Result
        if plot:
            plt.figure(figsize=(20, 10))
            img3 = cv.drawMatches(query,kp1,setting,kp2,good,None, matchesMask=matchesMask, flags = 2)
            plt.imshow(img3, 'gray')
            plt.show()
    else:
        print( "Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT) )
        return False, None, None

    return True, pts1, pts2

# Shows the chess position labels, not piece positions
def show_board_labels(img, pts, patttern_size):
    # cv.drawChessboardCorners(img, patttern_size, pts, True)
    pts2_reshaped = pts.reshape(*patttern_size, 2)
    for i in range(patttern_size[0]):
        for j in range(patttern_size[1]):
            x, y = pts2_reshaped[i, j].astype(int)
            name = f"{chr(j + ord('A'))}{8 - i}"
            (text_width, text_height), _ = cv.getTextSize(name, font_args['fontFace'], font_args['fontScale'], font_args['thickness'])
            cv.putText(
                img=img,
                text=name,
                org=(x-text_width//2,y+text_height//2),
                fontFace=font_args['fontFace'],
                fontScale = font_args['fontScale'],
                thickness = font_args['thickness'],
                color = font_args['color'],
                bottomLeftOrigin=font_args['bottomLeftOrigin'],
            )
    plt.figure(figsize=(20, 10))
    plt.imshow(img)
    plt.show()

def get_red_n_blue(img, combine:bool=True, plot:bool=False):
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    blue = cv.inRange(hsv, (100, 0, 0), (130, 255, 255))
    blue = cv.GaussianBlur(blue,(21,21),0)
    _, blue = cv.threshold(blue, 50, 255, cv.THRESH_BINARY)
    red = cv.inRange(hsv, (0, 50, 50), (10, 255, 255))
    red = cv.GaussianBlur(red,(21,21),0)
    _, red = cv.threshold(red, 50, 255, cv.THRESH_BINARY)
    if plot:
        print(np.max(blue))
        print(np.max(red))
        img = np.concatenate(
            (np.expand_dims(red, axis=0),
             np.zeros((1, *red.shape)),
             np.expand_dims(blue, axis=0)),
            axis=0
        )
        img = img.transpose(1,2,0)
        print(img.shape)
        plt.figure(figsize=(20, 10))
        plt.imshow(img)
        plt.show()
    if combine:
        return np.bitwise_or(red, blue)
    return red, blue

# def check_square(img, corners):

# Gets the Board
def get_board(query, canvas, centers, corners, patttern_size:tuple=(8,8), plot:bool=False):
    ret, pts1, pts2 = tranform_points(query.copy(), canvas.copy(), centers, plot)
    if not ret:
        return False, None, None
    if plot:
        img = canvas.copy()
        show_board_labels(img, pts2, patttern_size)
    height, width = query.shape[:2]
    M, mask = cv.findHomography(pts2, pts1, cv.RANSAC, 5.0)
    warped_canvas = cv.warpPerspective(canvas, M, (width, height))
    
    pieces = get_red_n_blue(warped_canvas, plot=plot)

    crnr_size = (patttern_size[0] + 1, patttern_size[1] + 1)
    corners_reshaped = corners.reshape(*crnr_size,2)
    occupancy = []
    spaces_occupant = []
    space = []
    for i in reversed(range(patttern_size[0])):
        row = []
        t_row = []
        for j in range(patttern_size[1]):
            four_corners = corners_reshaped[i:i+2, j:j+2, :]
            right =     int((four_corners[0, 0, 0] + four_corners[0, 1, 0]) // 2)
            left =      int((four_corners[1, 0, 0] + four_corners[1, 1, 0]) // 2)
            top =       int((four_corners[0, 0, 1] + four_corners[1, 0, 1]) // 2)
            bottom =    int((four_corners[0, 1, 1] + four_corners[1, 1, 1]) // 2)
            value = np.sum(pieces[left:right, top:bottom])
            presence = value > SQUARE_THRESHOLD
            name = f"{chr(ord('h')-i)}{j+1}"
            if presence:
                spaces_occupant.append(name)
            row.append(presence)
            t_row.append(name)
        occupancy.append(row)
        space.append(t_row)
    occupancy = np.array(occupancy)
    space = np.array(space)
    print(space)
    # # TODO: Integrate Chris's Detection Algorithm
    # img1 = cv.cvtColor(warped_canvas, cv.COLOR_RGB2GRAY)
    # img1 = cv.GaussianBlur(img1, (3, 3), 0)
    # img2 = cv.cvtColor(query, cv.COLOR_RGB2GRAY)
    # img2 = cv.GaussianBlur(img1, (3, 3), 0)
    # diff = cv.absdiff(img1, img2)
    return ret, warped_canvas, pieces, occupancy, spaces_occupant
castle_sets = [
    ((['e1'], ['g1']), set(['e1', 'h1']), set(['g1', 'f1'])),
    ((['e1'], ['b1']), set(['e1', 'a1']), set(['b1', 'c1'])),
    ((['e1'], ['c1']), set(['e1', 'a1']), set(['c1', 'd1'])),
    ((['e8'], ['g8']), set(['e8', 'h8']), set(['g8', 'f8'])),
    ((['e8'], ['b8']), set(['e8', 'a8']), set(['b8', 'c8'])),
    ((['e8'], ['c8']), set(['e8', 'a8']), set(['c8', 'd8'])),
]

def check_castle(starts, ends):
    starts = set(starts)
    ends = set(ends)
    for m, s, e in castle_sets:
        if s == starts and e == ends:
            return m
    else:
        return None
    
def get_move(state_prev, state_current):
    state_prev = set(state_prev)
    state_current = set(state_current)
    state_intersection = state_current.intersection(state_prev)
    start_locs = list(state_prev.difference(state_intersection))
    end_locs = list(state_current.difference(state_intersection))
    if len(start_locs) != len(end_locs):
        print("WARNING: expected states to have equal occupancies")
    if len(start_locs) == 0:
        print("WARNING: No change occurred")
    if len(start_locs) == 2 and len(end_locs) == 2:
        locs = check_castle(start_locs, end_locs)
        if isinstance(start_locs, type(None)):
            print("WARNING: Not a castle")
        else:
            print("Castling!")
            start_locs, end_locs = locs
    return start_locs, end_locs

# Get the centers of each square of the chessboard
def get_centers(img, patttern_size:tuple=(8,8), return_corners:bool=True, plot:bool=False):
    assert not isinstance(img, type(None)) # confirm that there is an image
    # Differentiate between chessboard size, chessboard find corners, and chesboard corners
    search_pattern = (patttern_size[0]-1, patttern_size[1]-1)
    
    # Copy image to draw
    img = img.copy()
    
    # Get the inner corners with built in function
    ret, corners = cv.findChessboardCorners(img, search_pattern, None)
    
    ########################################################################################################
    # Get the outer corners
    ########################################################################################################
    corners_reshaped = corners.reshape(*search_pattern,2) # Reshape matrix for easy point acccessing
    # Get average spacing between corners
    x_diff = (corners_reshaped[0,:,0] - corners_reshaped[-1,:,0])/(search_pattern[0]-1)
    y_diff = (corners_reshaped[0,:,1] - corners_reshaped[-1,:,1])/(search_pattern[1]-1)
    diff = np.append(np.expand_dims(x_diff, 0), np.expand_dims(y_diff, 0), axis=0).T
    
    # Get left and right set of outer corners
    left = corners_reshaped[-1,:,:] - diff
    right = corners_reshaped[0,:,:] + diff
    
    # Add left and right to corners reshaped so that we can get the four outermost corners
    corners_reshaped = np.append(np.expand_dims(right, 0), corners_reshaped, 0)
    corners_reshaped = np.append(corners_reshaped, np.expand_dims(left, 0), 0)
    corners = corners_reshaped.reshape(-1, 1, 2)
    
    # Get average spacing between corners
    x_diff = (corners_reshaped[:,-1,0] - corners_reshaped[:,0,0])/(search_pattern[0]-1)
    y_diff = (corners_reshaped[:,-1,1] - corners_reshaped[:,0,1])/(search_pattern[1]-1)
    diff = np.append(np.expand_dims(x_diff, 0), np.expand_dims(y_diff, 0), axis=0).T
    
    # Get top and bottom rows of outer corners
    top = corners_reshaped[:,0,:] - diff
    bottom = corners_reshaped[:,-1,:] + diff
    
    # Add top and bottom to corners reshaped so that we can get the four outermost corners
    corners_reshaped = corners_reshaped.transpose(1, 0, 2)
    corners_reshaped = np.append(np.expand_dims(top, 0), corners_reshaped, 0)
    corners_reshaped = np.append(corners_reshaped, np.expand_dims(bottom, 0), 0)
    corners_reshaped = corners_reshaped.transpose(1, 0, 2)
    
    # Convert corners reshaped into original format
    corners = corners_reshaped.reshape(-1, 1, 2)
    ########################################################################################################
    # Convert Corners to Centers
    ########################################################################################################
    centers = []
    for i in range(patttern_size[0]):
        for j in range(patttern_size[1]):
            centers.append(np.mean(corners_reshaped[i:i+2, j:j+2, :].reshape(-1, 2), axis=0))
    centers = np.array(centers).reshape(-1, 1, 2)
    
    ########################################################################################################
    # Plot image and return
    ########################################################################################################
    
    if return_corners:
        if ret and plot:
            crnr_pattern = (patttern_size[0]+1, patttern_size[1]+1)
            cv.drawChessboardCorners(img, patttern_size, centers, ret)
            cv.drawChessboardCorners(img, crnr_pattern, corners, ret)
            plt.imshow(img)
        return (centers, corners) if ret else (None, None)
    if ret and plot:
        cv.drawChessboardCorners(img, patttern_size, centers, ret)
        plt.imshow(img)
    return centers if ret else None