#!/usr/bin/env python3
"""Generate the hero dial ornament.  Usage: gen_dial.py <out.svg>

A 640 unit dial: hairline bezel ring, railway minute track with 60 ticks,
12 brass hour batons (a pair at twelve), and a rose-engine field of
barleycorn (grain d'orge) scallops.  One scalloped ring is drawn once and
reused; each next ring is scaled up and turned half a lobe so its cusps sit
on the crowns of the ring inside it.
"""
import math
import sys

LINE = "#2A2E37"
LINE2 = "#363B45"
BRASS = "#C6A15B"
C = 320.0

LOBES = 60        # scallops per ring, one to a minute
ALPHA = 0.30      # sagitta as a share of the chord
R_FIELD_IN = 96.0
R_FIELD_OUT = 246.0


def f(v, p=2):
    s = f"{v:.{p}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def pt(r, deg):
    a = math.radians(deg - 90)
    return C + r * math.cos(a), C + r * math.sin(a)


def radial(r1, r2, deg, off=0.0):
    a = math.radians(deg - 90)
    px, py = -math.sin(a) * off, math.cos(a) * off
    x1, y1 = pt(r1, deg)
    x2, y2 = pt(r2, deg)
    return f"M{f(x1 + px)} {f(y1 + py)}L{f(x2 + px)} {f(y2 + py)}"


def field():
    half = math.pi / LOBES
    rc = 100.0
    chord = 2 * rc * math.sin(half)
    sag = ALPHA * chord
    rp = rc * math.cos(half) + sag
    big_r = (chord * chord / 4 + sag * sag) / (2 * sag)
    q = rp / rc
    d = []
    for i in range(LOBES + 1):
        ang = math.radians(i * 360.0 / LOBES - 90)
        x, y = rc * math.cos(ang), rc * math.sin(ang)
        d.append(f"M{f(x)} {f(y)}" if i == 0 else f"A{f(big_r)} {f(big_r)} 0 0 1 {f(x)} {f(y)}")
    out = [
        "<defs>",
        f'<path id="s" d="{"".join(d)}z" vector-effect="non-scaling-stroke"/>',
        f'<clipPath id="c"><path clip-rule="evenodd" d="M320 {f(C - R_FIELD_OUT)}a{f(R_FIELD_OUT)} {f(R_FIELD_OUT)} 0 1 0 .01 0zM320 {f(C - R_FIELD_IN)}a{f(R_FIELD_IN)} {f(R_FIELD_IN)} 0 1 0 .01 0z"/></clipPath>',
        "</defs>",
        '<g clip-path="url(#c)">',
        f'<g fill="none" stroke="{LINE2}" stroke-width=".6" transform="translate(320 320)">',
    ]
    # start a little inside the inner ring so the field is cut by it, and run
    # a little past the outer ring for the same reason
    r = R_FIELD_IN / q / q
    k = 0
    while r <= R_FIELD_OUT:
        rot = (k % 2) * (180.0 / LOBES)
        out.append(f'<use href="#s" transform="rotate({f(rot)}) scale({f(r / rc, 4)})"/>')
        r *= q
        k += 1
    out += ["</g>", "</g>"]
    return out


def build():
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" width="640" height="640">']
    out += field()
    out.append(f'<g fill="none" stroke="{LINE2}">')
    ne = ' vector-effect="non-scaling-stroke"'
    for r in (319.5, 309.5, 299.5, R_FIELD_OUT, R_FIELD_IN):
        out.append(f'<circle cx="320" cy="320" r="{f(r)}"{ne}/>')
    out.append(f'<circle cx="320" cy="320" r="4.5"{ne}/>')
    ticks = "".join(radial(299.5, 309.5, i * 6) for i in range(60))
    out.append(f'<path d="{ticks}"{ne}/>')
    out.append("</g>")
    batons = []
    for h in range(12):
        for off in ((-3.0, 3.0) if h == 0 else (0.0,)):
            batons.append(radial(259, 289, h * 30, off))
    out.append(f'<path d="{"".join(batons)}" fill="none" stroke="{BRASS}" stroke-width="2"/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    with open(sys.argv[1], "w") as fh:
        fh.write(build())
