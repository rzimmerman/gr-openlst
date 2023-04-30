#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2023 Robert Zimmerman.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import zmq
import pmt
import threading
from gnuradio import gr

class raw_zmq_source(gr.basic_block):
    """
    Raw ZMQ Source

    This block listens for ZMQ messages on a socket and passes the raw
    bytes of the message as a PMT-encoded uint8 array. This is slightly
    different from the built-in ZMQ Source which expects messages
    arriving on the socket to already be PMT-encoded.

    Supported modes are PULL and SUB
    """
    def __init__(
            self,
            socket_path="ipc:///tmp/socket",
            socket_type="PULL",
        ):
        gr.basic_block.__init__(
            self,
            name='Raw ZMQ Source',
            in_sig=None,
            out_sig=None,
        )
        self.message_port_register_out(pmt.intern("message"))
        self.socket_path = socket_path
        if socket_type.upper() == "PULL":
            self.socket_type = zmq.PULL
        elif socket_type.upper() == "SUB":
            self.socket_type = zmq.SUB
        else:
            raise ValueError(
                "unknown socket type '%s' - expected 'PULL' or 'SUB'" %
                socket_type)
        self.socket = None

    @property
    def socket_poll(self):
        # Opportunistic connect to the socket (on first use)
        if self.socket is None:
            self._context = zmq.Context()
            self.socket = self._context.socket(self.socket_type)
            if self.socket_type == zmq.SUB:
                # SUB sockets need a topic - we set this to a blank filter
                self.socket.setsockopt(zmq.SUBSCRIBE, b"")
            self.socket.bind(self.socket_path)
            self._poller = zmq.Poller()
            self._poller.register(self.socket, zmq.POLLIN)
        return self._poller

    def start(self):
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()
    
    def stop(self):
        pass

    def run(self):
        while True:
            for sock, msg in self.socket_poll.poll(200):
                if sock == self.socket and msg == zmq.POLLIN:
                    raw = bytearray(sock.recv())
                    self.message_port_pub(
                        pmt.intern("message"),
                        pmt.init_u8vector(len(raw), raw)
                    )
