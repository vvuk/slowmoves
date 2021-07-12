from flask import Flask, request, make_response
app = Flask(__name__)

import io
from PIL import Image, ImageOps
import subprocess
import hitherdither

@app.route("/<string:moviefile>")
def movie_frame(moviefile):
    timestamp = float(request.args.get("timestamp", "0"))

    frame = get_frame_ppm(moviefile, timestamp)
    img = render_inkplate10(frame)

    buf = io.BytesIO()
    img.save(buf, format="PPM")
    body = buf.getvalue()

    resp = make_response(body)
    resp.headers["Content-Type"] = "image/x-portable-graymap"
    resp.headers["Content-Length"] = len(body)
    return resp

@app.route("/test-pattern")
def test_pattern():
    with open("test-pattern.pgm", "rb") as fd:
        body = fd.read()

    resp = make_response(body)
    resp.headers["Content-Type"] = "image/x-portable-graymap"
    resp.headers["Content-Length"] = len(body)
    return resp

def get_frame_ppm(moviefile, timestamp):
    args = [
        "ffmpeg",
        "-ss", str(timestamp),
        "-i", moviefile,
        "-frames:v", "1",
        "-vcodec", "ppm",
        "-f", "image2pipe",
        "pipe:"
    ]

    proc = subprocess.run(args, capture_output=True)
    if proc.returncode != 0:
        print(proc.stderr)
        raise Exception("ffmpeg failed")

    return proc.stdout

PALETTE_16_COLORS = []
for i in range(16):
    val = i << 15
    PALETTE_16_COLORS.append(val | (val << 8) | (val << 16))
PALETTE_16 = hitherdither.palette.Palette(PALETTE_16_COLORS)
PALETTE = PALETTE_16

def render_inkplate10(frame):
    resolution = (1200, 825)

    img = Image.open(io.BytesIO(frame))
    img = ImageOps.pad(img, resolution, Image.ANTIALIAS, color=0x000000)
    #img = img.convert("L", dither=Image.FLOYDSTEINBERG, colors=256)
    img = hitherdither.ordered.bayer.bayer_dithering(img, PALETTE, [256/len(PALETTE), 256/len(PALETTE), 256/len(PALETTE)], order=8)
    return img
