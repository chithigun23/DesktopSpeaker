#!/usr/bin/env python3
"""pngscale.py IN.png OUT.png K : nearest-neighbour upscale of an hr dbg PNG (8-bit RGB, filter 0) by K."""
import sys, zlib, struct
d = open(sys.argv[1], 'rb').read(); K = int(sys.argv[3])
W, H = struct.unpack('>II', d[16:24]); p = 8; raw = b''
while p < len(d):
    n = struct.unpack('>I', d[p:p + 4])[0]; t = d[p + 4:p + 8]
    if t == b'IDAT': raw += d[p + 8:p + 8 + n]
    p += 12 + n
raw = zlib.decompress(raw); rows = [raw[r * (3 * W + 1) + 1:(r + 1) * (3 * W + 1)] for r in range(H)]
out = b''
for r in rows:
    line = b''.join(r[3 * i:3 * i + 3] * K for i in range(W))
    out += (b'\x00' + line) * K
def ch(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
open(sys.argv[2], 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', W * K, H * K, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(out)) + ch(b'IEND', b''))
