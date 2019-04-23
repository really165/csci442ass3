import socket, time
import threading
import queue

import numpy as np
import cv2 as cv

import tkinter as tk
import maestro
import time

from picamera.array import PiRGBArray
from picamera import PiCamera

blurIterations = 3
cannyThreshold1 = 150
cannyThreshold2 = 400
erosionIterations = 5
edgeCutoffPercentage = 0.05
whiteToleranceColor = 180
grayscaleToleranceValue = 10
#distance it needs to be from the sides in order to turn
turnTolerance = 120
moveTolerance = 120
#how much the robot turns or moves when it needs to
changeValue = 1000
waitValue = 0.2
#color tolerance used when looking for orange and blue pixels
colorTolerance = 10

MOTORS = 1
TURN = 2
BODY = 0
HEADTILT = 4
HEADTURN = 3

tango = maestro.Controller()
body = 6000
headTurn = 6000
headTilt = 6200
motors = 6000
turn = 6000

def performSidefill(edges):
    global img
    global width
    global height
    global percentOffTheEdges
    for x in range(0,width-1):
        foundWhite = False
        for y in range(height-1,0,-1):
            if(foundWhite or x < percentOffTheEdges or x > (width-1)-percentOffTheEdges):
                edges[y][x] = 0
            elif(edges[y][x] == 255):
                blue = (int)(img[y][x][0])
                green = (int)(img[y][x][1])
                red = (int)(img[y][x][2])
                if(blue>whiteToleranceColor and green>whiteToleranceColor and red>whiteToleranceColor and isGrayscale(blue, green, red)):
                    foundWhite = True
                    edges[y][x] = 0
                else:
                    edges[y][x] = 255
            else:
                edges[y][x] = 255
    return edges

#checks if a pixel is grayscale
def isGrayscale(b, g, r):
    #values need to be no more than 10 away from each other
    diffBG = abs(b-g)
    diffGR = abs(g-r)
    diffBR = abs(b-r)
    if(diffBG<grayscaleToleranceValue and diffBR<grayscaleToleranceValue and diffGR<grayscaleToleranceValue):
        return True
    else:
        return False

#process image and only pay attention to the white pixels
def processImageWhite():
    global img
    blur = cv.medianBlur(img,blurIterations)
    edges = cv.Canny(blur,cannyThreshold1,cannyThreshold2)
    kernel = np.ones((5,5),np.uint8)
    dilation = cv.dilate(edges,kernel,iterations = 2)
    cv.imshow("dilation", dilation)
    sidefill = performSidefill(dilation)
    erosion = cv.erode(sidefill,kernel,iterations = 4)
    return erosion

def findMax(sidefill):
    global width
    global height
    #start from the top
    #find the first acceptable segment
    for y in range(0,height-1):
        correctedY = maxY-y
        preferredSize = (int)((minSegment-maxSegment)*((correctedY)/(height))+maxSegment)
        whitesFound = 0
        leftSegment = 0
        rightSegment = 0
        segmentStarted = False
        #print(correctedY)
        #print(preferredSize)
        for x in range(0,width-1):
            #if we haven't found a segment yet
            if(not segmentStarted):
                #if the pixel is white
                if(sidefill[y][x]==255):
                    #set left
                    leftSegment = x
                    #increment white count
                    whitesFound += 1
                    segmentStarted = True
            #if a segment was started
            else:
                #if the pixel is white
                if(sidefill[y][x]==255):
                    #increment white count
                    whitesFound += 1
                #if the pixel is black
                else:
                    #determine if the segment is long enough
                    rightSegment = x-1
                    #if it is long enough
                    if(rightSegment-leftSegment > preferredSize):
                        middleX = (int)((rightSegment+leftSegment)/2)
                        middleY = y
                        return middleX, middleY
                    else:
                        segmentStarted = False
                        whitesFound = 0
    return (width/2),height

#move based on the point given
def canMove(x, y):
    global width
    global height
    correctedY = height-y

    #determine if we need to move
    if(correctedY<moveTolerance):
        print("stay put")
        return False

    #determine if we must turn
    if(x<turnTolerance):
        print("turn left")
        turnLeft(waitValue)
        forward(waitValue)
        return True
    elif(x>(width-1)-turnTolerance):
        print("turn right")
        turnRight(waitValue)
        forward(waitValue)
        return True
    else:
        print("no turn")
        forward(waitValue)
        return True

def turnRight(waitValue):
    turn = 6000
    turn -= changeValue
    tango.setTarget(TURN, turn)
    print('turning right')
    time.sleep(waitValue)
    turn += changeValue
    tango.setTarget(TURN, turn)
    time.sleep(waitValue)

def turnLeft(waitValue):
    turn = 6000
    turn += changeValue
    tango.setTarget(TURN, turn)
    print('turning left')
    time.sleep(waitValue)
    turn -= changeValue
    tango.setTarget(TURN, turn)
    time.sleep(waitValue)

def forward(waitValue):
    motors = 6000
    motors += changeValue
    tango.setTarget(MOTORS, motors)
    print('moving forward')
    time.sleep(waitValue)
    motors -= changeValue
    tango.setTarget(MOTORS, motors)
    time.sleep(waitValue)

#turn until the colored pixels are centered
def coloredIsCentered():
    global img
    #process the image
    blur = cv.medianBlur(img,blurIterations)
    edges = cv.Canny(blur,cannyThreshold1,cannyThreshold2)
    kernel = np.ones((5,5),np.uint8)
    dilation = cv.dilate(edges,kernel,iterations = 3)
    averageX, averageY = coloredPixelsAveragePosition(dilation)
    if(averageX == -1 and averageY == -1):
        print("no colored pixels found")
        turnRight(waitValue)
        return False
    elif((height-averageY)>(int)(height/2)):
        print("invalid average found")
        turnRight(waitValue)
        return False
    else:
        cv.circle(img,(averageX,averageY),10,(255,0,0),-1)
        middleX = (int)(width/2)
        if(averageX<middleX-turnTolerance):
            print("found color; turn left")
            turnLeft(waitValue)
            return False
        elif(averageX>middleX+turnTolerance):
            print("found color; turn right")
            turnRight(waitValue)
            return False
        else:
            print("color is centered; ready to move")
            return True

def coloredPixelsAveragePosition(edges):
    global width
    global height
    xTotal = 0
    yTotal = 0
    numberOfPoints = 0
    for x in range(0,width-1):
        if(x > percentOffTheEdges and x < (width-1)-percentOffTheEdges):
            for y in range(height-1,0,-1):
                blue = (int)(img[y][x][0])
                green = (int)(img[y][x][1])
                red = (int)(img[y][x][2])
                if(edges[y][x]==255 and (not isGrayscale(blue,green,red))):
                    xTotal += x
                    yTotal += y
                    numberOfPoints += 1
    if(numberOfPoints>0):
        xAverage = (int)(xTotal/numberOfPoints)
        yAverage = (int)(yTotal/numberOfPoints)
    else:
        xAverage = -1
        yAverage = -1
    return xAverage, yAverage

#checks if the pixel is blue or orange
def isColored(blue, green, red):
    #check blue first
    if(185-colorTolerance < red < 185+colorTolerance and 203-colorTolerance < green < 203+colorTolerance and 205-colorTolerance < blue < 205+colorTolerance):
        return True
    elif(218-colorTolerance < red < 218+colorTolerance and 181-colorTolerance < green < 181+colorTolerance and 72-colorTolerance < blue < 72+colorTolerance):
        return True
    else:
        return False

def getCapture():
    # capture frames from the camera
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        # grab the raw NumPy array representing the image, then initialize the timestamp
        # and occupied/unoccupied text
        img = frame.array
        break
    rawCapture.truncate(0)
    return img

#initial capture
#img = cv.imread("demoimage3.png", cv.IMREAD_COLOR)
camera = PiCamera()
width = 480
height = 360
maxSegment = width - (int)(width*0.9)
minSegment = (int)(width*0.2)
camera.resolution = (width, height)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(width, height))
img = getCapture()
percentOffTheEdges = (int)(width*edgeCutoffPercentage)
maxX = (int)(width/2)
maxY = height

while(True):
    img = getCapture()
    sidefill = processImageWhite()
    #maxX, maxY = findMax(sidefill)
    #cv.circle(img,(maxX,maxY),10,(0,255,0),-1)
    cv.imshow("sidefill", sidefill)
    #cv.imshow("original", img)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

#todo: put pencil in box

cv.waitKey(0)
cv.destroyAllWindows()
