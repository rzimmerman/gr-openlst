#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2023 Robert Zimmerman.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

def crc16(data: bytes) -> int:
    """Calculate the CRC-16 (in the manner of the CC1110) of data"""
    crc = 0xFFFF
    for i in data:
        for _ in range(0, 8):
            if ((crc & 0x8000) >> 8) ^ (i & 0x80):
                crc =(crc << 1) ^ 0x8005
            else:
                crc = crc << 1
            i = i << 1
    return crc & 0xFFFF
