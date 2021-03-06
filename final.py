import cv2 as cv
import numpy as np

#import tkinter as tk
#import maestro
import time

MOTORS = 1
TURN = 2
BODY = 0
HEADTILT = 4
HEADTURN = 3

#tango = maestro.Controller()
body = 6000
headTurn = 6000
headTilt = 6000
motors = 6000
turn = 6000

changeValue = 1000
waitValue = 1

def forward():
    global motors
    motors += changeValue
    #tango.setTarget(MOTORS, motors)
    print('move forward: motors = ' + str(motors))
    time.sleep(waitValue)
    motors -= changeValue
    #tango.setTarget(MOTORS, motors)
    print('stop ' + str(motors))
    time.sleep(waitValue)

def backward():
    global motors
    motors -= changeValue
    #tango.setTarget(MOTORS, motors)
    print('move backward: motors = ' + str(motors))
    time.sleep(waitValue)
    motors += changeValue
    #tango.setTarget(MOTORS, motors)
    print('stop ' + str(motors))
    time.sleep(waitValue)

def turnRight():
    global turn
    turn -= changeValue
    #tango.setTarget(TURN, turn)
    print('turn right: turn = ' + str(turn))
    time.sleep(waitValue)
    turn += changeValue
    #tango.setTarget(TURN, turn)
    print('stop ' + str(turn))
    time.sleep(waitValue)

def turnLeft():
    global turn
    turn += changeValue
    #tango.setTarget(TURN, turn)
    print('turn left: turn = ' + str(turn))
    time.sleep(waitValue)
    turn -= changeValue
    #tango.setTarget(TURN, turn)
    print('stop ' + str(turn))
    time.sleep(waitValue)

def calculateTurnValue(center, xPos):
    distanceFromCenter = 0
    if(center > xPos):
        distanceFromCenter = center - xPos
    elif(xPos > center):
        distanceFromCenter = xPos - center
    else:
        distanceFromCenter = 0
    normalized = distanceFromCenter/center
    return normalized

def calculateForwardValue(height, yPos):
    normalized = 1-(yPos/height)
    return normalized

img = cv.imread("testimage2.jpg", cv.IMREAD_COLOR)

#step one: edges
gray = cv.cvtColor(img, cv.COLOR_RGB2GRAY)

#step two: threshold
ret,threshold = cv.threshold(gray,190,255,cv.THRESH_BINARY)
img2, contours, hierarchy = cv.findContours(threshold,cv.RETR_TREE,cv.CHAIN_APPROX_SIMPLE)

numberOfContours = 0
areaTolerance = 100
xTotal = 0
yTotal = 0
for contour in contours:
    #if the contour is big enough
    if(cv.contourArea(contour)>areaTolerance):
        numberOfContours += 1
        # compute the center of the contour
        M = cv.moments(contour)
        cX = int(M["m10"] / M["m00"])
        xTotal += cX
        cY = int(M["m01"] / M["m00"])
        yTotal += cY
    
        # draw the contour and center of the shape on the image
        cv.drawContours(img, [contour], -1, (0, 255, 0), 2)
        cv.circle(img, (cX, cY), 7, (0, 0, 0), -1)
        cv.putText(img, "center", (cX - 20, cY - 20),
            cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
#if a contour was found
if(numberOfContours > 0):
    xAverage = int(xTotal/numberOfContours)
    yAverage = int(yTotal/numberOfContours)
    print("Average center is (" + str(xAverage) + ", " + str(yAverage) + ")")

    height, width, channels = img.shape
    middleOfScreen = width/2
    turnTolerance = 50
    #determine if we need to turn
    #if the average is in the middle somewhat
    if((middleOfScreen-turnTolerance)<xAverage<(middleOfScreen+turnTolerance)):
        #go straight
        print("go straight")
        forwardValue = calculateForwardValue(height,yAverage)
        print(forwardValue)
        time.sleep(forwardValue)
        print("we're good")
        #forward()
    else:
        #find out if we need to turn left or right
        if(xAverage < middleOfScreen):
            print("turn left")
            turnValue = calculateTurnValue((width/2),xAverage)
            print(turnValue)
            time.sleep(turnValue)

            print("go straight")
            forwardValue = calculateForwardValue(height,yAverage)
            print(forwardValue)
            time.sleep(forwardValue)
            print("we're good")
            #turnLeft()
            #forward()
        elif(xAverage > middleOfScreen):
            print("turn right")
            turnValue = calculateTurnValue((width/2),xAverage)
            print(turnValue)
            time.sleep(turnValue)

            print("go straight")
            forwardValue = calculateForwardValue(height,yAverage)
            print(forwardValue)
            time.sleep(forwardValue)
            print("we're good")
            #turnRight()
            #forward()
        else:
            print("error")
else:
    print("stop")

cv.imshow("Foreground", img)

cv.waitKey(0)
cv.destroyAllWindows()
