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

face_cascade = cv.CascadeClassifier('data/haarcascades/haarcascade_frontalface_default.xml')

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
            
IP = '10.200.47.148'
PORT = 5010
client = ClientSocket(IP, PORT)

#greets the human
def sayHello():
    #IP = '10.200.28.12'
    #PORT = 5010
    #client = ClientSocket(IP, PORT)
    ##client.start()

    for i in ["hello human"]:
        time.sleep(1)
        client.sendData(i)            
    print("Exiting Sends")

#greets the human
def sayWhereAreYou():
    #IP = '10.200.28.12'
    PORT = 5010
    client = ClientSocket(IP, PORT)
    #client.start()

    for i in ["ugh where are you"]:
        time.sleep(1)
        client.sendData(i)            
    print("Exiting Sends")

#how much power is sent into the motors
headTurnValue = 100
#how long the head stabilizes
headTurnWaitValue = 0.5

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

#looks left once and waits
def lookLeft():
    global headTurn
    headTurn += headTurnValue
    print("looking left")
    tango.setTarget(HEADTURN, headTurn)
    print("stabilizing")
    time.sleep(headTurnWaitValue)
    
#looks right once and waits
def lookRight():
    global headTurn
    headTurn -= headTurnValue
    print("looking right")
    tango.setTarget(HEADTURN, headTurn)
    print("stabilizing")
    time.sleep(headTurnWaitValue)

#returns false if there is no face
#returns true and moves the robot
def hasFace(img):
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    hasFace = False
    for (x,y,w,h) in faces:
        cv.rectangle(img,(x,y),(x+w,y+h),(255,0,0),3)
        hasFace = True
    cv.imshow('Image',img)
    return hasFace

cv.namedWindow("Image")
cap = cv.VideoCapture(0)

faceNotFound = True
faceHasBeenFound = False

#number of times to look
numberOfTurns = 5

timeWithoutFace = 0

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
width = 640
height = 480
camera.resolution = (width, height)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(width, height))

def getCapture():
    # capture frames from the camera
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        # grab the raw NumPy array representing the image, then initialize the timestamp
        # and occupied/unoccupied text
        img = frame.array
        break
    rawCapture.truncate(0)
    return img

middleX = (int)(width/2)
middleY = (int)(height/2)
#used to decide if turning is necessary
turnTolerance = 100
heightTolerance = 75

#start in the middle
posX = middleX
posY = middleY
preferredArea = 35000
areaTolerance = 10000

changeValue = 1000
turnWaitValue = 0.2
motorWaitValue = 0.2

#get the head in the right position
tango.setTarget(HEADTILT, headTilt)
tango.setTarget(HEADTURN, headTurn)

def turnRight(waitValue):
    global turn
    turn -= changeValue
    tango.setTarget(TURN, turn)
    print('turn right: turn = ' + str(waitValue))
    time.sleep(waitValue)
    turn += changeValue
    tango.setTarget(TURN, turn)
    time.sleep(waitValue)

def turnLeft(waitValue):
    global turn
    turn += changeValue
    tango.setTarget(TURN, turn)
    print('turn left: turn = ' + str(waitValue))
    time.sleep(waitValue)
    turn -= changeValue
    tango.setTarget(TURN, turn)
    time.sleep(waitValue)

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
    motors += changeValue
    tango.setTarget(MOTORS, motors)
    print('move backward: motors = ' + str(motors))
    time.sleep(waitValue)
    motors -= changeValue
    tango.setTarget(MOTORS, motors)
    print('stop ' + str(motors))
    time.sleep(waitValue)

def changeLookHeight(newPos):
    global headTilt
    headTilt = newPos
    tango.setTarget(HEADTILT, headTilt)
    print('look up: newPos = ' + str(newPos))
    time.sleep(0.2)

def changeLookDirection(newPos):
    global headTurn
    headTurn = newPos
    tango.setTarget(HEADTURN, headTurn)
    print('look up: newPos = ' + str(newPos))
    time.sleep(0.2)

def correctPosition(X, Y, area):
    #check if we need to turn
    #if we need to turn right
    if(X > middleX + turnTolerance):
        print("need to turn right")
        turnRight(turnWaitValue)
        #turn the head a little if needed
        if(headTurn>6000):
            changeLookDirection(headTurn-headTurnValue)
        elif(headTurn<6000):
            changeLookDirection(headTurn+headTurnValue)
        else:
            print("head is oriented correctly")

    #if we need to turn left
    elif(X < middleX - turnTolerance):
        print("need to turn left")
        turnLeft(turnWaitValue)
        #turn the head a little if needed
        if(headTurn>6000):
            changeLookDirection(headTurn-headTurnValue)
        elif(headTurn<6000):
            changeLookDirection(headTurn+headTurnValue)
        else:
            print("head is oriented correctly")
    else:
        print("no need to turn")

    #check if we need to look up or down
    #if we need to look up
    if(Y > middleY + heightTolerance):
        print("need to look down")
        changeLookHeight(headTilt-headTurnValue)
    #if we need to turn left
    elif(Y < middleY - heightTolerance):
        print("need to look up")
        changeLookHeight(headTilt+headTurnValue)
    else:
        print("no need to look up or down")

    #check if we need to move back or forward
    print("area = " + str(area))
    #check if we need to move forward
    if(area < preferredArea-areaTolerance):
        print("need to move forward")
        forward(motorWaitValue)
    elif(area > preferredArea+areaTolerance):
        print("need to move backward")
        backward(motorWaitValue)
    else:
        print("no need to move forward or backward")

while True:
    while(faceNotFound):
        #turn left and look for face repeatedly
        for i in range(0, numberOfTurns):
            lookLeft()
            #get the camera feed
            img = getCapture()
            #cv.imshow('Image',img)
            #check if there's a face
            if(hasFace(img)):
                faceNotFound = False
                faceHasBeenFound = True
                sayHello()
                break
            if cv.waitKey(1) & 0xFF == ord('q'):
                break
        #if a face hasn't been found by turning left
        if(faceNotFound):
            for i in range(0, numberOfTurns*2):
                lookRight()
                #get the camera feed
                img = getCapture()
                #cv.imshow('Image',img)
                #check if there's a face
                if(hasFace(img)):
                    faceNotFound = False
                    faceHasBeenFound = True
                    sayHello()
                    break
                if cv.waitKey(1) & 0xFF == ord('q'):
                    break
        #if a face hasn't been found by turning left or right
        if(faceNotFound):
            #sayWhereAreYou()
            print("Ugh where are you?")
            #this will get the robot back to the center
            for i in range(0, numberOfTurns):
                lookLeft()
                img = getCapture()
                #cv.imshow('Image',img)
                if(hasFace(img)):
                    faceNotFound = False
                    faceHasBeenFound = True
                    sayHello()
                    break
                if cv.waitKey(1) & 0xFF == ord('q'):
                    break
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    #now time to get into position
    while(faceHasBeenFound):
        #get the capture
        img = getCapture()
        #get the face
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        faceFound = False
        for (x,y,w,h) in faces:
            faceFound = True
            cv.rectangle(img,(x,y),(x+w,y+h),(255,0,0),3)
            posX = int(x+(w/2))
            posY = int(y+(h/2))
            faceArea = w*h
            #turn or go back or forth depending on face position
            correctPosition(posX, posY, faceArea)
        
        if(faceFound):
            timeWithoutFace = 0
        else:
            timeWithoutFace += 1
            if(timeWithoutFace>20):
                faceNotFound = True
                faceHasBeenFound = False
            print(timeWithoutFace)

        cv.imshow('Image',img)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    if cv.waitKey(1) & 0xFF == ord('q'):
        break
