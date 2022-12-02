#!/usr/bin/env python3
# -
# Copyright (c) 2021-2022, David Kalliecharan <dave@dal.ca>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE
#
# SPDX-License-Identifier: BSD-2-Clause

from argparse import ArgumentParser
import numpy as np
import struct
import os.path

CHAR = {
    'B' : 1,
    'H' : 2,
    'I' : 4,
    'Q' : 8,
}


def bin2data(bdata, fmt="H"):
    """Converts binary data to an unsigned type integer"""
    char_len = CHAR[fmt]
    length = len(bdata) // char_len
    data = np.array(struct.unpack(fmt * length, bdata))
    return data


def read_bin(filename):
    with open(filename, 'rb') as f:
        data = bin2data(f.read())
    return data


def write_file(data, fname):
    if type(data) != np.ndarray:
        raise TypeError("Not a numpy.ndarray!")
    data.tofile(fname, "\n", "%i")
    return None


if __name__ == "__main__":
    parser = ArgumentParser(description="Convert binary data to CSV")
    parser.add_argument('file', type=str, help="Binary data file")

    args = parser.parse_args()

    data = read_bin(args.file)

    fname, _ = os.path.splitext(args.file)
    write_file(data, fname + ".CSV")
