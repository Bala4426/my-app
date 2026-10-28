"""Generates storage_lens.ico (for the .exe) and prints a base64 PNG (embedded in the app for the window icon)."""
import base64
import io
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
BIG = 1024
BG, HOLE = (22, 30, 48, 255), (22, 30, 48, 255)
SEGMENTS = [  # (share of the disk, colour)
    (0.46, (56, 189, 248, 255)),    # blue
    (0.26, (251, 146, 60, 255)),    # orange
    (0.18, (52, 211, 153, 255)),    # green
    (0.10, (167, 139, 250, 255)),   # purple
]


def render():
    img = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((16, 16, BIG - 16, BIG - 16), radius=220, fill=BG)
    pad = 190
    box = (pad, pad, BIG - pad, BIG - pad)
    start = -90.0
    gap = 4.0
    for share, col in SEGMENTS:
        end = start + 360 * share
        d.pieslice(box, start + gap / 2, end - gap / 2, fill=col)
        start = end
    inner = 150
    d.ellipse((BIG // 2 - inner - 60, BIG // 2 - inner - 60, BIG // 2 + inner + 60, BIG // 2 + inner + 60), fill=HOLE)
    # small "used" needle: a rounded bar in the middle
    d.rounded_rectangle((BIG // 2 - 26, BIG // 2 - 150, BIG // 2 + 26, BIG // 2 + 26), radius=26, fill=(241, 245, 249, 255))
    return img


if __name__ == "__main__":
    big = render()
    sizes = [16, 24, 32, 48, 64, 128, 256]
    big.save(os.path.join(HERE, "storage_lens.ico"), sizes=[(s, s) for s in sizes])
    buf = io.BytesIO()
    big.resize((64, 64), Image.LANCZOS).save(buf, "PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode()
    with open(os.path.join(HERE, "icon_b64.txt"), "w") as f:
        f.write(b64)
    print("icon written; b64 length", len(b64))
