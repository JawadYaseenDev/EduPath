"""Draws the EduRecommend logo: a winding road leading up to a graduation cap.

Outputs (in this folder):
  logo.svg                 vector logo (rounded square)
  logo-1024.png            app icon with background (iOS, web, store listing)
  logo-foreground-1024.png transparent foreground for Android adaptive icons
  logo-mark-512.png        transparent mark (for dark backgrounds only)
  logo-icon-512.png        rounded icon used inside the apps

Run:  uv run --with pillow python branding/make_logo.py
The SVG and PNGs are drawn from the same shapes, so they always match.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).parent
S = 1024  # design canvas

GREEN_TOP = (21, 128, 99)
GREEN_BOTTOM = (11, 79, 62)
ROAD = (246, 236, 208)
ROAD_EDGE = (226, 211, 170)
DASH = (255, 200, 87)
CAP = (255, 255, 255)
CAP_SHADE = (214, 236, 228)
TASSEL = (255, 200, 87)


def bezier(p0, p1, p2, p3, n=200):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def shapes():
    """All shapes in a 1024 x 1024 design space: list of (kind, points, colour)."""
    # Road centre line: from the bottom, an S-bend up to the foot of the cap.
    centre = bezier((470, 1130), (400, 900), (730, 720), (512, 470))
    left, right = [], []
    for i, (x, y) in enumerate(centre):
        j = min(i + 1, len(centre) - 1)
        k = max(i - 1, 0)
        dx, dy = centre[j][0] - centre[k][0], centre[j][1] - centre[k][1]
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length, dx / length
        t = i / (len(centre) - 1)
        half = 140 * (1 - t) + 34 * t  # wide near us, narrow far away
        left.append((x + nx * half, y + ny * half))
        right.append((x - nx * half, y - ny * half))
    road = left + right[::-1]
    edge = [(x, y) for x, y in road]

    # Dashes on the centre line, getting shorter with distance.
    dashes = []
    i = 8
    while i < len(centre) - 20:
        t = i / (len(centre) - 1)
        seg = int(16 * (1 - t) + 6 * t)
        width = 22 * (1 - t) + 7 * t
        a, b = centre[i], centre[min(i + seg, len(centre) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length * width / 2, dx / length * width / 2
        dashes.append([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny),
                       (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)])
        i += seg * 2

    # Graduation cap (mortarboard) sitting where the road ends.
    cx, cy = 512, 330
    board = [(cx, cy - 92), (cx + 250, cy), (cx, cy + 92), (cx - 250, cy)]
    skull = [(cx - 150, cy + 40), (cx + 150, cy + 40), (cx + 135, cy + 150),
             (cx, cy + 185), (cx - 135, cy + 150)]
    cord = [(cx - 6, cy - 6), (cx + 6, cy - 6), (cx + 196, cy + 40), (cx + 184, cy + 48)]
    tassel = [(cx + 176, cy + 40), (cx + 204, cy + 40), (cx + 214, cy + 170), (cx + 166, cy + 170)]
    button = [(cx + 16 * math.cos(a), cy + 16 * math.sin(a))
              for a in [k * math.pi / 8 for k in range(16)]]

    return [
        ("poly", edge, ROAD_EDGE),
        ("poly", road, ROAD),
        *[("poly", d, DASH) for d in dashes],
        ("poly", skull, CAP_SHADE),
        ("poly", board, CAP),
        ("poly", cord, TASSEL),
        ("poly", tassel, TASSEL),
        ("poly", button, TASSEL),
    ]


def transform(points, scale, offset):
    return [(x * scale + offset, y * scale + offset) for x, y in points]


def draw_png(size, background: bool, scale=1.0, supersample=4):
    big = size * supersample
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    k = big / S
    if background:
        grad = Image.new("RGBA", (big, big))
        gd = ImageDraw.Draw(grad)
        for y in range(big):
            t = y / big
            c = tuple(int(GREEN_TOP[i] * (1 - t) + GREEN_BOTTOM[i] * t) for i in range(3))
            gd.line([(0, y), (big, y)], fill=c + (255,))
        mask = Image.new("L", (big, big), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, big - 1, big - 1], radius=int(224 * k), fill=255)
        img.paste(grad, (0, 0), mask)
    layer = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    offset = (1 - scale) * S / 2
    for _kind, pts, colour in shapes():
        p = transform(pts, scale, offset)
        d.polygon([(x * k, y * k) for x, y in p], fill=colour + (255,))
    if background:
        # Keep the road inside the rounded square.
        clip = Image.new("L", (big, big), 0)
        ImageDraw.Draw(clip).rounded_rectangle([0, 0, big - 1, big - 1], radius=int(224 * k), fill=255)
        layer.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", (big, big), 0), clip))
    img = Image.alpha_composite(img, layer)
    return img.resize((size, size), Image.LANCZOS)


def write_svg(path: Path):
    def hexc(c):
        return "#%02x%02x%02x" % c

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="{S}" height="{S}">',
        "<title>EduRecommend</title>",
        "<defs>",
        '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0" stop-color="{hexc(GREEN_TOP)}"/>',
        f'<stop offset="1" stop-color="{hexc(GREEN_BOTTOM)}"/>',
        "</linearGradient>",
        f'<clipPath id="r"><rect width="{S}" height="{S}" rx="224"/></clipPath>',
        "</defs>",
        f'<rect width="{S}" height="{S}" rx="224" fill="url(#bg)"/>',
        '<g clip-path="url(#r)">',
    ]
    for _kind, pts, colour in shapes():
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        parts.append(f'<polygon points="{p}" fill="{hexc(colour)}"/>')
    parts += ["</g>", "</svg>"]
    path.write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    write_svg(OUT / "logo.svg")
    draw_png(1024, background=True).save(OUT / "logo-1024.png")
    # Android adaptive icons crop to a circle/squircle: keep the drawing in the safe zone.
    draw_png(1024, background=False, scale=0.62).save(OUT / "logo-foreground-1024.png")
    draw_png(512, background=False, scale=0.92).save(OUT / "logo-mark-512.png")
    # In-app logo: keeps its green background so it works in light and dark mode.
    draw_png(512, background=True).save(OUT / "logo-icon-512.png")
    print("Wrote logo.svg, logo-1024.png, logo-foreground-1024.png, logo-mark-512.png, logo-icon-512.png")
