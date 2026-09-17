# -*- coding: utf-8 -*-
"""Trim the white margin off the 2x master, supersample down to the delivery
width, and emit WebP at a few qualities so the size/quality trade-off is a
measured choice rather than a guess."""
import os
from PIL import Image

D = r"C:\Users\zongy\AppData\Local\Temp\vc_drawio\r3"
SRC = os.path.join(D, "shot20.png")

im = Image.open(SRC).convert("RGB")
print("raw   %dx%d  %.1f KB" % (im.width, im.height,
                                os.path.getsize(SRC) / 1024.0))

# content bbox: anything that is not near-white
mask = im.convert("L").point(lambda p: 255 if p < 246 else 0)
box = mask.getbbox()
print("bbox  %s" % (box,))
im = im.crop(box)

PAD = 40  # 2x-space px -> 20 model px of breathing room
canvas = Image.new("RGB", (im.width + 2 * PAD, im.height + 2 * PAD), "#ffffff")
canvas.paste(im, (PAD, PAD))
print("pad   %dx%d" % (canvas.width, canvas.height))

for width in (2200, 2506):
    k = width / float(canvas.width)
    out = canvas.resize((width, int(round(canvas.height * k))), Image.LANCZOS)
    for q in (82, 86, 90):
        p = os.path.join(D, "cand_%d_q%d.webp" % (width, q))
        out.save(p, "WEBP", quality=q, method=6)
        print("%-26s %dx%d  %.1f KB" % (os.path.basename(p), out.width,
                                        out.height, os.path.getsize(p) / 1024.0))
    out.save(os.path.join(D, "lossless_%d.png" % width), "PNG")
    print("   png reference %dx%d  %.1f KB"
          % (out.width, out.height,
             os.path.getsize(os.path.join(D, "lossless_%d.png" % width)) / 1024.0))
