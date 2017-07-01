#! /usr/bin/python

import CHIP_IO.GPIO as GPIO
import threading
import atexit
import time
import Adafruit_GPIO.I2C as I2C
import struct

class RotaryEncoder():

  def __init__(self, addresses, invert=False, factor=1):
    atexit.register(GPIO.cleanup)

    self.factor = factor
    if invert:
        self.factor *= -1

    self.encoders = {}
    for address in addresses:
      self.encoders[address] =  I2C.get_i2c_device(address, busnum=1)

    try:
        with open("/sys/class/gpio/unexport", "w") as unexport:
            unexport.write("205\n")
    except IOError:
        pass

    self.intr = "PWM1"
    GPIO.setup(self.intr, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

    self.residual = 0

    self.turn_cb = None
    self.press_cb = None

  def _call_callbacks(self, pin):
    for address, encoder in self.encoders.iteritems():
      pips = float(encoder.readS8(0))
      presses = encoder.readU8(1)

      pips *= self.factor
      pips += self.residual

      if abs(pips) < 1:
          self.residual = pips
          pips = 0
      else:
          self.residual = pips % 1
          pips -= self.residual

      if pips != 0 and self.turn_cb is not None:
        self.turn_cb(address, pips)

      if presses != 0 and self.press_cb is not None:
        self.press_cb(address, presses)

  def register_callbacks(self, turn=None, press=None):
    self.turn_cb = turn
    self.press_cb = press
    GPIO.add_event_detect(self.intr, GPIO.FALLING)
    GPIO.add_event_callback(self.intr, self._call_callbacks)

  def read_switches(self, pin=0):
    for address, encoder in self.encoders.iteritems():
      pips = encoder.readS8(0)
      presses = encoder.readU8(1)
      if self.turn_cb and pips:
          self.turn_cb(address, pips)
      if self.press_cb and presses:
          self.press_cb(address, presses)

      return (pips/2, presses/2)

def _press_cb(address, presses):
    print "Button %d pressed %d times" % (address, presses)

def _turn_cb(address, pips):
    print "Knob %d turned %d pips" % (address, pips)

if __name__ == '__main__':
  re = RotaryEncoder([0x11], invert=False, factor=0.5)
  re.register_callbacks(turn=_turn_cb, press=_press_cb)
  print re.read_switches()
  while True:
#    re.read_switches(0)
#    print "Intr: %d" % GPIO.input(re.intr) 
    time.sleep(1)
