#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2023 Robert Zimmerman.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

def pn9():
    """pn9 returns a generator that yields a PN9 sequence
    
    This can be XORed with a data stream to perform CC1110 whitening
    or dewhitening.
    """
    state = 0b111111111
    while True:
        yield state & 0xff
        for _ in range(8):
            new_bit = ((state & (0x20)) >> 5) ^ (state & 0x01)
            state = (state >> 1) | (new_bit << 8)


def whiten(raw: bytes, gen=None):
    """Whiten/dewhiten data
    
    If the gen argument is supplied, an existing pn9 generator can
    be used.
    """
    if gen is None:
        gen = pn9()
    return bytes([r ^ p for r, p in zip(raw, gen)])
