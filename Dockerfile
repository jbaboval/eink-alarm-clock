# Base image is arm32v7 Alpine Linux on Docker Hub
FROM arm32v6/alpine:3.7

# Install tools needed to download and build the CHIP_IO library from source.
RUN apk update
RUN apk add bison \
  flex \
  g++ \
  gcc \ 
  git \
  make \
  python-dev \
  py-setuptools

# Download source code for device tree compiler needed for CHIP_IO
RUN git clone https://github.com/NextThingCo/dtc.git
		
# Build and install the device tree compiler
RUN make -C dtc
RUN make -C dtc install PREFIX=/usr

# Remove the device tree compiler source code now that we've built it
RUN rm -rf dtc		
# Download the latest CHIP_IO source code
RUN git clone https://github.com/xtacocorex/CHIP_IO.git
		
# Install the CHIP_IO library from the proper directory
RUN cd CHIP_IO && python setup.py install && cd -

# Remove CHIP_IO source code directory after it has been installed
RUN rm -rf CHIP_IO
		
RUN apk add \
  ca-certificates \
  python2 \
  py2-openssl \
  py2-pip \
  geoip-dev \
  linux-headers

RUN pip install spidev pytz python-forecastio bitarray geoip 

RUN apk add \
  autoconf \
  automake \
  libtool \
  bash

ENV CONFIG_SHELL /bin/sh

# Set and create a working directory called app
WORKDIR /app

# Copy the contents of the current directory into the working directory
ADD . /app				
ADD ["WeatherIcons/Font Files/WeatherIcons.ttf", "/usr/share/fonts/truetype/WeatherIcons/"]
ADD weather-icons/font/weathericons-regular-webfont.ttf /usr/share/fonts/truetype/WeatherIcons/

RUN make install-libsoc

RUN apk add pkgconf \
  fuse-dev \
  json-c-dev

RUN make build-gratis

# Remove build tools, which are no longer needed after installation
RUN apk del bison \
  linux-headers \
  py2-pip \
  py2-pillow \
  flex \
  g++ \
  gcc \
  git \
  autoconf \
  automake \
  libtool \
  make

RUN rm -rf /app/.git

RUN echo '@testing http://dl-cdn.alpinelinux.org/alpine/edge/testing' >> /etc/apk/repositories
RUN apk update
RUN apk add i2c-tools@testing

RUN echo '::once:/usr/sbin/i2cset -f -y 0 0x34 0x93 0x0' >> /etc/inittab

				
CMD ["python"]
