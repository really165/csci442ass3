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
            
IP = '10.200.28.12'

#greets the human
def sayHello():
    #IP = '10.200.28.12'
    PORT = 5010
    client = ClientSocket(IP, PORT)
    ##client.start()

    for i in ["hello human", "How are you", "Sorry, you must die now"]:
        time.sleep(1)
        client.sendData(i)            
    print("Exiting Sends")

#greets the human
def sayWhereAreYou():
    #IP = '10.200.28.12'
    PORT = 5010
    client = ClientSocket(IP, PORT)
    ##client.start()

    for i in ["ugh where are you"]:
        time.sleep(1)
        client.sendData(i)            
    print("Exiting Sends")

#how much power is sent into the motors
changeValue = 100
#how long the head moves for
headTurnWaitValue = 0.5
#how long the robot waits before looking again
stabilizeWaitValue = 1

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

#looks left once and waits
def lookLeft():
    global headTurn
    headTurn += changeValue
    tango.setTarget(HEADTURN, headTurn)
    print("looking left")
    time.sleep(headTurnWaitValue)
    headTurn -= changeValue
    tango.setTarget(HEADTURN, headTurn)
    print("stabilizing")
    time.sleep(stabilizeWaitValue)
    
#looks right once and waits
def lookRight():
    global headTurn
    headTurn -= changeValue
    tango.setTarget(HEADTURN, headTurn)
    print("looking right")
    time.sleep(headTurnWaitValue)
    headTurn += changeValue
    tango.setTarget(HEADTURN, headTurn)
    print("stabilizing")
    time.sleep(stabilizeWaitValue)

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

def correctPosition():
    print("correct position")

cv.namedWindow("Image")
#cap = cv.VideoCapture(0)

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
                    break
                if cv.waitKey(1) & 0xFF == ord('q'):
                    break
        #if a face hasn't been found by turning left or right
        if(faceNotFound):
            sayWhereAreYou()
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
        
        if(faceFound):
            timeWithoutFace = 0
            correctPosition()
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