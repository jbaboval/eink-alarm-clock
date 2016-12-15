# Copyright 2016 John Baboval
#
# Originally based on Clock27.py by Pevasive Displays, Inc.
#
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

import sys
import os
import atexit
import glob
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from datetime import datetime
import time
from EPD_simulator import EPD
from RotaryEncoder import RotaryEncoder
from datetime import datetime
from pytz import timezone, country_timezones
import pytz
import GeoIP
import json
from urllib2 import urlopen

WHITE = 1
BLACK = 0

class Settings27(object):
    # fonts
    CLOCK_FONT_SIZE = 100
    DATE_FONT_SIZE  = 42

    # time
    X_OFFSET = 5
    Y_OFFSET = 3
    COLON_SIZE = 5
    COLON_GAP = 10

    # date
    DATE_X = 10
    DATE_Y = 95

class Settings20(object):
    # fonts
    CLOCK_FONT_SIZE = 60
    DATE_FONT_SIZE  = 30

    # time
    X_OFFSET = 25
    Y_OFFSET = 3
    COLON_SIZE = 3
    COLON_GAP = 5

    # date
    DATE_X = 10
    DATE_Y = 40

class AlarmClock():

    def __init__(self, epd, settings):

        self.epd = epd
        self.settings = settings
        self.menu_font = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'

        self.possible_fonts = [
            '/usr/share/fonts/truetype/fonts-georgewilliams/CaslonBold.ttf',
            '/usr/share/fonts/truetype/fonts-georgewilliams/CaslonItalic.ttf',
            '/usr/share/fonts/truetype/fonts-georgewilliams/GWMonospaceOblique.ttf',
            '/usr/share/fonts/truetype/fonts-georgewilliams/Caliban.ttf',
            '/usr/share/fonts/truetype/fonts-georgewilliams/GWMonospaceBold.ttf',
            '/usr/share/fonts/truetype/fonts-georgewilliams/CaslonRoman.ttf',
            '/usr/share/fonts/truetype/fonts-georgewilliams/Cupola.ttf',
            '/usr/share/fonts/truetype/fonts-georgewilliams/Caslon-Black.ttf',
            '/usr/share/fonts/truetype/fonts-georgewilliams/GWMonospace.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSerif.ttf',
            '/usr/share/fonts/truetype/freefont/FreeMono.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSerifBoldItalic.ttf',
            '/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf',
            '/usr/share/fonts/truetype/freefont/FreeMonoOblique.ttf',
            '/usr/share/fonts/truetype/freefont/FreeMonoBoldOblique.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf',
            '/usr/share/fonts/truetype/unifont/unifont.ttf',
            '/usr/share/fonts/truetype/unifont/unifont_upper.ttf',
            '/usr/share/fonts/truetype/humor-sans/Humor-Sans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/dustin/dustismo_bold.ttf',
            '/usr/share/fonts/truetype/dustin/Dustismo_Roman.ttf',
            '/usr/share/fonts/truetype/dustin/Winks.ttf',
            '/usr/share/fonts/truetype/dustin/dustismo_italic.ttf',
            '/usr/share/fonts/truetype/dustin/Balker.ttf',
            '/usr/share/fonts/truetype/dustin/Dustismo_Roman_Italic_Bold.ttf',
            '/usr/share/fonts/truetype/dustin/Domestic_Manners.ttf',
            '/usr/share/fonts/truetype/dustin/dustismo_bold_italic.ttf',
            '/usr/share/fonts/truetype/dustin/Junkyard.ttf',
            '/usr/share/fonts/truetype/dustin/Dustismo.ttf',
            '/usr/share/fonts/truetype/dustin/Wargames.ttf',
            '/usr/share/fonts/truetype/dustin/PenguinAttack.ttf',
            '/usr/share/fonts/truetype/dustin/It_wasn_t_me.ttf',
            '/usr/share/fonts/truetype/dustin/El_Abogado_Loco.ttf',
            '/usr/share/fonts/truetype/dustin/Dustismo_Roman_Italic.ttf',
            '/usr/share/fonts/truetype/dustin/Dustismo_Roman_Bold.ttf'
        ]

        self.font_index = 10

        self.state = "OK"
        self.timezones = country_timezones('US')
        self.timezone_index = 0
 
        try:
            ip = json.load(urlopen('http://jsonip.com'))['ip']
        except Exception:
            try:
                ip = json.load(urlopen('https://api.ipify.org/?format=json'))['ip']
            except Exception:
                self.state = "NetworkError"

        g = GeoIP.open("/usr/share/GeoIP/GeoIPCity.dat", GeoIP.GEOIP_STANDARD)
        try: 
            gr = g.record_by_addr(ip)
            print gr
            self.latitude = gr['latitude']
            self.longitude = gr['longitude']
            while self.timezones[self.timezone_index] != gr['time_zone']:
                self.timezone_index += 1
        except Exception:
            raise

        self.twentyfour = True

    def _calculate_fontsize(self, fontpath, str, size):

        image = Image.new('1', self.epd.size, WHITE)
        draw = ImageDraw.Draw(image)
        difference = size

        while True:
            font = ImageFont.truetype(fontpath, size)
            w, h = draw.textsize(str, font=font)
            difference = int(difference / 2)
            miss = self.epd.size[0] - w - 5
            print "Width: %d, Miss: %d, Difference: %d" % (w, miss, difference)
            if difference <= 0:
                if miss < 0:
                    difference = 1
                else:
                    break

            if (miss > 0) and (miss < 10):
                break

            if miss < 10:
                size -= difference
            else:
                size += difference

        return font

    def _update_timezone(self):
        self.timezone = timezone(self.timezones[self.timezone_index])

    def _update_fonts(self):
        self.font_index = self.font_index % len(self.possible_fonts)
        font = self.possible_fonts[self.font_index]
        print "Changing font to " + font
        if self.twentyfour:
            string = "23:59"
        else:
            string = "12:00 PM"
        self.clock_font = self._calculate_fontsize(font, string, self.settings.CLOCK_FONT_SIZE)
        string = "Wednesday September 29th"
        self.date_font = self._calculate_fontsize(font, string, self.settings.DATE_FONT_SIZE)

    def run(self):
        re = RotaryEncoder()

        utc = timezone('UTC')

        # initially set all white background
        image = Image.new('1', self.epd.size, WHITE)

        # prepare for drawing
        draw = ImageDraw.Draw(image)
        width, height = image.size

        # initial time
        now = utc.localize(datetime.today())
        full_update = True

        self._update_fonts()
        self._update_timezone()

        while True:
            now = now.astimezone(self.timezone)
            # clear the display buffer
            draw.rectangle((0, 0, width, height), fill=WHITE, outline=WHITE)

            # border
            draw.rectangle((1, 1, width - 1, height - 1), fill=WHITE, outline=BLACK)
            draw.rectangle((2, 2, width - 2, height - 2), fill=WHITE, outline=BLACK)

            # date
            daystr = '{dt:%A}, {dt:%B} {dt.day}'.format(dt=now)
            w, h = draw.textsize(daystr, font=self.date_font)
            draw.text(((width - w)/2, self.settings.DATE_Y), daystr, fill=BLACK, font=self.date_font)

            if self.twentyfour:
                timefmt = "%-H:%M"
            else:
                timefmt = "%-I:%M %p"

            timestr = now.strftime(timefmt)
            w, h = draw.textsize(timestr, font=self.clock_font)
            y = self.settings.Y_OFFSET + ((self.settings.DATE_Y - self.settings.Y_OFFSET - h) / 2)
            draw.text(((width - w)/2, y), timestr, fill=BLACK, font=self.clock_font)

            # display image on the panel
            self.epd.display(image)
            if not full_update:
                self.epd.partial_update()
            else:
                full_update = False
                self.epd.update()

            if (now.minute % 5) == 0:
                self.epd.blink()  

            # wait for next minute
            while True:
                now = utc.localize(datetime.today())
                if now.second == 0: # or now.second == 30:
                    break
                input = re.get()
                if input != 0:
                    self.font_index += input
                    self._update_fonts()

                    full_update = True
                    break
                time.sleep(0.1)

def main(argv):
    """main program - draw HH:MM clock on 2.70" size panel"""
    epd = EPD()

    time.sleep(0.1)

    print('panel = {p:s} {w:d} x {h:d}  version={v:s} COG={g:d} FILM={f:d}'.format(p=epd.panel, w=epd.width, h=epd.height, v=epd.version, g=epd.cog, f=epd.film))

    if 'EPD 2.7' == epd.panel:
        settings = Settings27()
    elif 'EPD 2.0' == epd.panel:
        settings = Settings20()
    else:
        print('incorrect panel size')
        sys.exit(1)

    epd.clear()
    clock = AlarmClock(epd, settings)
    clock.run()

# main
if "__main__" == __name__:
    if len(sys.argv) < 1:
        sys.exit('usage: {p:s}'.format(p=sys.argv[0]))

    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit('interrupted')
        pass
