import cv2 as cv
import numpy as np

import tkinter as tk
import maestro
import time

from picamera.array import PiRGBArray
from picamera import PiCamera

MOTORS = 1
TURN = 2
BODY = 0
HEADTILT = 4
HEADTURN = 3

tango = maestro.Controller()
body = 6000
headTurn = 6000
headTilt = 6000
motors = 6000
turn = 6000

changeValue = 1000
waitValue = 1

def forward(waitValue):
    global motors
    motors -= changeValue
    tango.setTarget(MOTORS, motors)
    print('move forward: motors = ' + str(motors))
    time.sleep(waitValue)
    motors += changeValue
    tango.setTarget(MOTORS, motors)
    print('stop ' + str(motors))
    time.sleep(waitValue)

def backward(waitValue):
    global motors
    motors -= changeValue
    tango.setTarget(MOTORS, motors)
    print('move backward: motors = ' + str(motors))
    time.sleep(waitValue)
    motors += changeValue
    tango.setTarget(MOTORS, motors)
    print('stop ' + str(motors))
    time.sleep(waitValue)

def turnRight(waitValue):
    global turn
    turn -= changeValue
    tango.setTarget(TURN, turn)
    print('turn right: turn = ' + str(turn))
    time.sleep(waitValue)
    turn += changeValue
    tango.setTarget(TURN, turn)
    print('stop ' + str(turn))
    time.sleep(waitValue)

def turnLeft(waitValue):
    global turn
    turn += changeValue
    tango.setTarget(TURN, turn)
    print('turn left: turn = ' + str(turn))
    time.sleep(waitValue)
    turn -= changeValue
    tango.setTarget(TURN, turn)
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
    if (normalized < 1):
        return 0.2
    elif (normalized > 0.5):
    	return 0.5
    else:
        return normalized

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
width = 640
height = 480
camera.resolution = (width, height)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(width, height))

sightTolerance = height - 100

# allow the camera to warmup
time.sleep(0.1)

hasFailed = False

# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    # grab the raw NumPy array representing the image, then initialize the timestamp
    # and occupied/unoccupied text
    img = frame.array

    #img = cv.imread("turnRight.jpg", cv.IMREAD_COLOR)

    #step one: edges
    gray = cv.cvtColor(img, cv.COLOR_RGB2GRAY)

    #step two: threshold
    ret,threshold = cv.threshold(gray,200,255,cv.THRESH_BINARY)
    contours, hierarchy = cv.findContours(threshold,cv.RETR_TREE,cv.CHAIN_APPROX_SIMPLE)

    numberOfContours = 0
    areaTolerance = 200
    xTotal = 0
    yTotal = 0
    for contour in contours:
        #if the contour is big enough
        if(cv.contourArea(contour)>areaTolerance):
            # compute the center of the contour
            M = cv.moments(contour)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

            if(cY > sightTolerance):
                xTotal += cX
                yTotal += cY
                numberOfContours += 1
            
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
        middleHeight = height/2
        turnTolerance = 50
        #determine if we need to turn
        #if the average is in the middle somewhat
        if((middleOfScreen-turnTolerance)<xAverage<(middleOfScreen+turnTolerance)):
            #go straight
            print("go straight")
            forwardValue = calculateForwardValue(height,yAverage)
            forward(forwardValue)

            #restore defaults
            sightTolerance = height - 20
            hasFailed = False
        else:
            #find out if we need to turn left or right
            if(xAverage < middleOfScreen):
                print("turn left")
                turnValue = calculateTurnValue((width/2),xAverage)
                turnLeft(turnValue)

                forwardValue = calculateForwardValue(height,yAverage)
                forward(forwardValue)

                #restore defaults
                sightTolerance = height - 20
                hasFailed = False
            elif(xAverage > middleOfScreen):
                print("turn right")
                turnValue = calculateTurnValue((width/2),xAverage)
                turnRight(turnValue)

                forwardValue = calculateForwardValue(height,yAverage)
                forward(forwardValue)

                #restore defaults
                sightTolerance = height - 20
                hasFailed = False
            else:
                print("error")
    else:
        if(hasFailed):
            print("searching")
            #restore defaults
            sightTolerance -= 20
            if(sightTolerance < 0):
                print("didn't find anything")
                break
        else:
            hasFailed = True

    cv.imshow("Contours", img)

    key = cv.waitKey(1) & 0xFF
    
    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)

    if key == ord("q"):
        break

cv.destroyAllWindows()
