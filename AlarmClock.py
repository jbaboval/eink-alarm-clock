# -*- coding: utf-8 -*-
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
import pickle
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from datetime import datetime
import time
#from EPD_simulator import EPD
from EPD import EPD
from RotaryEncoder import RotaryEncoder
from pytz import timezone, country_timezones
import pytz
import GeoIP
import json
from urllib2 import urlopen
import forecastio
from forecastio.models import Forecast

WHITE = 1
BLACK = 0

class AlarmClock():

    weather_icons = {
        'clear-day': unichr(0xf00d),
        'clear-night': unichr(0xf02e),
        'rain': unichr(0xf019),
        'snow': unichr(0xf076),
        'sleet': unichr(0xf0b5),
        'wind': unichr(0xf050),
        'fog': unichr(0xf014),
        'cloudy': unichr(0xf013),
        'partly-cloudy-day': unichr(0xf002),
        'partly-cloudy-night': unichr(0xf086),
        'hail': unichr(0xf015),
        'thunderstorm': unichr(0xf01d),
        'tornado': unichr(0xf056) 
    }

    def __init__(self, epd):

        self.epd = epd
        self.menu_font = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'

        self.possible_fonts = [
            '/usr/share/fonts/truetype/fonts-georgewilliams/CaslonBold.ttf',
            '/usr/share/fonts/truetype/fonts-georgewilliams/Caliban.ttf',
            '/usr/share/fonts/truetype/fonts-georgewilliams/Cupola.ttf',
            '/usr/share/fonts/truetype/fonts-georgewilliams/Caslon-Black.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSerif.ttf',
            '/usr/share/fonts/truetype/freefont/FreeMono.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf',
            '/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf',
            '/usr/share/fonts/truetype/freefont/FreeMonoOblique.ttf',
            '/usr/share/fonts/truetype/freefont/FreeMonoBoldOblique.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
            '/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf',
            '/usr/share/fonts/truetype/unifont/unifont.ttf',
            '/usr/share/fonts/truetype/humor-sans/Humor-Sans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/dustin/dustismo_bold.ttf',
            '/usr/share/fonts/truetype/dustin/Dustismo_Roman.ttf',
            '/usr/share/fonts/truetype/dustin/dustismo_italic.ttf',
            '/usr/share/fonts/truetype/dustin/Domestic_Manners.ttf',
            '/usr/share/fonts/truetype/dustin/Junkyard.ttf',
            '/usr/share/fonts/truetype/dustin/Dustismo.ttf',
            '/usr/share/fonts/truetype/dustin/Wargames.ttf',
            '/usr/share/fonts/truetype/dustin/PenguinAttack.ttf',
            '/usr/share/fonts/truetype/dustin/It_wasn_t_me.ttf',
            '/usr/share/fonts/truetype/dustin/Dustismo_Roman_Italic.ttf',
            '/usr/share/fonts/truetype/dustin/Dustismo_Roman_Bold.ttf'
        ]

        self.font_index = 27

        self.mode = "weather"
        self.timezones = country_timezones('US')
        self.timezone_index = 0
 
        self.re = RotaryEncoder()

        try:
            ip = json.load(urlopen('http://jsonip.com'))['ip']
        except Exception:
            try:
                ip = json.load(urlopen('https://api.ipify.org/?format=json'))['ip']
            except Exception:
                raise

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

        try:
            with open('/root/alarmclock-settings.pickle', 'rb') as settings:
                self.settings = pickle.load(settings)
        except Exception as e:
            print "Failed to load settings; using defaults"
            print e
            self.settings = {}
            self.settings['twentyfour'] = False
            self.settings['alarm'] = False

        try:
            with open('/root/darksky.key', 'r') as f:
                self.darksky_key = f.readline().strip()
                self.weather = True
        except Exception as e:
                print "Couldn't get key from /root/darksky.key: " + str(e)
                self.weather = False

        if self.weather:
            self._update_weather()

    def _set_setting(self, setting, value):
        self.settings[setting] = value
        with open('/root/alarmclock-settings.pickle', 'wb') as settings:
            pickle.dump(self.settings, settings)

    def _update_weather(self):
        try:
            with open('/root/weather-cache.pickle', 'rb') as wf:
                saved_weather = pickle.load(wf)
                self.forecast_time = saved_weather['then']
                response = saved_weather['forecast']
                self.forecast = Forecast(response.json(), response, response.headers)
                print "Loaded weather data from cache"
        except Exception as e:
            print "No cached weather data, or failed to load cache"
            print e
            self.forecast_time = datetime(1980, 1, 1)

        if self.weather:
            since = datetime.now() - self.forecast_time
            if since.total_seconds() >= (60*60):
                print "Weather cache is %d seconds old; fetching new data" % since.total_seconds()
                try:
                    self.forecast = forecastio.load_forecast(self.darksky_key, self.latitude, self.longitude)
                except Exception as e:
                    print "Failed to load forecast data"
                    print e
                    return

                self.forecast_time = datetime.now()
                with open('/root/weather-cache.pickle', 'wb') as wf:
                    pickle.dump({'then': self.forecast_time, 'forecast': self.forecast.response}, wf)
        #else:
            # Weather is disabled

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
#        if self.settings['twentyfour']:
#            string = "23:59"
#        else:
        string = "12:22 PM"
        self.clock_font = self._calculate_fontsize(font, string, 100)
        string = "Wednesday September 29th"
        self.date_font = self._calculate_fontsize(font, string, 42)
        self.icon_font = ImageFont.truetype('/usr/share/fonts/truetype/WeatherIcons/weathericons-regular-webfont.ttf', 46)
        self.weather_font = ImageFont.truetype(font, 42)
        self.menu_font = ImageFont.truetype(font, 38)

    def change_font(self, count):
        self.font_index += count
        self._update_fonts()
        return True

    def main_button(self, button):
        self.mode = 'menu'
        self.menuItem = 'alarm'
        return False

    menu = {
        # Main menu
        'settings':  { 'text':         "Settings",
                       'subArrow':     True,
                       'buttonAction': 'goto',
                       'buttonParam':  'setting-24h',
                       'next':         'alarm',
                       'prev':         'exit'
                     },
        'alarm':     { 'text':         "Alarm",
                       'subArrow':     False,
                       'buttonAction': 'toggle',
                       'buttonParam':  'alarm',
                       'next':         'set-alarm',
                       'prev':         'settings'
                     },
        'set-alarm': { 'text':         "Set Alarm",
                       'subArrow':     True,
                       'buttonAction': 'mode',
                       'buttonParam':  'set',
                       'next':         'exit',
                       'prev':         'alarm'
                     },
        'exit':      { 'text':         "Exit",
                       'subArrow':     False,
                       'buttonAction': 'mode',
                       'buttonParam':  'weather',
                       'next':         'settings',
                       'prev':         'set-alarm'
                     },

        # Settings menu
        'setting-24h': { 'text':         "24 Hour",
                         'subArrow':     False,
                         'buttonAction': 'toggle',
                         'buttonParam':  'twentyfour',
                         'next':         'setting-alarm-tone',
                         'prev':         'setting-exit'
                       },
        'setting-alarm-tone':
                       { 'text':         "Ringtone",
                         'subArrow':     True,
                         'buttonAction': 'mode',
                         'buttonParam':  'tone',
                         'next':         'setting-exit',
                         'prev':         'setting-24h'
                       },
        'setting-exit':      { 'text':         "Exit",
                       'subArrow':     False,
                       'buttonAction': 'mode',
                       'buttonParam':  'weather',
                       'next':         'setting-24h',
                       'prev':         'setting-alarm-tone'
                     }
    }


    def draw_menu(self, draw, width, height, time_date_bottom):

        avail = height - time_date_bottom - 2

        menustr = "> " + AlarmClock.menu[self.menuItem]['text']
        w, h = draw.textsize(menustr, font=self.menu_font)
        
        vspace = (avail - h) / 2
        y = time_date_bottom + vspace
        x = 8

        draw.text((x, y), menustr, fill=BLACK, font=self.menu_font)

        x += w

        if AlarmClock.menu[self.menuItem]['subArrow']:
            arrowstr = unichr(0xf04d)
            draw.text((x, y - 8), arrowstr, fill=BLACK, font=self.icon_font)
        elif AlarmClock.menu[self.menuItem]['buttonAction'] == 'toggle':
            param = AlarmClock.menu[self.menuItem]['buttonParam']
            checktxt = " - " + ("ON" if self.settings[param] else "OFF")
            draw.text((x, y), checktxt, fill=BLACK, font=self.menu_font)

        try:
            now = time.time()
            if now - self.lastMenuAction > 30:
                self.mode = 'weather'
        except:
            self.lastMenuAction = time.time()

        return False

    def menu_turn(self, count):

        self.lastMenuAction = time.time()

        while (count > 0):
            self.menuItem = AlarmClock.menu[self.menuItem]['next']
            count -= 1

        while (count < 0):
            self.menuItem = AlarmClock.menu[self.menuItem]['prev']
            count += 1

        return False

    def menu_button(self, button):

        self.lastMenuAction = time.time()

        entry = AlarmClock.menu[self.menuItem]
        action = entry['buttonAction']
        param = entry['buttonParam']

        if action == 'toggle':
            self._set_setting(param, not self.settings[param])
        elif action == 'mode':
            self.mode = param
            return True
        elif action == 'goto':
            self.menuItem = param

        return False

    def draw_set(self, draw, width, height, time_date_bottom):
        return

    def set_turn(self, count):
        return

    def set_press(self, button):
        return

    def draw_weather(self, draw, width, height, time_date_bottom):

            # The moon phase font represents the phase as a unicode glyph between f0d0 and f0eb
            # with the new moon at the end
            #
            # The DarkSky API represents the new moon as 0, the full moon as 0.5, and the rest
            # as a decimal fraction.
            #
            # To render the correct glpyh, first convert the fraction into an index between 0-28,
            # Subtract 1, and treat negative as a new moon...
            moonPhase = self.forecast.daily().data[0].moonPhase
            moonPhase *= 28.0
            moonPhase = int(round(moonPhase)) - 1
            if moonPhase < 0:
                moonPhase = 27
            moonstr = unichr(moonPhase + 0xf0d0)
 
            # weather
            avail = height - 2 - time_date_bottom

            iconstr = AlarmClock.weather_icons[self.forecast.hourly().icon]
            iw, ih = draw.textsize(iconstr, font=self.icon_font)
 
            tempstr = u"%d\u00B0" % (self.forecast.currently().apparentTemperature) #, self.forecast.daily().data[0].apparentTemperatureMin, self.forecast.daily().data[0].apparentTemperatureMax)
            tw, th = draw.textsize(tempstr, font=self.weather_font)

            lowstr = u"Low:%d\u00B0" % self.forecast.daily().data[0].apparentTemperatureMin
            lw, lh = draw.textsize(lowstr, font=self.date_font)
            highstr = u"High:%d\u00B0" % self.forecast.daily().data[0].apparentTemperatureMax
            hw, hh = draw.textsize(highstr, font=self.date_font)
            mw, mh = draw.textsize(moonstr, font=self.icon_font)

            hlw = max(hw, lw)
            line_width = iw + tw + mw + max(hw, lw)
            horiz_space = (width - 4 - line_width) / 5

            x = horiz_space + 2
            y = time_date_bottom + ((avail - ih) / 2)
            draw.text((x, y), iconstr, fill=BLACK, font=self.icon_font)
            x += iw + horiz_space
            y = time_date_bottom + ((avail - th) / 2)
            draw.text((x, y), tempstr, fill=BLACK, font=self.weather_font)
            x += tw + horiz_space
            hlvspace = (avail - hh - lh) / 2
            y = time_date_bottom + hlvspace
            draw.text((x, y), highstr, fill=BLACK, font=self.date_font)
            y += hh
            draw.text((x, y), lowstr, fill=BLACK, font=self.date_font)
            x += hlw + horiz_space
            y = time_date_bottom + ((avail - mh) / 2)
            draw.text((x, y), moonstr, fill=BLACK, font=self.icon_font)

    def run(self):
        utc = timezone('UTC')

        blinked = False
        timeUpdate = True

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

            if self.settings['twentyfour']:
                timefmt = "%-H:%M"
            else:
                timefmt = "%-I:%M %p"

            # Time & Date get 2/3rds of the display...
            daystr = '{dt:%A}, {dt:%B} {dt.day}'.format(dt=now)
            dw, dh = draw.textsize(daystr, font=self.date_font)
            timestr = now.strftime(timefmt)
            tw, th = draw.textsize(timestr, font=self.clock_font)
            avail = int((height - 4) * 0.60)
            space = (avail - dh - th) / 2
            time_date_bottom = avail + 2

            y = space + 2
            draw.text(((width - tw)/2, y), timestr, fill=BLACK, font=self.clock_font)

            y += th
            y += space
            draw.text(((width - dw)/2, y), daystr, fill=BLACK, font=self.date_font)

            try:
                AlarmClock.modes[self.mode]['render_bottom'](self, draw, width, height, time_date_bottom)
            except Exception as e:
                print e
                pass

            # display image on the panel
            self.epd.display(image)
            if not full_update:
                self.epd.partial_update()
            else:
                full_update = False
                self.epd.update()

            if (now.minute % 5) == 0:
                if blinked == False:
                    blinked = True
                    self.epd.blink()
                    self._update_weather()
            else:
                blinked = True

            # wait for next minute
            i = 0
            while True:
                if (i % 100) == 0: # Only call today() once every 100 loops
                    now = utc.localize(datetime.today())
                    if now.second == 0:
                        if timeUpdate: # Only update the time once per minute
                            timeUpdate = False
                            break
                    else:
                        timeUpdate = True

                i += 1

                input = self.re.get()
                if input != 0:
                    full_update = AlarmClock.modes[self.mode]['knob'](self, input)
                    break
                button = self.re.get_button()
                if button != 0:
                    full_update = AlarmClock.modes[self.mode]['button'](self, button)
                    break
                time.sleep(0.01)

    modes = {
        'weather': { 'render_bottom': draw_weather,
                     'knob':          change_font,
                     'button':        main_button },
        'menu': {    'render_bottom': draw_menu,
                     'knob':          menu_turn,
                     'button':        menu_button },
        'set':  {    'render_bottom': draw_set,
                     'knob':          set_turn,
                     'button':        set_press }
    }


def main(argv):
    """main program - draw HH:MM clock on 2.70" size panel"""
    epd = EPD()

    print('panel = {p:s} {w:d} x {h:d}  version={v:s} COG={g:d} FILM={f:d}'.format(p=epd.panel, w=epd.width, h=epd.height, v=epd.version, g=epd.cog, f=epd.film))

    clock = AlarmClock(epd)
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
