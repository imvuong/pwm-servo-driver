#!/usr/bin/python


# For a 50Hz PWM frequency, each cycle is 20ms wide.
# To make a pulse 1ms wide, you have it rise at 0 and fall at 205.
# To make the pulse 2ms wide, you have it rise at 0 and fall at 410.
# The neutral position would be halfway between the two, rising at 0 and falling at 307.

# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

import time
from threading import Thread

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

MODE_MANUAL = 0
MODE_AUTO = 1

# Software SPI configuration:
CLK  = 18
MISO = 23
MOSI = 24
CS   = 25
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)


# Initialise the PWM device using the default address
pwm = PWM(0x40)
# Note if you'd like more debug output you can instead run:
#pwm = PWM(0x40, debug=True)

robot_mode = MODE_MANUAL
pwm_frequency = 50              # Set desired frequency (Hz)
pwm_single_pulse_ms = 20        # Set single pulse period (ms)
max_pulse_length = 4096         # Max pulse length (ms)
neutral_ms = 1.5                # Servo neutral pulse width (ms)
neutral = round(max_pulse_length / pwm_single_pulse_ms * neutral_ms)  # Neutral pulse length (ms)
clockwise_max_ms = 1.7          # Continuous servo clockwise rotation max pulse width (ms)
counter_clockwise_max_ms = 1.3  # Continuous servo counter clockwise rotation max pulse width (ms)
clockwise_pulse = round(max_pulse_length / pwm_single_pulse_ms * clockwise_max_ms)
counter_clockwise_pulse = round(max_pulse_length / pwm_single_pulse_ms * counter_clockwise_max_ms)

danger_direction = [False] * 4
danger_label_name = ['back', 'right', 'front', 'left']

def stop():
    set_left_wheels(neutral)
    set_right_wheels(neutral)
    client.send_message("/robot/fader_left", neutral_ms)
    client.send_message("/robot/fader_right", neutral_ms)
    client.send_message("/robot/label_banner", "HALT!!!")

def forward():
    set_left_wheels(clockwise_pulse)
    set_right_wheels(counter_clockwise_pulse)
    client.send_message("/robot/fader_left", clockwise_max_ms)
    client.send_message("/robot/fader_right", counter_clockwise_max_ms)
    client.send_message("/robot/label_banner", "Full speed ahead!!!")

def backward():
    set_left_wheels(counter_clockwise_pulse)
    set_right_wheels(clockwise_pulse)
    client.send_message("/robot/fader_left", counter_clockwise_max_ms)
    client.send_message("/robot/fader_right", clockwise_max_ms)
    client.send_message("/robot/label_banner", "Watch out behind me!!!")

def turn_left():
    set_left_wheels(counter_clockwise_pulse)
    set_right_wheels(counter_clockwise_pulse)
    client.send_message("/robot/fader_left", counter_clockwise_max_ms)
    client.send_message("/robot/fader_right", counter_clockwise_max_ms)
    client.send_message("/robot/label_banner", "Making a left!!!")

def turn_right():
    set_left_wheels(clockwise_pulse)
    set_right_wheels(clockwise_pulse)
    client.send_message("/robot/fader_left", clockwise_max_ms)
    client.send_message("/robot/fader_right", clockwise_max_ms)
    client.send_message("/robot/label_banner", "Making a right!!!")

def set_left_wheels(pulse):
    pwm.setPWM(FL_WHEEL, 0, pulse)
    pwm.setPWM(BL_WHEEL, 0, pulse)

def set_right_wheels(pulse):
    pwm.setPWM(FR_WHEEL, 0, pulse)
    pwm.setPWM(BR_WHEEL, 0, pulse)

def ping_handler(unused_addr, args):
    print("[{0}]".format(args[0]))

def mode_change(mode):
    if (mode == MODE_MANUAL):
        client.send_message("/robot/label_mode", "Manual")
        client.send_message("/robot/label_banner", "Back to manual mode")
    else:
        client.send_message("/robot/label_mode", "Automatic")
        client.send_message("/robot/label_banner", "Look mom! I'm driving by myself!")


@debounce(0.1)
def fader_left_handler(unused_addr, args, value):
    print("[{0}] ~ {1}".format(args[0], value))
    pulse = round(max_pulse_length / pwm_single_pulse_ms * value)
    set_left_wheels(pulse)
    client.send_message("/robot/label_banner", " ")

@debounce(0.1)
def fader_right_handler(unused_addr, args, value):
    print("[{0}] ~ {1}".format(args[0], value))
    pulse = round(max_pulse_length / pwm_single_pulse_ms * value)
    set_right_wheels(pulse)
    client.send_message("/robot/label_banner", " ")

def push_button_handler(unused_addr, args, value):
    print("[{0}] ~ {1}".format(args[0], value))
    if (args[0] == "push_stop"):
        stop()
    elif (args[0] == "push_turn_left"):
        turn_left()
    elif (args[0] == "push_turn_right"):
        turn_right()
    elif (args[0] == "push_forward"):
        forward()
    elif (args[0] == "push_backward"):
        backward()
    elif (args[0] == "label_mode"):
        mode_change(value)

def read_ir_sensors():
    while True:
    # Read all the ADC channel values in a list.
        values = [0]*4
        IR_THRESHOLD = 1000
        for i in range(4):
            # The read_adc function will get the value of the specified channel (0-7).
            values[i] = mcp.read_adc(i)
            if (values[i] > IR_THRESHOLD):
                danger_direction[i] = True
                client.send_message("/robot/label_danger_" + danger_label_name[i], "Danger!!!")
            else:
                danger_direction[i] = False
                client.send_message("/robot/label_danger_" + danger_label_name[i], " ")

        # Print the ADC values.
        print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} |'.format(*values))
        # Pause for half a second.
        time.sleep(0.5)


pwm.setPWMFreq(pwm_frequency)

parser = argparse.ArgumentParser()
parser.add_argument("--server", default="192.168.1.17", help="The server ip to listen on")
parser.add_argument("--client", default="192.168.1.15", help="The remote control client ip to send to")
parser.add_argument("--server-port", type=int, default=5005, help="The server port to listen on")
parser.add_argument("--client-port", type=int, default=5006, help="The client port to send to")
args = parser.parse_args()

dispatcher = dispatcher.Dispatcher()
dispatcher.map("/ping", ping_handler, "ping")
dispatcher.map("/robot/fader_left", fader_left_handler, "fader_left")
dispatcher.map("/robot/fader_right", fader_right_handler, "fader_right")
dispatcher.map("/robot/push_stop", push_button_handler, "push_stop")
dispatcher.map("/robot/push_forward", push_button_handler, "push_forward")
dispatcher.map("/robot/backward", push_button_handler, "backward")
dispatcher.map("/robot/turn_left", push_button_handler, "turn_left")
dispatcher.map("/robot/turn_right", push_button_handler, "turn_right")
dispatcher.map("/robot/mode", push_button_handler, "mode")

server = osc_server.ThreadingOSCUDPServer((args.server, args.server_port), dispatcher)
client = udp_client.SimpleUDPClient(args.client, args.client_port)

# Set to servo motors to stop
stop()

# Start background thread to read IR sensors
background_thread = Thread(target=read_ir_sensors)
background_thread.start()

# Listen for TouchOSC messages
print("Serving on {}".format(server.server_address))
server.serve_forever()
