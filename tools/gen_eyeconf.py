#!/usr/bin/env python3
"""
gen_eyeconf.py - AJCloud/Closeli p2pcam eye.conf tool

Generates or decodes the 32-byte /bak/eye.conf binary from a P2P serial number.

Commands:
  encode <SERIAL> [-o FILE]   Generate eye.conf from serial (print hex, or write to FILE)
  decode <FILE>               Decode an existing eye.conf -> serial

Background:
  eye.conf is the 32-byte P2P identity file stored in /bak/. It contains the device
  P2P serial number encrypted with a custom LSB-first DES variant, key "iloveyou".

  Emptying eye.conf forces p2pcam into SONG TOOL mode (RTSP on port 554).
  Restoring a valid 32-byte eye.conf re-enables P2P cloud mode (port 554 closes).

How to find the serial:
  1. Decode /bak/eye.conf BEFORE emptying it:
       python gen_eyeconf.py decode /path/to/eye.conf
  2. Vendor app: YCC365 Plus / AJCloud -> Device details -> Serial number.
     Works even after eye.conf has been emptied.

  Note: the QR code on the camera label encodes the MAC address, not the serial.

The DES variant:
  - Standard DES tables except PC2[35] = 46 instead of 47
  - Key and data both expanded LSB-first; output packed LSB-first
  - ECB mode, no padding (32-byte serial = 4 x 8-byte blocks)
"""

import sys
import os
import re
import struct
import argparse

# ---------------------------------------------------------------------------
# DES variant tables — all read from p2pcam binary (ARM Thumb-2, load base 0x10000)
# All permutation indices are 0-based.
# ---------------------------------------------------------------------------

PC1 = [56,48,40,32,24,16,8,0,57,49,41,33,25,17,9,1,58,50,42,34,26,18,10,2,
       59,51,43,35,62,54,46,38,30,22,14,6,61,53,45,37,29,21,13,5,60,52,44,
       36,28,20,12,4,27,19,11,3]

# PC2 differs from standard DES at index 35: 46 instead of 47
PC2 = [13,16,10,23,0,4,2,27,14,5,20,9,22,18,11,3,25,7,15,6,26,19,12,1,
       40,51,30,36,46,54,29,39,50,44,32,46,43,48,38,55,33,52,45,41,49,35,28,31]

ROTS = [1,1,2,2,2,2,2,2,1,2,2,2,2,2,2,1]

IP = [57,49,41,33,25,17,9,1,59,51,43,35,27,19,11,3,61,53,45,37,29,21,13,5,
      63,55,47,39,31,23,15,7,56,48,40,32,24,16,8,0,58,50,42,34,26,18,10,2,
      60,52,44,36,28,20,12,4,62,54,46,38,30,22,14,6]

FP = [39,7,47,15,55,23,63,31,38,6,46,14,54,22,62,30,37,5,45,13,53,21,61,29,
      36,4,44,12,52,20,60,28,35,3,43,11,51,19,59,27,34,2,42,10,50,18,58,26,
      33,1,41,9,49,17,57,25,32,0,40,8,48,16,56,24]

E = [31,0,1,2,3,4,3,4,5,6,7,8,7,8,9,10,11,12,11,12,13,14,15,16,15,16,17,18,
     19,20,19,20,21,22,23,24,23,24,25,26,27,28,27,28,29,30,31,0]

P = [15,6,19,20,28,11,27,16,0,14,22,25,4,17,30,9,1,7,23,13,31,26,2,8,18,12,29,5,21,10,3,24]

SBOXES = [
    [14,4,13,1,2,15,11,8,3,10,6,12,5,9,0,7,0,15,7,4,14,2,13,1,10,6,12,11,9,5,3,8,
     4,1,14,8,13,6,2,11,15,12,9,7,3,10,5,0,15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13],
    [15,1,8,14,6,11,3,4,9,7,2,13,12,0,5,10,3,13,4,7,15,2,8,14,12,0,1,10,6,9,11,5,
     0,14,7,11,10,4,13,1,5,8,12,6,9,3,2,15,13,8,10,1,3,15,4,2,11,6,7,12,0,5,14,9],
    [10,0,9,14,6,3,15,5,1,13,12,7,11,4,2,8,13,7,0,9,3,4,6,10,2,8,5,14,12,11,15,1,
     13,6,4,9,8,15,3,0,11,1,2,12,5,10,14,7,1,10,13,0,6,9,8,7,4,15,14,3,11,5,2,12],
    [7,13,14,3,0,6,9,10,1,2,8,5,11,12,4,15,13,8,11,5,6,15,0,3,4,7,2,12,1,10,14,9,
     10,6,9,0,12,11,7,13,15,1,3,14,5,2,8,4,3,15,0,6,10,1,13,8,9,4,5,11,12,7,2,14],
    [2,12,4,1,7,10,11,6,8,5,3,15,13,0,14,9,14,11,2,12,4,7,13,1,5,0,15,10,3,9,8,6,
     4,2,1,11,10,13,7,8,15,9,12,5,6,3,0,14,11,8,12,7,1,14,2,13,6,15,0,9,10,4,5,3],
    [12,1,10,15,9,2,6,8,0,13,3,4,14,7,5,11,10,15,4,2,7,12,9,5,6,1,13,14,0,11,3,8,
     9,14,15,5,2,8,12,3,7,0,4,10,1,13,11,6,4,3,2,12,9,5,15,10,11,14,1,7,6,0,8,13],
    [4,11,2,14,15,0,8,13,3,12,9,7,5,10,6,1,13,0,11,7,4,9,1,10,14,3,5,12,2,15,8,6,
     1,4,11,13,12,3,7,14,10,15,6,8,0,5,9,2,6,11,13,8,1,4,10,7,9,5,0,15,14,2,3,12],
    [13,2,8,4,6,15,11,1,10,9,3,14,5,0,12,7,1,15,13,8,10,3,7,4,12,5,6,11,0,14,9,2,
     7,11,4,1,9,12,14,2,0,6,10,13,15,3,5,8,2,1,14,7,4,10,8,13,15,12,9,0,3,5,6,11],
]

KEY = b"iloveyou"

# ---------------------------------------------------------------------------
# Core cipher implementation
# ---------------------------------------------------------------------------

def _lsb_expand(byte_data):
    """Expand bytes to bit array, LSB of each byte first."""
    bits = []
    for b in byte_data:
        for k in range(8):
            bits.append((b >> k) & 1)
    return bits

def _lsb_compress(bits):
    """Pack 64 LSB-first bits back to 8 bytes."""
    out = []
    for j in range(8):
        val = 0
        for k in range(8):
            val |= bits[8 * j + k] << k
        out.append(val & 0xff)
    return bytes(out)

def _permute(bits, table):
    return [bits[i] for i in table]

def _rotate_left(bits, n):
    return bits[n:] + bits[:n]

def _key_schedule(key_bytes):
    bits = _lsb_expand(key_bytes)
    cd = _permute(bits, PC1)
    C, D = cd[:28], cd[28:]
    subkeys = []
    for rot in ROTS:
        C = _rotate_left(C, rot)
        D = _rotate_left(D, rot)
        subkeys.append(_permute(C + D, PC2))
    return subkeys

def _f(R, sk):
    ER = _permute(R, E)
    xored = [ER[i] ^ sk[i] for i in range(48)]
    out = []
    for i in range(8):
        b = xored[i * 6:(i + 1) * 6]
        row = (b[0] << 1) | b[5]
        col = b[1] * 8 + b[2] * 4 + b[3] * 2 + b[4]
        val = SBOXES[i][row * 16 + col]
        for k in range(3, -1, -1):
            out.append((val >> k) & 1)
    return _permute(out, P)

def _encrypt_block(block, subkeys):
    bits = _lsb_expand(block)
    bits = _permute(bits, IP)
    L, R = bits[:32], bits[32:]
    for sk in subkeys:
        f = _f(R, sk)
        L, R = R, [L[j] ^ f[j] for j in range(32)]
    return _lsb_compress(_permute(R + L, FP))

def _decrypt_block(block, subkeys):
    return _encrypt_block(block, list(reversed(subkeys)))

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

SUBKEYS = _key_schedule(KEY)

def encode_serial(serial: str) -> bytes:
    """Encrypt a 32-character P2P serial to produce the 32-byte eye.conf content."""
    raw = serial.encode("ascii")
    if len(raw) != 32:
        raise ValueError(f"Serial must be exactly 32 ASCII characters (got {len(raw)})")
    ct = b""
    for i in range(4):
        ct += _encrypt_block(raw[i * 8:(i + 1) * 8], SUBKEYS)
    return ct

def decode_eyeconf(data: bytes) -> str:
    """Decrypt 32 bytes of eye.conf content to recover the P2P serial."""
    if len(data) != 32:
        raise ValueError(f"eye.conf must be exactly 32 bytes (got {len(data)})")
    pt = b""
    for i in range(4):
        pt += _decrypt_block(data[i * 8:(i + 1) * 8], SUBKEYS)
    serial = pt.decode("ascii")
    # Basic sanity check
    if not re.match(r'^[A-Z0-9]{32}$', serial):
        raise ValueError(f"Decrypted data does not look like a valid serial: {pt!r}")
    return serial

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_encode(args):
    serial = args.serial.strip().upper()
    try:
        data = encode_serial(serial)
    except ValueError as e:
        sys.exit(f"[!] {e}")
    if args.output:
        with open(args.output, 'wb') as f:
            f.write(data)
        print(f"[+] Serial:     {serial}")
        print(f"[+] eye.conf:   {data.hex()}")
        print(f"[+] Written to: {args.output}")
        print(f"\n    To install on the camera (SSH, password: cxlinux):")
        print(f"      cat {args.output} | ssh root@<camera_ip> 'cat > /home/eye.conf'")
        print(f"    start.sh will move it to /bak/eye.conf on the next boot.")
        print(f"\n    WARNING: restoring eye.conf disables RTSP on port 554.")
    else:
        print(f"Serial:    {serial}")
        print(f"eye.conf:  {data.hex()}")
        print(f"Bytes:     {' '.join(f'{b:02x}' for b in data)}")


def cmd_decode(args):
    try:
        with open(args.eyeconf, 'rb') as f:
            data = f.read()
    except OSError as e:
        sys.exit(f"[!] {e}")
    if len(data) == 0:
        sys.exit("[!] eye.conf is empty (0 bytes) -- P2P serial has been lost from this file.")
    try:
        serial = decode_eyeconf(data)
        print(f"[+] P2P serial: {serial}")
    except ValueError as e:
        sys.exit(f"[!] {e}")




def main():
    parser = argparse.ArgumentParser(
        description="AJCloud/Closeli p2pcam eye.conf recovery tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    sub = parser.add_subparsers(dest="cmd")

    p_enc = sub.add_parser("encode", help="Generate eye.conf binary from a P2P serial")
    p_enc.add_argument("serial", help="32-character P2P serial (e.g. AJWL230608101QWWHJ0WID7NPM002243)")
    p_enc.add_argument("-o", "--output", help="Output file (default: print hex only)")

    p_dec = sub.add_parser("decode", help="Decode an existing eye.conf to recover the serial")
    p_dec.add_argument("eyeconf", help="Path to eye.conf (32-byte binary)")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    dispatch = {
        "encode": cmd_encode,
        "decode": cmd_decode,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
