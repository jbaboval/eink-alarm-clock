#!/usr/bin/make

deps:
	apt-get -y install build-essential python-dev python-pip flex bison vim

local-install:
	sed -i '/# ALARM_CLOCK START/,/# ALARM_CLOCK END/d' /etc/rc.local
	sed -i '/exit 0/i# ALARM_CLOCK START\nmkdir -p /sys/kernel/config/device-tree/overlays/spi\ncat /lib/firmware/nextthingco/chip/sample-spi.dtbo > /sys/kernel/config/device-tree/overlays/spi/dtbo\n# ALARM_CLOCK END\n' /etc/rc.local
	systemctl stop serial-getty@ttyS0.service
	systemctl disable serial-getty@ttyS0.service
