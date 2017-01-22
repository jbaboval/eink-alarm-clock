#!/usr/bin/python

# Based on example by hrvoje at:
# https://www.raspberrypi.org/forums/viewtopic.php?f=37&t=140250

import CHIP_IO.GPIO as GPIO
import threading
import atexit

class RotaryEncoder():

    def __init__(self):
        atexit.register(GPIO.cleanup)

        # FIXME
        try:
            with open("/sys/class/gpio/unexport", "w") as unexport:
                unexport.write("1015\n")
        except IOError:
            pass

        try:
            with open("/sys/class/gpio/unexport", "w") as unexport:
                unexport.write("1017\n")
        except IOError:
            pass

        try:
            with open("/sys/class/gpio/unexport", "w") as unexport:
                unexport.write("1019\n")
        except IOError:
            pass

        GPIO.setup("XIO-P4", GPIO.OUT)
        GPIO.output("XIO-P4", GPIO.LOW)

        self.Enc_A = "XIO-P2"   # Encoder input A
        self.Enc_B = "XIO-P6"   # Encoder input B

        self.counter = 0   # Start counting from 0
        self.A = 1         # Assume that rotary switch is not 
        self.B = 1         # moving while we init software

        self.lock = threading.Lock()      # create lock for rotary switch

        GPIO.setup(self.Enc_A, GPIO.IN)             
        GPIO.setup(self.Enc_B, GPIO.IN)

        # setup interrupts for the A and B pins
        GPIO.add_event_detect(self.Enc_A, GPIO.RISING, callback=self.rotary_interrupt)
        GPIO.add_event_detect(self.Enc_B, GPIO.RISING, callback=self.rotary_interrupt)
        return

    # Rotary encoder interrupt:
    # this one is called for both inputs from rotary switch (A and B)
    def rotary_interrupt(self, A_or_B):

        # read both of the switches
        Switch_A = GPIO.input(self.Enc_A)
        Switch_B = GPIO.input(self.Enc_B)

        # check if state of A or B has changed
        # if not that means that bouncing caused the interrupt
        if self.A == Switch_A and self.B == Switch_B:
            return

        self.A = Switch_A
        self.B = Switch_B

        if (Switch_A and Switch_B): # Both high? Yes -> end of sequence
            self.lock.acquire()
            if A_or_B == self.Enc_B:     # Turning direction depends on 
                self.counter += 1 # which input gave last interrupt
            else:
                self.counter -= 1
            self.lock.release()
        return

    def get(self):
        self.lock.acquire()
        state = self.counter
        self.counter = 0
        self.lock.release()
        return state
