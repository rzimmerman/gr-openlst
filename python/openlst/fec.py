#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2023 Robert Zimmerman.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

aTrellisSourceStateLut = (
    (0, 4), (0, 4), (1, 5), (1, 5), (2, 6), (2, 6), (3, 7), (3, 7),
)
aTrellisTransitionOutput = (
    (0, 3), (3, 0), (1, 2), (2, 1), (3, 0), (0, 3), (2, 1), (1, 2),
)
aTrellisTransitionInput = (0, 1, 0, 1, 0, 1, 0, 1,)


def hamming_weight(byte: int) -> int:
    """Return the number of one bits in a byte"""
    return sum(int(b) for b in f"{byte:b}")


def interleave(chunk: bytes) -> bytes:
    """Interleave or deinterleave a 4 byte chunk"""
    if len(chunk) != 4:
        raise ValueError("interleaving only works on 4 byte chunks")
    chunk_int = int.from_bytes(chunk, byteorder='little')
    grid = []
    for _ in range(4):
        row = []
        for _ in range(4):
            bits = (chunk_int & 0xc0000000) >> 30
            chunk_int = chunk_int << 2
            row.append(bits)
        grid.append(row)

    flipped = 0
    for x in range(4):
        for y in range(4):
            flipped = flipped << 2
            flipped |= grid[y][x]
    return flipped.to_bytes(4, byteorder='little')

def decode_fec_chunk():
    """decode_fec_chunk returns a generator for FEC decode/correction
    
    This generator decodes FEC + interleaved data per CC1110 DN504 (A).
    This involves deinterleaving and decoding a 2:1 Viterbit sequence.

    The caller passes in 4 byte chunks using the `send` function. The
    generator yields decoded chunks.
    """
    path_bits = 0
    cost = [[100] * 8, [0] * 8]
    path = [[0] * 8, [0] * 8]
    last_buf = 0
    cur_buf = 1
    out = []

    while True:
        chunk = yield bytes(out)
        chunk = interleave(chunk)

        symbols = []
        for b in chunk:
            for _ in range(4):
                symbols.append((b & 0xc0) >> 6)
                b <<= 2
        out = []
        for symbol in symbols:
            # check each state in the trellis
            min_cost = 0xff
            for dest_state in range(8):
                input_bit = aTrellisTransitionInput[dest_state]
                src_state0 = aTrellisSourceStateLut[dest_state][0]
                cost0 = cost[last_buf][src_state0]
                cost0 += hamming_weight(symbol ^ aTrellisTransitionOutput[dest_state][0])
                src_state1 = aTrellisSourceStateLut[dest_state][1]
                cost1 = cost[last_buf][src_state1]
                cost1 += hamming_weight(symbol ^ aTrellisTransitionOutput[dest_state][1])

                if cost0 < cost1:
                    cost[cur_buf][dest_state] = cost0
                    min_cost = min(min_cost, cost0)
                    path[cur_buf][dest_state] = (path[last_buf][src_state0] << 1) | input_bit
                else:
                    cost[cur_buf][dest_state] = cost1
                    min_cost = min(min_cost, cost1)
                    path[cur_buf][dest_state] = (path[last_buf][src_state1] << 1) | input_bit
            path_bits += 1


            if path_bits >= 32:
                out.append((path[cur_buf][0] >> 24) & 0xff)
                path_bits -= 8
            last_buf = (last_buf + 1) % 2
            cur_buf = (cur_buf + 1) % 2
            for i in range(8):
                cost[last_buf][i] -= min_cost


# From CC1110 DN504 (A)
FEC_ENCODE_TABLE = [
    0, 3, 1, 2,
    3, 0, 2, 1,
    3, 0, 2, 1,
    0, 3, 1, 2
]


def encode_fec(raw: bytes):
    """Encode bytes with the CC1110 FEC + interleaving mechanism
    
    Poorly copied and half-heartedly translated to Python from CC1110 DN504 (A)
    """
    rv = b""
    terminated = raw + b"\x0b\x0b"
    fec_reg = 0
    chunk = b""
    for c in terminated:
        fec_reg = (fec_reg & 0x700) | c
        fec_output = 0
        for j in range(8):
            fec_output = (fec_output << 2) | FEC_ENCODE_TABLE[fec_reg >> 7]
            fec_reg = (fec_reg << 1) & 0x07ff
        chunk += fec_output.to_bytes(2, byteorder="big")
        if len(chunk) == 4:
            rv += interleave(chunk)
            chunk = b""
    if len(chunk) == 0:
        pass
    elif len(chunk) == 2:
        rv += interleave(chunk + b"\0\0")
    else:
        raise Exception(f"unexpected chunk length {len(chunk)}")
    return rv
