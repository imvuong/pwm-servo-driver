#!/usr/bin/python


# For a 50Hz PWM frequency, each cycle is 20ms wide. 
# To make a pulse 1ms wide, you have it rise at 0 and fall at 205. 
# To make the pulse 2ms wide, you have it rise at 0 and fall at 410. 
# The neutral position would be halfway between the two, rising at 0 and falling at 307.

from Adafruit_PWM_Servo_Driver import PWM
import sys, termios, tty, os, time

import argparse
import math
from debounce import debounce

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

pwm_frequency = 50              # Set desired frequency (Hz)
pwm_single_pulse_ms = 20        # Set single pulse period (ms)
max_pulse_length = 4096         # Max pulse length (ms)
neutral_ms = 1.5                # Servo neutral pulse width (ms)
neutral = round(max_pulse_length / pwm_single_pulse_ms * neutral_ms)  # Neutral pulse length (ms)
clockwise_max_ms = 1.7          # Continuous servo clockwise rotation max pulse width (ms)
counter_clockwise_max_ms = 1.3  # Continuous servo counter clockwise rotation max pulse width (ms)
clockwise_pulse = round(max_pulse_length / pwm_single_pulse_ms * clockwise_max_ms)
counter_clockwise_pulse = round(max_pulse_length / pwm_single_pulse_ms * counter_clockwise_max_ms)

def stop():
    set_left_wheels(neutral)
    set_right_wheels(neutral)
    client.send_message("/robot/left", neutral_ms)
    client.send_message("/robot/right", neutral_ms)
    client.send_message("/robot/banner", "HALT!!!")

def forward():
    set_left_wheels(clockwise_pulse)
    set_right_wheels(counter_clockwise_pulse)
    client.send_message("/robot/left", clockwise_max_ms)
    client.send_message("/robot/right", counter_clockwise_max_ms)
    client.send_message("/robot/banner", "Full speed ahead!!!")

def backward():
    set_left_wheels(counter_clockwise_pulse)
    set_right_wheels(clockwise_pulse)
    client.send_message("/robot/left", counter_clockwise_max_ms)
    client.send_message("/robot/right", clockwise_max_ms)
    client.send_message("/robot/banner", "Watch out behind me!!!")

def turn_left():
    set_left_wheels(counter_clockwise_pulse)
    set_right_wheels(counter_clockwise_pulse)
    client.send_message("/robot/left", counter_clockwise_max_ms)
    client.send_message("/robot/right", counter_clockwise_max_ms)
    client.send_message("/robot/banner", "Making a left!!!")

def turn_right():
    set_left_wheels(clockwise_pulse)
    set_right_wheels(clockwise_pulse)
    client.send_message("/robot/left", clockwise_max_ms)
    client.send_message("/robot/right", clockwise_max_ms)
    client.send_message("/robot/banner", "Making a right!!!")

def set_left_wheels(pulse):
    pwm.setPWM(FL_WHEEL, 0, pulse)
    pwm.setPWM(BL_WHEEL, 0, pulse)
    
def set_right_wheels(pulse):
    pwm.setPWM(FR_WHEEL, 0, pulse)
    pwm.setPWM(BR_WHEEL, 0, pulse)

def ping_handler(unused_addr, args):
    print("[{0}]".format(args[0]))

@debounce(0.1)
def left_handler(unused_addr, args, value):
    print("[{0}] ~ {1}".format(args[0], value))
    pulse = round(max_pulse_length / pwm_single_pulse_ms * value)
    set_left_wheels(pulse)
    client.send_message("/robot/banner", " ")

@debounce(0.1)
def right_handler(unused_addr, args, value):
    print("[{0}] ~ {1}".format(args[0], value))
    pulse = round(max_pulse_length / pwm_single_pulse_ms * value)
    set_right_wheels(pulse)
    client.send_message("/robot/banner", " ")

def push_button_handler(unused_addr, args, value):
    print("[{0}] ~ {1}".format(args[0], value))
    if (args[0] == "stop"):
        stop()
    elif (args[0] == "turn_left"):
        turn_left()
    elif (args[0] == "turn_right"):
        turn_right()
    elif (args[0] == "forward"):
        forward()
    elif (args[0] == "backward"):
        backward()


pwm.setPWMFreq(pwm_frequency)

parser = argparse.ArgumentParser()
parser.add_argument("--server", default="192.168.1.17", help="The server ip to listen on")
parser.add_argument("--client", default="192.168.1.15", help="The remote control client ip to send to")
parser.add_argument("--server-port", type=int, default=5005, help="The server port to listen on")
parser.add_argument("--client-port", type=int, default=5006, help="The client port to send to")
args = parser.parse_args()

dispatcher = dispatcher.Dispatcher()
dispatcher.map("/ping", ping_handler, "ping")
dispatcher.map("/robot/left", left_handler, "left")
dispatcher.map("/robot/right", right_handler, "right")
dispatcher.map("/robot/stop", push_button_handler, "stop")
dispatcher.map("/robot/forward", push_button_handler, "forward")
dispatcher.map("/robot/backward", push_button_handler, "backward")
dispatcher.map("/robot/turn_left", push_button_handler, "turn_left")
dispatcher.map("/robot/turn_right", push_button_handler, "turn_right")

server = osc_server.ThreadingOSCUDPServer((args.server, args.server_port), dispatcher)
client = udp_client.SimpleUDPClient(args.client, args.client_port)

# Set to stop
stop()

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
