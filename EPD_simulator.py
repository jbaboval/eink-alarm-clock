# Copyright 2016      Spineless Industries
# Copyright 2013-2015 Pervasive Displays, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

from Tkinter import Tk, Canvas, NW
from PIL import Image, ImageTk
from PIL import ImageOps
import re
import os
import time

class EPDError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class EPD(object):

    """EPD E-Ink interface

to use:
  from EPD import EPD

  epd = EPD([path='/path/to/epd'], [auto=boolean])

  image = Image.new('1', epd.size, 0)
  # draw on image
  epd.clear()         # clear the panel
  epd.display(image)  # tranfer image data
  epd.update()        # refresh the panel image - not deeed if auto=true
"""

    def __init__(self, *args, **kwargs):
        self._width = 264
        self._height = 176
        self._panel = 'EPD 2.7'
        self._cog = 0
        self._film = 0
        self._auto = False

        self._version = '4'

        if ('auto' in kwargs) and kwargs['auto']:
            self._auto = True

        self.root = Tk()
        self.canvas = Canvas(self.root, width=self._width, height=self._height)
        self.canvas.pack()

    @property
    def size(self):
        return (self._width, self._height)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def panel(self):
        return self._panel

    @property
    def version(self):
        return self._version

    @property
    def cog(self):
        return self._cog

    @property
    def film(self):
        return self._film

    @property
    def auto(self):
        return self._auto

    @auto.setter
    def auto(self, flag):
        if flag:
            self._auto = True
        else:
            self._auto = False


    def display(self, image):

        # attempt grayscale conversion, and then to single bit.
        # better to do this before calling this if the image is to
        # be displayed several times
        if image.mode != "1":
            image = ImageOps.grayscale(image).convert("1", dither=Image.FLOYDSTEINBERG)

        if image.mode != "1":
            raise EPDError('only single bit images are supported')

        if image.size != self.size:
            raise EPDError('image size mismatch')
        image = image.convert('L')
        image = ImageOps.invert(image)
        image = image.convert('1')
        try:
            self.oldimage = self.image
        except Exception:
            self.oldimage = image
        self.image = image

        if self.auto:
            self.update()

    def _invert(self, image):
        image = image.convert('L')
        image = ImageOps.invert(image)
        image = image.convert('1')
        self.timage = ImageTk.BitmapImage(image)
        self.imagesprite = self.canvas.create_image(0, 0, anchor=NW, image=self.timage)
        self.root.update()
        time.sleep(0.250)

    def _fill(self, color):
        self.timage = ImageTk.BitmapImage(Image.new("1", (self._width, self._height), color))
        self.imagesprite = self.canvas.create_image(0, 0, anchor=NW, image=self.timage)
        self.root.update()
        time.sleep(0.250)

    def _paint(self):
        self.timage = ImageTk.BitmapImage(self.image)
        self.imagesprite = self.canvas.create_image(0, 0, anchor=NW, image=self.timage)
        self.root.update()

    def update(self):
        self._invert(self.oldimage)
        self._fill(1)
        self._fill(0)
        self._invert(self.image)
        self._paint()

    def partial_update(self):
        self._paint()

    def blink(self):
        self._invert(self.image)
        self._paint()        

    def clear(self):
        self._fill(0)

