#!/usr/bin/make

.PHONY: all
all: build-libsoc build-gratis

deps:
	apt-get -y install build-essential python-dev python-pip flex bison vim autoconf libtool python-bitarray libb64-dev python-geoip geoip-database-contrib
	pip install spidev
	pip install pytz
	pip install python-forecastio

local-install: install-libsoc
	sed -i '/# ALARM_CLOCK START/,/# ALARM_CLOCK END/d' /etc/rc.local
	sed -i '/exit 0/i# ALARM_CLOCK START\n# Turn off the status LED\n/usr/sbin/i2cset -f -y 0 0x34 0x93 0x0\n# ALARM_CLOCK END\n' /etc/rc.local
	systemctl stop serial-getty@ttyS0.service
	systemctl disable serial-getty@ttyS0.service
	mkdir -p /usr/share/fonts/truetype/WeatherIcons/
	cp 'WeatherIcons/Font Files/WeatherIcons.ttf' /usr/share/fonts/truetype/WeatherIcons/
	cp weather-icons/font/weathericons-regular-webfont.ttf /usr/share/fonts/truetype/WeatherIcons/
	cp epdd.service /etc/systemd/system
	cp AlarmClock.service /etc/systemd/system
	systemctl enable epdd.service
	systemctl enable AlarmClock.service

libsoc/configure:
	cd libsoc && autoreconf -i

libsoc/Makefile:
	cd libsoc && ./configure --enable-board=chip --prefix=/usr

.PHONY: build-libsoc
build-libsoc: libsoc/configure libsoc/Makefile
	cd libsoc && make

install-libsoc: build-libsoc
	cd libsoc && make install

.PHONY: build-gratis
build-gratis:
	cd gratis && PANEL_VERSION=V231_G2 make chip
