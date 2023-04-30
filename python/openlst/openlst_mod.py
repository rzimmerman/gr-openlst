#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2023 Robert Zimmerman.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import pmt
import time
import numpy as np
from gnuradio import gr

from .fec import encode_fec
from .whitening import whiten
from .crc import crc16

class openlst_mod(gr.sync_block):
    """
    OpenLST Encoder/Framer

    This block encodes a raw data packet (typically from a ZMQ socket)
    in the form:
    
        | HWID (2 bytes) | Seqnum (2 bytes) | Data (N bytes) |
    
    To an RF message:

        | Preamble | Sync Word(s) | Data Segment |
    
    Where "Data Segment" contains:

        | Length (1 byte) | Flags (1 byte) | Seqnum (2 bytes) | Data (N bytes) | HWID (2 bytes) | CRC (2 bytes)
    
    And may be encoded with whitening (PN-9 coding) and/or 2:1 Forward-Error Correction (FEC).

    It supports throttling of the output data rate for low bitrates. This avoids filling up the
    (very large) buffer of the downstream blocks and inducing a lot of latency.
    """
    def __init__(
            self,
            preamble_bytes=4,
            sync_byte1=0xd3,
            sync_byte0=0x91,
            sync_words=2,
            flags=0xC0,
            fec=True,
            whitening=True,
            bitrate=7415.77,
            max_latency=0.1,
        ):
        gr.sync_block.__init__(
            self,
            name="OpenLST Encode and Frame",
            in_sig=None,
            out_sig=[np.uint8],
        )
        # Messages arrive in raw form without a length or CRC
        # generally this comes from a ZMQ socket
        self.message_port_register_in(pmt.intern('message'))
        self.set_msg_handler(pmt.intern('message'), self.handle_msg)

        self.preamble_bytes = preamble_bytes
        self.sync_byte1 = sync_byte1
        self.sync_byte0 = sync_byte0
        self.sync_words = sync_words
        self.flags = flags
        self.fec = fec
        self.whitening = whitening

        self._msg_buffer = []
        self._partial = False

        self.bitrate = bitrate
        if self.bitrate != 0:
            # Attempt to set the output buffer to about 1 packet
            # this will be rounded to the nearest system page size, however,
            # which can be 4KB or 16KB and may produce a warning
            self.set_max_output_buffer(0, 255)

        self.max_latency = max_latency
        self._bytes_sent = 0
        self._last_buff_check = None

    def handle_msg(self, msg):
        raw = bytearray(pmt.to_python(msg))

        # Insert the preamble and sync words
        preamble = bytearray(
            [0xaa] * self.preamble_bytes +  # preamble
            [self.sync_byte1, self.sync_byte0] * self.sync_words)  # sync word(s)
        
        # Prefix with length byte and flags
        content = bytes(
            [len(raw) + 3] +  # length = raw + flags + checksum (2 bytes)
            [self.flags]  # flags
        )
        content += raw[2:]  # data (includes seqnum)
        # The HWID goes at the end for RF transmission
        content += raw[0:2]
        checksum = crc16(content)

        # Append checksum
        content += checksum.to_bytes(2, byteorder='little')

        # Per the datasheet, whitening happens _before_ FEC
        if self.whitening:
            content = whiten(content)
        if self.fec:
            content = encode_fec(content)

        # Queue these bytes for transmission
        self._msg_buffer.append((time.time(), preamble + content))


    def work(self, input_items, output_items):
        if self._last_buff_check is None:
            self._bytes_sent = 0
            self._last_buff_check = time.time()

        if len(self._msg_buffer) > 0:
            recv_time, msg = self._msg_buffer[0]
            # Try to send the whole message, but send a chunk for now
            # if the output buffer is too small (unlikely given our message size)
            bytes_out = min(len(msg), len(output_items[0]))
            # Write the bytes
            output_items[0][:bytes_out] = msg[:bytes_out]
            # Save the rest for next iteration
            remaining = msg[bytes_out:]
            if len(remaining) > 0:
                self._partial = True
                self._msg_buffer[0] = (recv_time, remaining)
            else:
                # Message complete
                self._partial = False
                self._msg_buffer.pop(0)

            # Keep track of bytes sent so we can estimate bitrate
            self._bytes_sent += bytes_out
            return bytes_out
        elif self.bitrate:
            # If the user has set a target bitrate, try not to exceed it
            # by more than a little bit
            dt = max(time.time() - self._last_buff_check, 0.001)

            # Decide how much fill is missing to reach the target bitrate
            expected_bytes = int(self.bitrate * dt // 8)
            latency_buff_bytes = int(self.bitrate * self.max_latency // 8)
            fill = expected_bytes + latency_buff_bytes - self._bytes_sent
            if fill < 0:
                # Try to fill the buffer to catch up
                bytes_out = min(len(output_items[0]), fill)
            else:
                # Just send one byte, but wait a little and throttle the flow
                # so we don't just fill the buffer one byte at a time
                time.sleep(1.02 * 8.0 / self.bitrate)
                bytes_out = 1

            output_items[0][:bytes_out] = 0
            self._bytes_sent += bytes_out
            return bytes_out
        else:
            # Return fill data without throttle
            output_items[0][0] = 0
            self._bytes_sent += 1
            return 1
