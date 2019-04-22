import tkinter as tk
import maestro
import time

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

changeValue = 800
waitValue = 1

def forward():
    global motors
    motors += changeValue
    tango.setTarget(MOTORS, motors)
    print('move forward: motors = ' + str(motors))
    time.sleep(waitValue)
    motors -= changeValue
    tango.setTarget(MOTORS, motors)
    print('stop ' + str(motors))
    time.sleep(waitValue)

def backward():
    global motors
    motors -= changeValue
    tango.setTarget(MOTORS, motors)
    print('move backward: motors = ' + str(motors))
    time.sleep(waitValue)
    motors += changeValue
    tango.setTarget(MOTORS, motors)
    print('stop ' + str(motors))
    time.sleep(waitValue)

def turnLeft():
    global turn
    turn -= changeValue
    tango.setTarget(TURN, turn)
    print('turn left: turn = ' + str(turn))
    time.sleep(waitValue)
    turn += changeValue
    tango.setTarget(TURN, turn)
    print('stop ' + str(turn))
    time.sleep(waitValue)

def turnRight():
    global turn
    turn += changeValue
    tango.setTarget(TURN, turn)
    print('turn right: turn = ' + str(turn))
    time.sleep(waitValue)
    turn -= changeValue
    tango.setTarget(TURN, turn)
    print('stop ' + str(turn))
    time.sleep(waitValue)

forward()
backward()
turnLeft()
turnRight()
