#!/usr/bin/python


# For a 50Hz PWM frequency, each cycle is 20ms wide. 
# To make a pulse 1ms wide, you have it rise at 0 and fall at 205. 
# To make the pulse 2ms wide, you have it rise at 0 and fall at 410. 
# The neutral position would be halfway between the two, rising at 0 and falling at 307.

from Adafruit_PWM_Servo_Driver import PWM
import sys, termios, tty, os, time

import argparse
import math

from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import osc_message_builder
from pythonosc import udp_client

FL_WHEEL = 0
FR_WHEEL = 4
BL_WHEEL = 8
BR_WHEEL = 12


# Initialise the PWM device using the default address
pwm = PWM(0x40)
# Note if you'd like more debug output you can instead run:
#pwm = PWM(0x40, debug=True)

servoMin = 150  # Min pulse length out of 4096
servoMax = 600  # Max pulse length out of 4096

neutral = 307
neutral_ms = 1.5


def stop():
    pwm.setPWM(FL_WHEEL, 0, neutral)
    pwm.setPWM(BL_WHEEL, 0, neutral)
    pwm.setPWM(FR_WHEEL, 0, neutral)
    pwm.setPWM(BR_WHEEL, 0, neutral)

def forward():
    pwm.setPWM(FL_WHEEL, 0, 410)
    pwm.setPWM(BL_WHEEL, 0, 410)
    pwm.setPWM(FR_WHEEL, 0, 205)
    pwm.setPWM(BR_WHEEL, 0, 205)

def backward():
    pwm.setPWM(FL_WHEEL, 0, 205)
    pwm.setPWM(BL_WHEEL, 0, 205)
    pwm.setPWM(FR_WHEEL, 0, 410)
    pwm.setPWM(BR_WHEEL, 0, 410)

def turn_left():
    pwm.setPWM(FL_WHEEL, 0, 205)
    pwm.setPWM(BL_WHEEL, 0, 205)
    pwm.setPWM(FR_WHEEL, 0, 205)
    pwm.setPWM(BR_WHEEL, 0, 205)

def turn_right():
    pwm.setPWM(FL_WHEEL, 0, 410)
    pwm.setPWM(BL_WHEEL, 0, 410)
    pwm.setPWM(FR_WHEEL, 0, 410)
    pwm.setPWM(BR_WHEEL, 0, 410)


def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def ping_handler(unused_addr, args):
    print("[{0}]".format(args[0]))

def left_handler(unused_addr, args, value):
    print("[{0}] ~ {1}".format(args[0], value))

def right_handler(unused_addr, args, value):
    print("[{0}] ~ {1}".format(args[0], value))

def stop_handler(unused_addr, args, value):
    print("[{0}] ~ {1}".format(args[0], value))
    client.send_message("/robot/left", neutral_ms)
    client.send_message("/robot/right", neutral_ms)


pwm.setPWMFreq(50)                        # Set frequency to 60 Hz

# Set to stop
stop()

parser = argparse.ArgumentParser()
parser.add_argument("--server", default="192.168.1.17", help="The server ip to listen on")
parser.add_argument("--client", default="192.168.1.15", help="The remote control client ip to send to")
parser.add_argument("--server-port", type=int, default=5005, help="The server port to listen on")
parser.add_argument("--client-port", type=int, default=5006, help="The client port to send to")
args = parser.parse_args()

dispatcher = dispatcher.Dispatcher()
dispatcher.map("/ping", ping_handler, "Ping")
dispatcher.map("/robot/left", left_handler, "Left")
dispatcher.map("/robot/right", right_handler, "Right")
dispatcher.map("/robot/stop", stop_handler, "Stop")

server = osc_server.ThreadingOSCUDPServer((args.server, args.server_port), dispatcher)
client = udp_client.SimpleUDPClient(args.client, args.client_port)
print("Serving on {}".format(server.server_address))
server.serve_forever()

# button_delay = 0.2
# while True:
#     char = getch()

#     if (char == "x"):
#         print("Exit!")
#         exit(0)

#     if (char == "s"):
#         print("Stop")
#         stop()
#         time.sleep(button_delay)

#     elif (char == "f"):
#         print("Forward")
#         forward()
#         time.sleep(button_delay)

#     elif (char == "b"):
#         print("Backward")
#         backward()
#         time.sleep(button_delay)

#     elif (char == "l"):
#         print("Turn Left")
#         turn_left()
#         time.sleep(button_delay)

#     elif (char == "r"):
#         print("Turn Right")
#         turn_right()
#         time.sleep(button_delay)

# while (True):
    # Change speed of continuous servo on channel O
    # pwm.setPWM(0, 0, servoMin)
    # time.sleep(1)
    # pwm.setPWM(0, 0, servoMax)
    # time.sleep(1)

    # pwm.setPWM(4, 0, servoMin)
    # time.sleep(1)
    # pwm.setPWM(4, 0, servoMax)
    # time.sleep(1)

    # pwm.setPWM(8, 0, servoMin)
    # time.sleep(1)
    # pwm.setPWM(8, 0, servoMax)
    # time.sleep(1)

    # pwm.setPWM(12, 0, servoMin)
    # time.sleep(1)
    # pwm.setPWM(12, 0, servoMax)
    # time.sleep(1)
