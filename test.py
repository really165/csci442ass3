import cv2 as cv
import numpy as np

img = cv.imread("testimage2.jpg", cv.IMREAD_COLOR)

#step one: edges
gray = cv.cvtColor(img, cv.COLOR_RGB2GRAY)

#step two: threshold
ret,threshold = cv.threshold(gray,190,255,cv.THRESH_BINARY)
img2, contours, hierarchy = cv.findContours(threshold,cv.RETR_TREE,cv.CHAIN_APPROX_SIMPLE)

i = 0
areaTolerance = 100
result = gray.copy()
for contour in contours:
    #if the contour is big enough
    if(cv.contourArea(contour)>areaTolerance):
        # compute the center of the contour
        M = cv.moments(contour)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
    
        # draw the contour and center of the shape on the image
        cv.drawContours(img, [contour], -1, (0, 255, 0), 2)
        cv.circle(img, (cX, cY), 7, (0, 0, 0), -1)
        cv.putText(img, "center", (cX - 20, cY - 20),
            cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

cv.imshow("Foreground", img)

cv.waitKey(0)
cv.destroyAllWindows()