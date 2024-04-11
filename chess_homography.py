import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import matplotlib
from PIL import Image

MIN_MATCH_COUNT = 4
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

# Gets the Board
def get_board(query, canvas, pts, patttern_size:tuple=(8,8), plot:bool=False):
    ret, pts1, pts2 = tranform_points(query.copy(), canvas.copy(), pts, plot)
    if not ret:
        return False, None, None
    if plot:
        img = canvas.copy()
        show_board_labels(img, pts2, patttern_size)
    height, width = query.shape[:2]
    M, mask = cv.findHomography(pts2, pts1, cv.RANSAC, 5.0)
    warped_canvas = cv.warpPerspective(canvas, M, (width, height))
    
    
    # TODO: Integrate Chris's Detection Algorithm
    img1 = cv.cvtColor(warped_canvas, cv.COLOR_RGB2GRAY)
    img1 = cv.GaussianBlur(img1, (3, 3), 0)
    img2 = cv.cvtColor(query, cv.COLOR_RGB2GRAY)
    img2 = cv.GaussianBlur(img1, (3, 3), 0)
    diff = cv.absdiff(img1, img2)
    return ret, warped_canvas, diff

# Get the centers of each square of the chessboard
def get_centers(img, patttern_size:tuple=(8,8), plot:bool=False):
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
    if img.shape == 2:
        img = cv.cvtColor(img, cv.COLOR_GRAY2RGB)
    if ret and plot:
        cv.drawChessboardCorners(img, patttern_size, centers, ret)
        plt.imshow(img)
    return centers if ret else None