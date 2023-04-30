#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2023 Robert Zimmerman.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import zmq
import pmt
from gnuradio import gr

class raw_zmq_sink(gr.basic_block):
    """
    Raw ZMQ Sink

    This block writes ZMQ messages to a socket from bytes of the incoming message.
    This is slightly different from the built-in ZMQ sink which writes messages as
    PMT-encoded.

    Supported modes are PUB and PUSH.
    """
    def __init__(
            self,
            socket_path="ipc:///tmp/socket",
            socket_type="PUB",
        ):
        gr.basic_block.__init__(
            self,
            name='Raw ZMQ Sink',
            in_sig=None,
            out_sig=None,
        )
        self.message_port_register_in(pmt.intern('message'))
        self.set_msg_handler(pmt.intern('message'), self.handle_msg)
        self.socket_path = socket_path
        if socket_type.upper() == "PUB":
            self.socket_type = zmq.PUB
        elif socket_type.upper() == "PUSH":
            self.socket_type = zmq.PUSH
        else:
            raise ValueError(
                "unknown socket type '%s' - expected 'PUB' or 'PUSH'" %
                socket_type)
        self._socket = None

    @property
    def socket(self):
        # Opportunistic bind to the socket (on first use)
        if self._socket is None:
            self._context = zmq.Context()
            self._socket = self._context.socket(self.socket_type)
            self._socket.bind(self.socket_path)
        return self._socket

    def handle_msg(self, msg):
        raw = bytes(pmt.u8vector_elements(msg))
        self.socket.send(raw)
