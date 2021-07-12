from flask import Flask, request, make_response, abort
app = Flask(__name__)

import io
from PIL import Image, ImageOps
import subprocess
import hitherdither

def select_format():
    format = "PNG"
    content_type = "image/png"

    if "image/x-portable-graymap" in request.headers.get("Accept", ""):
        format = "PPM"
        content_type = "image/x-portable-graymap"
    
    return (format, content_type)

@app.route("/<string:moviefile>")
def movie_frame(moviefile):
    if moviefile == "favicon.ico":
        abort(404)
    timestamp = float(request.args.get("timestamp", "0"))

    (format, content_type) = select_format()
    body = frame_for_movie(moviefile, timestamp, format)

    resp = make_response(body)
    resp.headers["Content-Type"] = content_type
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

MAC_TIMESTAMP_TABLE = dict()

@app.route("/slowframe")
def slow_frame_client():
    mac = request.args.get("mac", "unknown")

    # TODO better save/lookup

    if mac not in MAC_TIMESTAMP_TABLE:
        MAC_TIMESTAMP_TABLE[mac] = 5000

    timestamp = MAC_TIMESTAMP_TABLE[mac]
    MAC_TIMESTAMP_TABLE[mac] = timestamp + 1
    print(f"Sending frame at timestamp {timestamp}")

    moviefile = "russia.mkv"

    # SAME TIMESTAMP FOR COMPARISON
    timestamp = 5002

    (format, content_type) = select_format()
    body = frame_for_movie(moviefile, timestamp, format)

    resp = make_response(body)
    resp.headers["Content-Type"] = content_type
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
        print("=======\n")
        print(proc.stderr)
        print("\n=======\n")
        raise Exception("ffmpeg failed")

    return proc.stdout

def frame_for_movie(moviefile, timestamp, format):
    frame = get_frame_ppm(moviefile, timestamp)
    img = render_inkplate10(frame)

    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()

# Generate palettes
def make_palette(num):
    colors = []
    bits = bin(num-1).count("1")
    for i in range(num):
        val = i << (8 - bits)
        if i >= num / 2:
            val = val | (0xff >> bits)
        cval = (val | (val << 8) | (val << 16))
        print(f"{cval:x} ")
        colors.append(cval)
    return hitherdither.palette.Palette(colors)

PALETTE_8 = make_palette(8)
PALETTE_4 = make_palette(4)
PALETTE_2 = make_palette(2)
# use this palette
PALETTE = PALETTE_2

def render_inkplate10(frame):
    resolution = (1200, 825)

    img = Image.open(io.BytesIO(frame))
    img = ImageOps.pad(img, resolution, Image.ANTIALIAS, color=0x000000)
    #img = img.convert("L", dither=Image.FLOYDSTEINBERG, colors=256)
    img = hitherdither.ordered.bayer.bayer_dithering(img, PALETTE, [256/len(PALETTE), 256/len(PALETTE), 256/len(PALETTE)], order=8)

    # PIL can't write mode "P" as PPM, so convert back to grayscale
    img = img.convert("L", dither=Image.NONE, colors=256)

    return img
