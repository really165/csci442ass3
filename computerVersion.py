import numpy as np
import cv2 as cv
#import tkinter as tk
#import maestro
import time

blurIterations = 3
cannyThreshold1 = 300
cannyThreshold2 = 700
erosionIterations = 5
edgeCutoffPercentage = 0.05
whiteToleranceColor = 200
maxSegment = 600
minSegment = 50
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

#tango = maestro.Controller()
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
    for x in range(width-1,0,-1):
        if(x > percentOffTheEdges and x < (width-1)-percentOffTheEdges):
            foundWhite = False
            for y in range(height-1,0,-1):
                if(foundWhite):
                    edges[y][x] = 0
                elif(not foundWhite and edges[y][x] == 255):
                    if(img[y][x][0]>whiteToleranceColor and img[y][x][1]>whiteToleranceColor and img[y][x][2]>whiteToleranceColor):
                        foundWhite = True
                        edges[y][x] = 0
                else:
                    edges[y][x] = 255
    return edges

#process image and only pay attention to the white pixels
def processImageWhite(img):
    #global img
    blur = cv.medianBlur(img,blurIterations)
    edges = cv.Canny(blur,cannyThreshold1,cannyThreshold2)
    kernel = np.ones((5,5),np.uint8)
    dilation = cv.dilate(edges,kernel,iterations = 1)
    sidefill = performSidefill(dilation)
    erosion = cv.erode(sidefill,kernel,iterations = 4)
    return erosion

def findMax(sidefill):
    global width
    global height
    foundSegment = False

    #start from the top
    #find the first acceptable segment
    for y in range(0,height-1):
        correctedY = maxY-y
        preferredSize = (maxSegment-minSegment)*((correctedY)/(height))+minSegment
        whitesFound = 0
        leftSegment = 0
        rightSegment = 0
        for x in range(0,width-1):
            #if we haven't found a segment and have found a white pixel
            if(not foundSegment and sidefill[y][x]==255):
                #increment pixel count
                whitesFound += 1
                #set the left point of the segment
                leftSegment = x
                #say we've found a segment
                foundSegment = True
            #if we've found a segment and have found a white pixel
            elif(foundSegment and sidefill[y][x]==255):
                #just increment the pixel count
                whitesFound += 1
            #if we've found a segment and have found a black pixel
            elif(foundSegment and sidefill[y][x] == 0):
                #determine if the segment is long enough
                rightSegment = x-1
                #if it is long enough
                if(rightSegment-leftSegment > preferredSize):
                    middleX = (int)((rightSegment+leftSegment)/2)
                    middleY = y
                    return middleX, middleY
    return 0,0

#move based on the point given
def move(x, y):
    global width
    global height
    correctedY = height-y
    #determine if we must turn
    if(x<turnTolerance):
        print("turn left")
        turnLeft(waitValue)
    elif(x>(width-1)-turnTolerance):
        print("turn right")
        turnRight(waitValue)
    else:
        print("no turn")
    #determine if we need to move
    if(correctedY>moveTolerance):
        print("must move forward")
        forward(waitValue)
    else:
        print("stay put")

def turnRight(waitValue):
    turn = 6000
    turn -= changeValue
    #tango.setTarget(TURN, turn)
    print('turning right')
    time.sleep(waitValue)
    turn += changeValue
    #tango.setTarget(TURN, turn)
    time.sleep(waitValue)

def turnLeft(waitValue):
    turn = 6000
    turn += changeValue
    #tango.setTarget(TURN, turn)
    print('turning left')
    time.sleep(waitValue)
    turn -= changeValue
    #tango.setTarget(TURN, turn)
    time.sleep(waitValue)

def forward(waitValue):
    motors = 6000
    motors += changeValue
    #tango.setTarget(MOTORS, motors)
    print('moving forward')
    time.sleep(waitValue)
    motors -= changeValue
    #tango.setTarget(MOTORS, motors)
    time.sleep(waitValue)

#turn until the blue bar is centered
def turnUntilBlue():
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
                if(edges[y][x]==255 and isColored(img[y][x][0], img[y][x][1], img[y][x][2])):
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

img = cv.imread("demoimage3.png", cv.IMREAD_COLOR)
height, width, channels = img.shape
percentOffTheEdges = (int)(width*edgeCutoffPercentage)
maxX = (int)(width/2)
maxY = height

#get the sidefill of the image
sidefill = processImageWhite(img)
#find the highest point that can be moved to
maxX, maxY = findMax(sidefill)
cv.circle(img,(maxX,maxY),10,(0,255,0),-1)
#move based on the point found
move(maxX, maxY)
turnUntilBlue()

cv.imshow("sidefill", sidefill)
cv.imshow("original", img)

cv.waitKey(0)
cv.destroyAllWindows()
