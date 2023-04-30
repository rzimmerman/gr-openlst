# Installation

This code has been tested primarily on macOS on an M1 Macbook Pro. Linux installation should work well (and be simpler), but I don't have a guide for it at this time.

## GNURadio

Official instructions are [here](https://wiki.gnuradio.org/index.php/InstallingGR).

Installing GNURadio can be done with a package manager. On macOS, Homebrew is recommended:

    # macOS
    brew install gnuradio
    # Debian/Ubuntu
    apt-get install gnuradio

This repository was developed with version 3.10.6.0.

## cmake and build tools

GNURadio modules rely heavily on CMake, even for pure Python implementations like this one.

    # macOS
    brew install cmake
    # Debian/Ubuntu
    apt-get install cmake build-essential

I believe build tools like clang/llvm and make are sufficient on a baseline macOS install, but you may need to install gcc.

PyZMQ is also required. I think this is included as part of GNURadio, but it may need to be installed with:

    pip install --global pyzmq

or

    sudo pip install pyzmq


## Installing this module

The best way to install this (well, the only way I've tried) is with cmake:

    cd gr-openlst
    mkdir build
    cd build
    cmake .. -DCMAKE_INSTALL_PREFIX=/opt/homebrew  # -DCMAKE option for macOS only
    make install

The OpenLST blocks should show up in gnuradio-companion when you next start it up.

## HackRF drivers

You'll need the [SoapySDR](https://formulae.brew.sh/formula/soapysdr) software

    brew install soapyhackrf
    SoapySDRUtil --probe=driver=hackrf  # check if your device was found

## Hardware Setup

This setup was tested with hardware attenuation:

 * 40dB on the RTL-SDR
 * 0dB on the OpenLST transmitter/receiver - I recommend starting with more here (20-30dB) but I didn't have the parts available.
 * 20dB on the output of the HackRF device

With rubber duck antennas.

The HackRF transmitter is always active on the same frequency as the OpenLST. It's attenuated so that its transmit output is significantly below the transmit output of the OpenLST.

Another possibly safer solution:

 * 20dB on the RTL-SDR
 * 20dB on the OpenLST
 * 0dB on the HackRF

Though I found this to be less reliable. I may be able to update this recommendation when I have better equipment and suggestions are welcome.

## OpenLST tools

The OpenLST tools may still require Python 2.7. It's best to run them from a virtualenv.

    sudo pip install -U pip
    sudo pip install virtualenv

And clone the repo to create the environment

    git clone https://github.com/OpenLST/openlst.git
    cd openlst/open-lst/tools
    make venv
    source venv/bin/activate


## Running the Flowgraph and Sending Commands

Open gnuradio-companion:

    gnuradio-companion

And open the flowgraph in this repo under examples/openlst_transceiver.grc. Make sure your RTL-SDR is plugged in and your HackRF board is also plugged in. If you don't have a HackRF board, you can replace that sink block with a null sink for receive only. Or to test loopback, replace both the RTL-SDR and HackRF blocks with a Throttle and connect the RX and TX chains through the throttle.

In another terminal, source the OpenLST tools and start `radio_terminal`:

    cd openlst/open-lst/tools
    source venv/bin/activate
    radio_terminal --rx-socket ipc:///tmp/openlst_rx --tx-socket ipc:///tmp/openlst_tx --hwid 0001

Replace 0001 with your hardware ID.

You should be able to send commands and receive responses if your setup is working properly.

Good luck!
