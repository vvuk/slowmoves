# pip install git+https://www.github.com/hbldh/hitherdither
# pip install "pillow!=8.3.0" 
# pip install ffmpeg-py
# 8.3.0 has a bug with numpy
import os
import io
import time
import sys
import random
import signal
import logging
import glob
import ffmpeg
import configargparse
from PIL import Image, ImageEnhance
from fractions import Fraction
import hitherdither

PALETTE_2 = hitherdither.palette.Palette([0xF2F4EF, 0x2F2429])
PALETTE_4 = hitherdither.palette.Palette([0xF2F4EF, 0xB1AFAD, 0x70696B, 0x2F2429])
PALETTE_4_R = hitherdither.palette.Palette([0xFFFFFF, 0xAAAAAA, 0x707070, 0x000000])

def generate_frame_as_image(movie_filename, timestamp):
    fq = (ffmpeg
        .input(movie_filename, ss=timestamp)
        .output("pipe:", vframes=1, f="image2pipe", copyts=None, vcodec="ppm")
    )
    #print(fq.compile())
    process = fq.run_async(pipe_stdout=True, pipe_stderr=True)
    fout, ferr = process.communicate()
    return fout

res = generate_frame_as_image("ave5.mkv", "15:00.0")

print(f"Frame bytes length: {len(res)}\n")

img = Image.open(io.BytesIO(res))
img = hitherdither.ordered.bayer.bayer_dithering(img, PALETTE_4, [256/4, 256/4, 256/4], order=8)
img.show()