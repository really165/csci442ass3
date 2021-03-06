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

IP = '10.200.47.148'

blurIterations = 3
cannyThreshold1 = 150
cannyThreshold2 = 400
erosionIterations = 5
edgeCutoffPercentage = 0.05
whiteToleranceColor = 215
grayscaleToleranceValue = 7
#distance it needs to be from the sides in order to turn
turnTolerance = 120
moveTolerance = 120
#how much the robot turns or moves when it needs to
changeValue = 1000
waitValue = 0.2
#color tolerance used when looking for orange and blue pixels
pinkR = 245
pinkG = 187
pinkB = 212
yellowR = 221
yellowG = 194
yellowB = 107
colorTolerance = 25
#how long the robot takes to turn around
turnAroundTime = 2.6

globalVar = ""

class ClientSocket(threading.Thread):
    def __init__(self, IP, PORT):
        super(ClientSocket, self).__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((IP, PORT))
  
        print ('connected')
        self.alive = threading.Event()
        self.alive.set()

    def recieveData(self):
        global globalVar
        try:
            data = self.s.recv(105)
            print (data)
            globalVar = data
        except IOError as e:
            if e.errno == errno.EWOULDBLOCK:
                pass

    def sendData(self, sendingString):
        print ('sending')
        sendingString += "\n"
        self.s.send(sendingString.encode('UTF-8'))
        print ('done sending')

    def run(self):
        global globalVar
        while self.alive.isSet():
            data = self.s.recv(105)
            print (data)
            globalVar = data
            if(data == "0"):
                self.killSocket()           
            
    def killSocket(self):
        self.alive.clear()
        self.s.close()
        print("Goodbye")
        exit()

PORT = 5010
client = ClientSocket(IP, PORT)

#greets the human
def sayGivePen():
    for i in ["give pen human"]:
        time.sleep(1)
        client.sendData(i)            
    print("Exiting Sends")

#greets the human
def sayThanks():
    for i in ["thank you"]:
        time.sleep(1)
        client.sendData(i)            
    print("Exiting Sends")

MOTORS = 1
TURN = 2
BODY = 0
HEADTILT = 4
HEADTURN = 3
SHOULDER = 7
HAND = 8

tango = maestro.Controller()
body = 6000
headTurn = 6000
headTilt = 4000
motors = 6000
turn = 6000
shoulder = 6000
hand = 6000

#move parts into the right positions
def setDefaults():
    #center head
    global headTurn
    headTurn = 6000
    tango.setTarget(HEADTURN, headTurn)
    #tilt head down
    global headTilt
    headTilt = 4000
    tango.setTarget(HEADTILT, headTilt)
    #close hand
    global hand
    hand = 7000
    tango.setTarget(HAND, hand)
    #move arm down
    global shoulder
    shoulder = 6000
    tango.setTarget(SHOULDER, shoulder)

def grabPen():
    #look up
    global headTilt
    headTilt = 6100
    tango.setTarget(HEADTILT, headTilt)
    #open hand
    global hand
    hand = 6000
    tango.setTarget(HAND, hand)
    #move arm up
    global shoulder
    shoulder = 8000
    tango.setTarget(SHOULDER, shoulder)
    #ask for pen
    sayGivePen()
    #wait two seconds
    time.sleep(3)
    sayThanks()
    #close hand
    hand = 7000
    tango.setTarget(HAND, hand)
    #go back to defaults
    setDefaults()

#drop the pen
def dropPen():
    #raise arm
    global shoulder
    shoulder = 8000
    tango.setTarget(SHOULDER, shoulder)
    #open hand
    global hand
    hand = 6000
    tango.setTarget(HAND, hand)
    #wait one second
    time.sleep(1)
    #lower arm
    shoulder = 6000
    tango.setTarget(SHOULDER, shoulder)
    #close hand
    hand = 7000
    tango.setTarget(HAND, hand)

def performSidefill(edges):
    global img
    global width
    global height
    global percentOffTheEdges
    for x in range(0,width-1):
        foundWhite = False
        for y in range(height-1,0,-1):
            if(foundWhite or x < percentOffTheEdges or x > (width-1)-percentOffTheEdges or y < topCutoff):
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
    #cv.imshow("dilation", dilation)
    sidefill = performSidefill(dilation)
    erosion = cv.erode(sidefill,kernel,iterations = 4)
    return erosion

def findMax(sidefill):
    global width
    global height
    #start from the top
    #find the first acceptable segment
    for y in range(topCutoff,height-1):
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
    motors -= changeValue
    tango.setTarget(MOTORS, motors)
    print('moving forward')
    time.sleep(waitValue)
    motors += changeValue
    tango.setTarget(MOTORS, motors)
    time.sleep(waitValue)

def turnAround():
    turn = 6000
    turn -= changeValue
    tango.setTarget(TURN, turn)
    print('turning around')
    time.sleep(turnAroundTime)
    turn += changeValue
    tango.setTarget(TURN, turn)
    time.sleep(waitValue)

#turn until the colored pixels are centered
def coloredIsCentered():
    global img
    #process the image
    blur = cv.medianBlur(img,blurIterations)
    edges = cv.Canny(blur,cannyThreshold1,cannyThreshold2)
    kernel = np.ones((5,5),np.uint8)
    dilation = cv.dilate(edges,kernel,iterations = 3)
    #cv.imshow("output", dilation)
    averageX, averageY = coloredPixelsAveragePosition(dilation)
    if(averageX == -1 and averageY == -1):
        print("no colored pixels found")
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
    for x in range(percentOffTheEdges,(width-1)-percentOffTheEdges):
        for y in range(((height-1)-colorCutoff),(height-1)):
            blue = (int)(img[y][x][0])
            green = (int)(img[y][x][1])
            red = (int)(img[y][x][2])
            if(edges[y][x]==255 and isColored(blue, green, red)):
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
    if(pinkR-colorTolerance < red < pinkR+colorTolerance and pinkG-colorTolerance < green < pinkG+colorTolerance and pinkB-colorTolerance < blue < pinkB+colorTolerance):
        return True
    elif(yellowR-colorTolerance < red < yellowR+colorTolerance and yellowG-colorTolerance < green < yellowG+colorTolerance and yellowB-colorTolerance < blue < yellowB+colorTolerance):
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

#get limbs into position
setDefaults()

#initial capture
#img = cv.imread("demoimage3.png", cv.IMREAD_COLOR)
camera = PiCamera()
width = 352
height = 240
turnTolerance = (int)(width*0.3)
moveTolerance = (int)(height*0.1)
maxSegment = width - (int)(width*0.9)
minSegment = (int)(width*0.3)
topCutoff = (int)(height*0.2)
camera.resolution = (width, height)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(width, height))
img = getCapture()
percentOffTheEdges = (int)(width*edgeCutoffPercentage)
maxX = (int)(width/2)
maxY = height

#orientate the robot until the blue and orange pixels are somewhat centered
while(not coloredIsCentered()):
    #update the capture
    img = getCapture()
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

#move forward until the maxY is too close to move
#initial process of the image
sidefill = processImageWhite()
maxX, maxY = findMax(sidefill)
while(canMove(maxX, maxY)):
    img = getCapture()
    sidefill = processImageWhite()
    maxX, maxY = findMax(sidefill)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

#get the pen
grabPen()

#turn around
turnAround()

while(not coloredIsCentered()):
    #update the capture
    img = getCapture()
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

#go forward again
sidefill = processImageWhite()
maxX, maxY = findMax(sidefill)
while(canMove(maxX, maxY)):
    img = getCapture()
    sidefill = processImageWhite()
    maxX, maxY = findMax(sidefill)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

#drop pencil
dropPen()

cv.waitKey(0)
cv.destroyAllWindows()
