from typing import Any, cast

import math
import random
import sys
import base64
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

rnd = random.Random(7)


def bez(p0, p1, p2, p3, t):
    return tuple(
        round((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t**3 * d, 1)
        for a, b, c, d in zip(p0, p1, p2, p3)
    )


# Ty 0.0.18 miscounts the fixed tuple expansion below; keep the approved drawing intact.
bez = cast(Any, bez)

# ---- Forest plot: a column of square stars whose horizontal diffraction flares are the whiskers
ROWS = [  # (estimate x, y, half CI width, square size)
    (351, 74, 50, 7), (381, 106, 46, 9), (326, 138, 40, 11),
    (370, 170, 50, 9), (338, 202, 38, 12), (398, 234, 62, 6),
]
forest = []
for x, y, hw, s in ROWS:
    forest.append(
        f'<rect x="{x-hw}" y="{y-0.6}" width="{2*hw}" height="1.2" fill="url(#flare)"/>'
        f'<line x1="{x}" y1="{y-s*1.3}" x2="{x}" y2="{y+s*1.3}" stroke="#fff" stroke-opacity=".35" stroke-width=".8"/>'
        f'<circle cx="{x-hw}" cy="{y}" r=".9" fill="#dfe5ff" opacity=".7"/>'
        f'<circle cx="{x+hw}" cy="{y}" r=".9" fill="#dfe5ff" opacity=".7"/>'
        f'<circle cx="{x}" cy="{y}" r="{s*1.2}" fill="url(#starGlow)"/>'
        f'<rect x="{x-s/2}" y="{y-s/2}" width="{s}" height="{s}" rx=".8" fill="#fffaf0"/>'
    )
forest = "\n        ".join(forest)


# ---- Meta-regression: a comet whose straight tail is the regression line; weighted square stars around it
def star(cx, cy, sz):
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{sz*1.2:.1f}" fill="url(#starGlow)"/>'
        f'<line x1="{cx}" y1="{cy-sz*1.3:.1f}" x2="{cx}" y2="{cy+sz*1.3:.1f}" stroke="#fff" stroke-opacity=".35" stroke-width=".8"/>'
        f'<rect x="{cx-sz/2}" y="{cy-sz/2}" width="{sz}" height="{sz}" rx=".8" fill="#fffaf0"/>'
    )


TAIL0, HEAD = (8, 262), (262, 58)
roids = []
roid_pos = []
for t, r in [(0.1, 4), (0.22, 8), (0.36, 5), (0.47, 11), (0.6, 6), (0.71, 9)]:
    x = TAIL0[0] + (HEAD[0] - TAIL0[0]) * t
    y = TAIL0[1] + (HEAD[1] - TAIL0[1]) * t + rnd.uniform(-7, 7)
    roids.append(star(round(x, 1), round(y, 1), r))
    roid_pos.append((x, y, r))
roids = "\n        ".join(roids)
# The comet's head is a meteor: an irregular rock glowing hot on its leading edge
mr = random.Random(11)
meteor = []
for i in range(11):
    a = i / 11 * 2 * math.pi
    r = 11.5 * mr.uniform(.78, 1.08)
    meteor.append(f"{HEAD[0] + r*math.cos(a):.1f},{HEAD[1] + r*math.sin(a):.1f}")
meteor = " ".join(meteor)


# ---- Funnel plot: clusters of pines (studies), tight under the summit and spreading toward the foot
CLUSTERS = [(163, 262, 3), (139, 271, 2), (171, 293, 3), (125, 318, 2), (186, 337, 3),
            (110, 360, 3), (156, 372, 4), (207, 388, 3), (90, 403, 4), (232, 414, 3)]
tr = random.Random(5)
trees = []


def pine(x, y, h):
    w = h * .34
    t = [f'<ellipse cx="{x + w*.3:.1f}" cy="{y + .3:.1f}" rx="{w*1.1:.1f}" ry="{h*.07:.2f}" fill="#0a0d3a" fill-opacity=".45"/>',
         f'<rect x="{x - h*.03:.2f}" y="{y - h*.16:.1f}" width="{h*.06:.2f}" height="{h*.16:.1f}" fill="#1a1430"/>']
    for k, (top, bot, ww) in enumerate(((0, .42, .62), (.22, .7, .82), (.44, .86, 1))):
        yt, yb, hw = y - h*(1 - top), y - h*(1 - bot) + h*.0, w*ww
        t.append(f'<path d="M{x:.1f},{yt:.1f} L{x+hw:.1f},{yb:.1f} Q{x:.1f},{yb - h*.05:.1f} {x-hw:.1f},{yb:.1f} Z" fill="#1b4560"/>')
        t.append(f'<path d="M{x:.1f},{yt:.1f} L{x+hw:.1f},{yb:.1f} Q{x+hw*.5:.1f},{yb - h*.03:.1f} {x+hw*.15:.1f},{yb - h*.02:.1f} Z" fill="#ffb38a" fill-opacity=".16"/>')
    return "".join(t)


for cx, cy, n in CLUSTERS:
    h = 6.5 + (cy - 220) * .036  # nearer clusters (lower) are drawn taller
    for k in sorted(range(n), key=lambda k: k % 2):  # back row first
        x = cx + (k - (n - 1) / 2) * h * .42 + tr.uniform(-.6, .6)
        y = cy + (k % 2) * h * .12 + tr.uniform(-.4, .4)
        trees.append(pine(x, y, h * tr.uniform(.8, 1.15)))
trees = "".join(trees)

# ---- SROC: a trail that climbs steeply from the near corner, then levels off toward the horizon
L = ((0, 600), (12, 522), (58, 478), (194, 462)), ((194, 462), (316, 450), (420, 446), (520, 443))
R = ((520, 449), (420, 452), (320, 458), (206, 471)), ((206, 471), (92, 486), (54, 530), (46, 600))
TRAIL = (f"M{L[0][0][0]},{L[0][0][1]} C{L[0][1][0]},{L[0][1][1]} {L[0][2][0]},{L[0][2][1]} {L[0][3][0]},{L[0][3][1]} "
         f"C{L[1][1][0]},{L[1][1][1]} {L[1][2][0]},{L[1][2][1]} {L[1][3][0]},{L[1][3][1]} "
         f"L{R[0][0][0]},{R[0][0][1]} C{R[0][1][0]},{R[0][1][1]} {R[0][2][0]},{R[0][2][1]} {R[0][3][0]},{R[0][3][1]} "
         f"C{R[1][1][0]},{R[1][1][1]} {R[1][2][0]},{R[1][2][1]} {R[1][3][0]},{R[1][3][1]} Z")
MID = ((23, 600), (33, 526), (76, 482), (200, 466)), ((200, 466), (318, 454), (420, 449), (520, 446))
glints = []
for seg, t, w in [(0, .25, 9), (0, .7, 6), (1, .1, 4.5), (1, .4, 3.5), (1, .7, 2.6), (1, .92, 2)]:
    x, y = bez(*MID[seg], t)
    glints.append(
        f'<circle cx="{x}" cy="{y}" r="{w*.55:.1f}" fill="url(#starGlow)"/>'
        f'<path d="M{x},{y-.2} v{w*.6:.1f}" stroke="#fff6e4" stroke-opacity=".25" stroke-width=".5" stroke-linecap="round"/>'
        f'<circle cx="{x}" cy="{y}" r=".7" fill="#fff6e4" fill-opacity=".8"/>'
    )
glints = "".join(glints)
sx, sy = bez(*MID[0], .47)
# A footbridge where the river climbs steeply, carrying the Funnel Peak path to the near bank
BW, BE = bez(*L[0], .5), bez(*R[1], .5)
BW, BE = (BW[0] - 4, BW[1] - 1), (BE[0] + 4, BE[1] + 1)

# ---- Foreground pines: tiered silhouettes, rim-lit on the side facing the sun (left)
def big_pine(x, top, base, w):
    h = base - top
    out = [f'<rect x="{x-1.8}" y="{base - h*.08:.1f}" width="3.6" height="{600 - base + h*.08:.1f}" fill="#070926"/>']
    for k, (a, b, ww) in enumerate(((0, .34, .42), (.2, .56, .64), (.4, .78, .84), (.6, 1, 1))):
        yt, yb, hw = top + h*a, top + h*b, w*ww
        out.append(f'<path d="M{x},{yt:.1f} L{x+hw:.1f},{yb:.1f} Q{x},{yb - h*.04:.1f} {x-hw:.1f},{yb:.1f} Z" fill="#090c34"/>')
        out.append(f'<path d="M{x},{yt:.1f} L{x-hw:.1f},{yb:.1f} Q{x-hw*.75:.1f},{yb - h*.02:.1f} {x-hw*.55:.1f},{yb - h*.025:.1f} Z" fill="#9a8ee0" fill-opacity=".13"/>')
    return "".join(out)


fg_pines = big_pine(404, 474, 562, 24) + big_pine(494, 454, 560, 26) + big_pine(448, 436, 552, 30)

# ---- Astronomer's chart: a faint ecliptic with ticks, and asterism lines between the forest stars
def quad(p0, p1, p2, t):
    return tuple((1-t)**2*a + 2*(1-t)*t*b + t*t*c for a, b, c in zip(p0, p1, p2))
E0, E1, E2 = (-10, 150), (250, 30), (530, 150)
ticks = []
for k in range(1, 26):
    t = k / 26
    x, y = quad(E0, E1, E2, t)
    dx, dy = (2*(1-t)*(E1[0]-E0[0]) + 2*t*(E2[0]-E1[0]), 2*(1-t)*(E1[1]-E0[1]) + 2*t*(E2[1]-E1[1]))
    n = math.hypot(dx, dy); nx, ny = -dy/n, dx/n
    h = 3.2 if k % 5 == 0 else 1.6
    ticks.append(f'M{x-nx*h:.1f},{y-ny*h:.1f}L{x+nx*h:.1f},{y+ny*h:.1f}')
ticks = "".join(ticks)
asterism = " ".join(f"{x},{y}" for x, y, _, _ in ROWS)

html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>RCMS splash - direction</title>
<style>
  html, body {{ margin: 0; }}
  body {{ background: #1e1e1e; padding: 40px; }}
  .splash {{
    position: relative; display: flex;
    width: 960px; height: 600px; border-radius: 10px; overflow: hidden;
    font-family: "Segoe UI", system-ui, sans-serif;
    box-shadow: 0 30px 80px rgba(0,0,0,.45), 0 0 0 1px rgba(0,0,0,.08);
  }}
  .panel {{ width: 440px; background: #fff; position: relative; color: #1f2a44; }}
  .art {{ width: 520px; }}
  .art svg {{ display: block; }}
  .logo {{ position: absolute; left: 52px; top: 92px; width: 320px; }}
  .p {{ position: absolute; left: 56px; right: 40px; margin: 0; }}
  /* Runtime text (drawn by the app at startup, not part of the artwork PNG) */
  .version {{ top: 200px; font-size: 14px; line-height: 20px; color: #4f5a76; }}
  .legal   {{ top: 266px; font-size: 13.5px; line-height: 21px; color: #4f5a76; }}
  .status  {{ top: 352px; font-size: 15px; line-height: 20px; font-weight: 500; }}
  .names   {{ top: 462px; font-size: 13.5px; line-height: 21px; color: #4f5a76; }}
</style>
</head>
<body>
<div class="splash">
  <div class="panel">
    <img class="logo" src="../../../src/rc_metastudio/images/rc-metastudio-splash-logo.png" alt="RC MetaStudio">
    <p class="p version">Version 0.5.3</p>
    <p class="p legal">&copy; 2026 Ali Salman and RC MetaStudio contributors.<br>Released under GPL-3.0.</p>
    <p class="p status">Loading metafor&hellip;</p>
    <p class="p names">Statistics by R, metafor, meta, mada, and RCMetaR.<br>Built with Python, Qt, and rpy2.</p>
  </div>

  <div class="art">
    <svg width="520" height="600" viewBox="0 0 520 600">
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#070d3a"/><stop offset=".45" stop-color="#1b2a8c"/>
          <stop offset=".6" stop-color="#6a4bb8"/><stop offset=".7" stop-color="#ff8a4c"/>
          <stop offset=".76" stop-color="#ffc27a"/>
        </linearGradient>
        <radialGradient id="sunGlow" cx="370" cy="398" r="230" gradientUnits="userSpaceOnUse">
          <stop offset="0" stop-color="#ffb347" stop-opacity=".95"/><stop offset=".35" stop-color="#ff7a12" stop-opacity=".35"/>
          <stop offset="1" stop-color="#ff7a12" stop-opacity="0"/>
        </radialGradient>
        <linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#fff1c9"/><stop offset=".5" stop-color="#ffb347"/><stop offset="1" stop-color="#ff7a12"/>
        </linearGradient>
        <linearGradient id="ray" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0" stop-color="#ffd59a" stop-opacity=".55"/><stop offset="1" stop-color="#ffd59a" stop-opacity="0"/>
        </linearGradient>
        <linearGradient id="mtn" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#3a3f9e"/><stop offset="1" stop-color="#1a1f66"/>
        </linearGradient>
        <linearGradient id="flare" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="#dfe5ff" stop-opacity=".25"/><stop offset=".5" stop-color="#fff" stop-opacity=".85"/>
          <stop offset="1" stop-color="#dfe5ff" stop-opacity=".25"/>
        </linearGradient>
        <radialGradient id="starGlow"><stop offset="0" stop-color="#cfd8ff" stop-opacity=".55"/><stop offset="1" stop-color="#cfd8ff" stop-opacity="0"/></radialGradient>
        <linearGradient id="cometTail" x1="{TAIL0[0]}" y1="{TAIL0[1]}" x2="{HEAD[0]}" y2="{HEAD[1]}" gradientUnits="userSpaceOnUse">
          <stop offset="0" stop-color="#cfd8ff" stop-opacity="0"/><stop offset="1" stop-color="#eef1ff" stop-opacity=".55"/>
        </linearGradient>
        <radialGradient id="meteorLit" cx=".9" cy=".1" r=".65">
          <stop offset="0" stop-color="#fff4dc"/><stop offset=".35" stop-color="#ffb26a" stop-opacity=".85"/><stop offset=".7" stop-color="#ff7a3a" stop-opacity=".25"/><stop offset="1" stop-color="#ff7a3a" stop-opacity="0"/>
        </radialGradient>
        <linearGradient id="road" gradientUnits="userSpaceOnUse" x1="0" y1="196" x2="0" y2="520">
          <stop offset="0" stop-color="#c2a6a0" stop-opacity=".45"/><stop offset=".7" stop-color="#c99a48" stop-opacity=".8"/><stop offset="1" stop-color="#c8963e" stop-opacity=".92"/>
        </linearGradient>
        <linearGradient id="wood" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8a6248"/><stop offset="1" stop-color="#5a3c2e"/></linearGradient>
        <radialGradient id="cometHead"><stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset=".3" stop-color="#e6ebff" stop-opacity=".7"/><stop offset="1" stop-color="#cfd8ff" stop-opacity="0"/></radialGradient>
        <radialGradient id="ember"><stop offset="0" stop-color="#ffb347" stop-opacity=".8"/><stop offset="1" stop-color="#ff7a12" stop-opacity="0"/></radialGradient>
        <radialGradient id="lamp"><stop offset="0" stop-color="#ffd27a" stop-opacity=".9"/><stop offset="1" stop-color="#ffb347" stop-opacity="0"/></radialGradient>
        <linearGradient id="trail" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stop-color="#26318a"/><stop offset=".45" stop-color="#5a4fb0"/><stop offset=".8" stop-color="#e98a6a"/><stop offset="1" stop-color="#ffd09a"/>
        </linearGradient>
        <linearGradient id="ground" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#171c60"/><stop offset="1" stop-color="#0a0d3a"/></linearGradient>
        <linearGradient id="mist" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd2a8" stop-opacity="0"/><stop offset=".5" stop-color="#ffd2a8" stop-opacity=".10"/><stop offset="1" stop-color="#ffd2a8" stop-opacity="0"/></linearGradient>
      </defs>

      <rect width="520" height="600" fill="url(#sky)"/>
      <g fill="#fff">
        <circle cx="34" cy="28" r="1.2" opacity=".6"/><circle cx="96" cy="74" r="1" opacity=".5"/>
        <circle cx="150" cy="22" r="1.4" opacity=".7"/><circle cx="210" cy="150" r="1" opacity=".5"/>
        <circle cx="270" cy="200" r="1.2" opacity=".5"/><circle cx="18" cy="140" r="1" opacity=".4"/>
        <circle cx="500" cy="30" r="1.2" opacity=".6"/><circle cx="496" cy="300" r="1" opacity=".4"/>
        <circle cx="262" cy="290" r="1" opacity=".4"/><circle cx="470" cy="120" r="1" opacity=".5"/>
      </g>

      <!-- Celestial chart: ecliptic arc with degree ticks, and faint asterism lines -->
      <g fill="none" stroke="#e8ddff" stroke-opacity=".13" stroke-width=".7">
        <path d="M{E0[0]},{E0[1]} Q{E1[0]},{E1[1]} {E2[0]},{E2[1]}"/>
        <path d="{ticks}"/>
      </g>
      <polyline points="{asterism}" fill="none" stroke="#dfe5ff" stroke-opacity=".14" stroke-width=".6"/>

      <!-- Meta-regression: a comet whose straight tail is the regression line, asteroids sized by weight in its wake -->
      <polygon points="{TAIL0[0]-4},{TAIL0[1]-10} {HEAD[0]+2},{HEAD[1]-4} {HEAD[0]-2},{HEAD[1]+4} {TAIL0[0]+6},{TAIL0[1]+10}" fill="url(#cometTail)" opacity=".45"/>
      <polygon points="{TAIL0[0]},{TAIL0[1]-1} {HEAD[0]+1},{HEAD[1]-1.6} {HEAD[0]-1},{HEAD[1]+1.6} {TAIL0[0]},{TAIL0[1]+1}" fill="url(#cometTail)"/>
      <circle cx="{HEAD[0]+5}" cy="{HEAD[1]-4}" r="16" fill="url(#ember)" opacity=".55"/>
      <polygon points="{meteor}" fill="#3b3580"/>
      <polygon points="{meteor}" fill="url(#meteorLit)"/>
      <circle cx="{HEAD[0]-3}" cy="{HEAD[1]+2.5}" r="2.2" fill="#262262" opacity=".8"/>
      <circle cx="{HEAD[0]+1.5}" cy="{HEAD[1]+5}" r="1.4" fill="#262262" opacity=".7"/>
      <g>
        {roids}
      </g>

      <!-- Forest plot: square stars with flares for whiskers, hanging on the sun's ray -->
      <rect x="367" y="40" width="6" height="360" fill="url(#ray)"/>
      <g>
        {forest}
      </g>

      <!-- Pooled diamond: the setting sun -->
      <circle cx="370" cy="398" r="230" fill="url(#sunGlow)"/>
      <polygon points="300,398 370,366 440,398 370,430" fill="url(#sun)"/>

      <!-- Funnel plot: the mountain, with tree clusters tight at the summit and spreading toward its foot -->
      <polygon points="150,196 -40,470 340,470" fill="url(#mtn)"/>
      <!-- contour-enhanced funnel bands: lightest inside, stepping darker outward -->
      <polygon points="150,196 4,470 296,470" fill="#8a90ee" fill-opacity=".11"/>
      <polygon points="150,196 46,470 254,470" fill="#8a90ee" fill-opacity=".12"/>
      <polygon points="150,196 88,470 212,470" fill="#a0a6ff" fill-opacity=".14"/>
      <!-- shaded right half keeps the form -->
      <polygon points="150,196 150,470 340,470" fill="#05082a" fill-opacity=".26"/>
      <g fill="none" stroke="#c9ccff" stroke-opacity=".1" stroke-width=".6" stroke-linecap="round">
                <path d="M70,380 l16,-6 M42,430 l20,-5 M98,350 l10,-3 M176,300 l14,6 M196,380 l18,7 M226,420 l14,6"/>
      </g>
      <!-- snow cap -->
      <polygon points="150,196 167,220.5 162,226 158,223 153,236 148,227 142,232 138,225 133,229 130.7,224" fill="#aeb2f2"/>
      <polygon points="150,196 167,220.5 162,226 158,223 153,236 152,214" fill="#05082a" fill-opacity=".28"/>
      <polygon points="150,196 340,470 328,470" fill="#ff9a5a" fill-opacity=".12"/>
      <g>{trees}</g>

      <!-- Far hills and distant tree line -->
      <path d="M0,452 C 80,430 160,446 250,440 C 340,434 420,418 520,428 L520,600 L0,600 Z" fill="#1a1d5e"/>
      <g fill="#14174f">
        <polygon points="232,428 226,446 238,446"/><polygon points="246,424 239,446 253,446"/>
        <polygon points="262,430 256,446 268,446"/><polygon points="440,412 433,432 447,432"/>
        <polygon points="456,408 448,430 464,430"/><polygon points="474,414 467,432 481,432"/>
        <polygon points="492,410 484,430 500,430"/><polygon points="510,416 503,434 517,434"/>
      </g>
      <rect x="0" y="420" width="520" height="70" fill="url(#mist)"/>
      <path d="M0,480 C 60,470 200,462 520,470 L520,600 L0,600 Z" fill="url(#ground)"/>

      <!-- SROC: the river, reflecting the sky; star glints are the studies, the brightest is the summary point -->
      <path d="{TRAIL}" fill="url(#trail)"/>
      <path d="M{MID[0][0][0]},{MID[0][0][1]} C{MID[0][1][0]},{MID[0][1][1]} {MID[0][2][0]},{MID[0][2][1]} {MID[0][3][0]},{MID[0][3][1]} C{MID[1][1][0]},{MID[1][1][1]} {MID[1][2][0]},{MID[1][2][1]} {MID[1][3][0]},{MID[1][3][1]}" fill="none" stroke="#fff" stroke-opacity=".08" stroke-width="2" filter="url(#soft)"/>
      <path d="{TRAIL}" fill="none" stroke="#0a0d3a" stroke-opacity=".35" stroke-width="1"/>
      {glints}
      <g transform="translate({sx},{sy}) rotate(-16) scale(1.55)">
        <ellipse rx="14" ry="6.4" fill="none" stroke="#fff6dc" stroke-opacity=".35" stroke-width=".6" stroke-dasharray="1.6 2.2"/>
        <ellipse cy="1.8" rx="8.6" ry="4.2" fill="#05072a" fill-opacity=".35"/>
        <ellipse rx="7.2" ry="3.7" fill="none" stroke="#efe6d6" stroke-width="3.1"/>
        <ellipse rx="7.2" ry="3.7" fill="none" stroke="#ff6f1a" stroke-width="3.1" stroke-dasharray="4.5 4.5" stroke-dashoffset="2.2"/>
        <ellipse rx="7.2" ry="3.7" fill="none" stroke="#05072a" stroke-opacity=".25" stroke-width="1.2" transform="translate(0,.9)"/>
        <ellipse rx="7.4" ry="3.9" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width=".5" transform="translate(0,-.8)"/>
        <circle r="4" fill="url(#lamp)" opacity=".8"/>
        <circle r="1" fill="#fff6dc"/>
      </g>

      <!-- Shrubs and grass tufts in the near foreground -->
      <defs>
        <g id="shrub">
          <path d="M-14,0 L-12.6,-4 L-11,-2.4 L-9.4,-8 L-7,-3.2 L-5,-10.6 L-2.4,-4.2 L0,-12 L2.4,-4.6 L4.8,-10 L6.8,-3.6 L9,-8.2 L10.8,-3 L12.6,-5.6 L14,0 Z" fill="#141a52"/>
          <path d="M-9.4,-8 L-7,-3.2 L-8.4,-3 Z M-5,-10.6 L-2.4,-4.2 L-4,-4 Z M0,-12 L2.4,-4.6 L.8,-4.4 Z" fill="#ff9a5a" fill-opacity=".1"/>
        </g>
        <g id="tuft" stroke="#1c2367" stroke-width=".8" stroke-linecap="round" fill="none">
          <path d="M0,0 q-1,-3 -3,-5 M0,0 q0,-4 1,-6 M0,0 q1,-2 4,-4"/>
        </g>
      </defs>
      <use href="#shrub" transform="translate(128,592)"/>
      <use href="#shrub" transform="translate(92,566) scale(.8)"/>
      <use href="#tuft" transform="translate(150,560)"/><use href="#tuft" transform="translate(186,580) scale(1.2)"/>
      <use href="#tuft" transform="translate(318,552)"/><use href="#tuft" transform="translate(96,548) scale(.8)"/>
      <use href="#tuft" transform="translate(342,586) scale(1.1)"/>

      <g transform="translate(236,534) scale(1.75) translate(-240,-511)">
      <!-- The researcher's camp -->
      <circle cx="212" cy="514" r="22" fill="url(#ember)" opacity=".55"/>
      <g>
        <ellipse cx="212" cy="519" rx="6.5" ry="1.6" fill="#05072a" fill-opacity=".5"/>
        <g fill="#4a4a78"><ellipse cx="206.2" cy="518.6" rx="1.4" ry=".9"/><ellipse cx="217.8" cy="518.6" rx="1.4" ry=".9"/><ellipse cx="212" cy="520" rx="1.4" ry=".9"/></g>
        <path d="M207.5,519 L216.5,516.4 M207.5,516.4 L216.5,519" stroke="#5a3a26" stroke-width="1.3" stroke-linecap="round"/>
        <path d="M212,509.5 C214.6,512.6 215.2,515 212,517.6 C208.8,515 209.4,512.6 212,509.5 Z" fill="#ff7a1a"/>
        <path d="M212,512.4 C213.4,514 213.6,515.6 212,517.2 C210.4,515.6 210.6,514 212,512.4 Z" fill="#ffd27a"/>
        <circle cx="214.5" cy="507" r=".45" fill="#ffd27a"/><circle cx="210.6" cy="504.6" r=".35" fill="#ffb347"/>
      </g>
      <!-- Log seat by the fire -->
      <g transform="translate(198,521)">
        <ellipse cx="0" cy=".5" rx="7" ry="1" fill="#05072a" fill-opacity=".45"/>
        <rect x="-6" y="-2.8" width="12" height="3.2" rx="1.6" fill="#6a4632"/>
        <rect x="-6" y="-2.8" width="12" height="1.1" rx=".55" fill="#ff9a5a" fill-opacity=".3"/>
        <ellipse cx="6" cy="-1.2" rx="1" ry="1.6" fill="#c9905e"/>
        <path d="M-4,-1 h6" stroke="#4a3022" stroke-width=".3"/>
      </g>
      <!-- Open star atlas on the grass -->
      <g transform="translate(225,526) rotate(-6) scale(1.35)">
        <path d="M-6,0 L0,1 L0,-3.4 L-6,-4.4 Z" fill="#f1e4c8"/><path d="M6,0 L0,1 L0,-3.4 L6,-4.4 Z" fill="#e2d2b2"/>
        <g fill="#3a3f8e"><circle cx="-4" cy="-2.6" r=".35"/><circle cx="-2.2" cy="-1.4" r=".35"/><circle cx="-1" cy="-2.8" r=".3"/></g>
        <path d="M-4,-2.6 L-2.2,-1.4 L-1,-2.8" stroke="#3a3f8e" stroke-width=".2" fill="none"/>
        <path d="M1.6,-2.8 h3 M1.6,-1.8 h2.4 M1.6,-.8 h2.8" stroke="#8a7a62" stroke-width=".25"/>
      </g>
      <!-- Celestial globe on a stand -->
      <g transform="translate(294,506.8) scale(1.55)">
        <ellipse cx="0" cy=".2" rx="3" ry=".5" fill="#05072a" fill-opacity=".45"/>
        <path d="M-2,0 h4 M0,0 v-1.6" stroke="#8a6a3e" stroke-width=".7" stroke-linecap="round"/>
        <circle cy="-4.4" r="2.7" fill="#2c3a8e"/>
        <circle cy="-4.4" r="2.7" fill="none" stroke="#e0bb6e" stroke-width=".35"/>
        <path d="M-2.7,-4.4 h5.4 M0,-7.1 q1.6,2.7 0,5.4" stroke="#e0bb6e" stroke-width=".25" fill="none"/>
        <circle cx="-1" cy="-5.4" r=".25" fill="#fff6dc"/><circle cx=".9" cy="-3.6" r=".25" fill="#fff6dc"/><circle cx="1.2" cy="-5.6" r=".2" fill="#fff6dc"/>
      </g>

      <!-- Crate -->
      <g>
        <ellipse cx="282" cy="513.8" rx="10.5" ry="1.4" fill="#05072a" fill-opacity=".45"/>
        <rect x="274.5" y="502.5" width="15" height="11" rx=".6" fill="#6a4632"/>
        <rect x="274.5" y="502.5" width="5" height="11" fill="#ff9a5a" fill-opacity=".2"/>
        <path d="M274.5,506.2 h15 M274.5,509.9 h15" stroke="#3a2820" stroke-width=".4"/>
        <path d="M275.3,502.5 v11 M288.7,502.5 v11" stroke="#4a3022" stroke-width=".6"/>
        <!-- mug -->
        <rect x="276.4" y="499.6" width="2.6" height="2.9" rx=".35" fill="#e8e2d4"/>
        <path d="M279,500.3 a.8,.9 0 0 1 0,1.6" fill="none" stroke="#e8e2d4" stroke-width=".4"/>
        <!-- stethoscope: earpieces resting on the lid, tubing hanging in a loop, chest piece at the side -->
        <path d="M279.6,502.2 h4.2" stroke="#c9cede" stroke-width=".8" stroke-linecap="round"/>
        <circle cx="280" cy="502.3" r=".45" fill="#2a2e44"/><circle cx="283.4" cy="502.3" r=".45" fill="#2a2e44"/>
        <path d="M281.7,502.5 C281.6,507.4 284.6,509.4 286.4,506.6 C287.4,505 287.8,503.2 287.8,502.5" fill="none" stroke="#2a2e44" stroke-width="1.25" stroke-linecap="round"/>
        <path d="M287.8,502.5 C289.4,504.4 290.4,507.6 290.2,509.6" fill="none" stroke="#2a2e44" stroke-width="1.15" stroke-linecap="round"/>
        <circle cx="290.2" cy="511" r="1.8" fill="#d4d8e6" stroke="#7d8298" stroke-width=".35"/>
        <!-- lantern -->
        <circle cx="286.4" cy="499.8" r="6" fill="url(#lamp)" opacity=".75"/>
        <path d="M285,502.5 h2.8 l-.3,-3.8 h-2.2 Z" fill="#ffd27a"/>
        <path d="M284.8,498.7 h3.2 M285.4,498.7 q1,-1.7 2,0 M284.8,502.5 h3.2" stroke="#2a2030" stroke-width=".45" fill="none"/>
      </g>
      <!-- Clipboard with a tiny forest plot, leaning on the crate -->
      <g transform="translate(272.4,513.6) rotate(-10) scale(1.35)">
        <rect x="-2.6" y="-7.4" width="5.2" height="7.4" rx=".4" fill="#8a6248"/>
        <rect x="-2.1" y="-6.6" width="4.2" height="6.2" fill="#f4eee2"/>
        <rect x="-.9" y="-7.8" width="1.8" height=".9" rx=".2" fill="#b9bfd2"/>
        <path d="M-1.6,-5.4 h2 M-1,-4.4 h2.2 M-1.8,-3.4 h1.8 M-.6,-2.4 h2" stroke="#2c3170" stroke-width=".3"/>
        <path d="M.2,-6 v4.6" stroke="#2c3170" stroke-width=".15"/>
        <path d="M-.5,-1.2 l.6,-.4 l.6,.4 l-.6,.4 Z" fill="#ff7a12"/>
      </g>
      <!-- Sextant standing on its arc -->
      <g transform="translate(296,518.6) rotate(-6) scale(.9)" stroke-linecap="round">
        <path d="M0,-11 L-5,-1.4 M0,-11 L5,-1.4" stroke="#c9a05a" stroke-width=".8"/>
        <path d="M-5.2,-1.6 Q0,1.2 5.2,-1.6" fill="none" stroke="#e0bb6e" stroke-width="1.2"/>
        <path d="M-3.6,-.8 l.2,-.9 M-1.8,-.3 l.1,-.9 M0,-.1 v-.9 M1.8,-.3 l-.1,-.9 M3.6,-.8 l-.2,-.9" stroke="#8a6a3e" stroke-width=".25"/>
        <path d="M0,-11 L1.8,-.4" stroke="#8a6a3e" stroke-width=".7"/>
        <path d="M-1.4,-7.6 L-3.4,-3.8" stroke="#5a4226" stroke-width="1.4"/>
        <rect x="-1" y="-11.6" width="2" height="1.2" rx=".2" fill="#9fb6d8"/>
        <circle cx="0" cy="-11" r=".8" fill="#e0bb6e"/>
      </g>
      <!-- A researcher in a white coat at the end of the path, eye to a brass telescope on a tripod -->
      <g transform="translate(240,511) scale(1.3)" stroke-linecap="round" stroke-linejoin="round">
        <ellipse cx="8" cy=".4" rx="12" ry="1.3" fill="#05072a" fill-opacity=".45"/>
        <!-- tripod and tapered telescope -->
        <path d="M14,-27.6 L9.5,0 M14,-27.6 L14.6,.3 M14,-27.6 L19.5,0" stroke="#8a6a4a" stroke-width=".8"/>
        <path d="M14,-27.4 L14,-28.4" stroke="#3a2a24" stroke-width="1.6"/>
        <polygon points="6.8,-25.3 21.8,-34.6 23.2,-32.2 7.6,-23.9" fill="#9a7646"/>
        <path d="M7,-24.9 L22.2,-33.9" stroke="#f0d39a" stroke-opacity=".7" stroke-width=".45"/>
        <path d="M21.75,-31.2 L20.25,-33.8" stroke="#5a4226" stroke-width="1.2"/>
        <path d="M7.2,-24.6 L6.2,-24" stroke="#1a1428" stroke-width="1.1"/>
        <!-- legs and shoes -->
        <path d="M-1.6,-7.8 L-1.9,-.7 M2.4,-7.8 L2.8,-.7" stroke="#6a7098" stroke-width="1.9"/>
        <path d="M3.2,-7.8 L3.6,-.9" stroke="#e8b48a" stroke-opacity=".55" stroke-width=".45"/>
        <path d="M-3,-.4 h2.4 M2,-.4 h2.6" stroke="#4a2e22" stroke-width="1.2"/>
        <!-- neck, then the coat over it -->
        <path d="M2.7,-22.8 L2.4,-21" stroke="#d9a884" stroke-width="1.3"/>
        <path d="M-1.4,-21.4 C-2.4,-21 -2.8,-18 -2.9,-14 L-3.8,-7.6 L4.8,-7.6 L4.2,-14 C4.1,-17.5 4.4,-20.6 3.4,-21.5 Q1,-22.2 -1.4,-21.4 Z" fill="#eef0f7"/>
        <path d="M3.4,-21.5 C4.4,-20.6 4.1,-17.5 4.2,-14 L4.8,-7.6 L3.6,-7.6 L3.1,-14 C3,-17.5 3.2,-20.4 2.6,-21.4 Z" fill="#ffc890" fill-opacity=".7"/>
        <path d="M1.4,-21.5 L2.2,-19.6 L2.9,-21.4 Z" fill="#3a4a8a"/>
        <g stroke="#b9bfd2" stroke-width=".35" fill="none">
          <path d="M1,-21.6 L2.2,-18.6 L3.2,-21.4 M2.2,-18.6 L2.2,-15.5 L2.6,-7.6"/>
          <path d="M-.6,-11.6 h2 M-3,-10.4 L-3.5,-7.6"/>
        </g>
        <path d="M1.3,-21.3 L1.6,-17.2" stroke="#3a6ad6" stroke-width=".3"/>
        <rect x="1" y="-17.4" width="1.3" height="1.6" rx=".2" fill="#e8f0ff" stroke="#3a6ad6" stroke-width=".2"/>
        <!-- head with ear and hair, eye at the eyepiece -->
        <circle cx="3.6" cy="-25.2" r="2.4" fill="#d9a884"/>
        <ellipse cx="3" cy="-25" rx=".5" ry=".7" fill="#c08a68"/>
        <path d="M1.3,-24.6 C1,-27.4 4.6,-28.4 6,-26.4 C4.8,-26.9 3.6,-26.6 3.4,-25.6 C3.2,-24.7 2.6,-23.6 1.6,-23.4 Z" fill="#1a1428"/>
        <!-- near arm: elbow dropped, hand steadying the tube -->
        <path d="M2.6,-20.4 L6.6,-20.2 L9.6,-26" fill="none" stroke="#b9bfd2" stroke-width="2.1"/>
        <path d="M2.6,-20.4 L6.6,-20.2 L9.6,-26" fill="none" stroke="#eef0f7" stroke-width="1.6"/>
        <circle cx="10" cy="-26.4" r=".85" fill="#d9a884"/>
      </g>

      </g>

      <!-- Foreground forest -->
      {fg_pines}
      <!-- Foreground knoll under the pines -->
      <path d="M318,600 C 352,580 410,568 470,570 C 492,571 510,574 520,576 L520,600 Z" fill="#0b0e3a"/>
      <path d="M326,595 C 358,579 410,569 470,571 C 492,572 510,575 520,577" fill="none" stroke="#3a3f9e" stroke-opacity=".45" stroke-width="1"/>
      <g>
        <path d="M368,588 C 368,580 376,575 385,576 C 394,577 399,583 398,590 Z" fill="#1a1f5a"/>
        <path d="M371,584 C 373,579 379,577 385,577.6" fill="none" stroke="#6a70c0" stroke-opacity=".5" stroke-width=".9" stroke-linecap="round"/>
        <path d="M376,590 C 380,586 386,585 392,587" fill="none" stroke="#0b0e3a" stroke-opacity=".6" stroke-width=".7"/>
      </g>
      <g fill="none" stroke="#2a3070" stroke-width="1" stroke-linecap="round">
        <path d="M430,578 q-4,-6 -10,-8 M430,578 q-1,-8 -4,-12 M430,578 q2,-8 6,-11 M430,578 q5,-5 11,-6"/>
        <path d="M486,580 q-3,-5 -8,-7 M486,580 q0,-7 -2,-10 M486,580 q3,-6 7,-8"/>
      </g>
      <use href="#tuft" transform="translate(404,582) scale(1.3)"/><use href="#tuft" transform="translate(458,584) scale(1.4)"/>
      <use href="#tuft" transform="translate(352,592) scale(1.1)"/><use href="#tuft" transform="translate(508,588) scale(1.2)"/>
      <g fill="#fff3a8">
        <circle cx="414" cy="560" r=".9" opacity=".8"/><circle cx="470" cy="548" r=".8" opacity=".6"/><circle cx="378" cy="566" r=".7" opacity=".7"/>
      </g>
    </svg>
  </div>
</div>
</body>
</html>
"""
# Only the output boundary changes the approved drawing/template.
html = re.sub(r'<p class="p [^" ]+">.*?</p>', '', html)
html = html.replace('background: #1e1e1e; padding: 40px;', 'background: transparent; padding: 0;')
html = re.sub(r'box-shadow: [^;]+;', '', html)
logo = ROOT / "src/rc_metastudio/images/rc-metastudio-splash-logo.png"
html = html.replace('../../../src/rc_metastudio/images/rc-metastudio-splash-logo.png',
                    'data:image/png;base64,' + base64.b64encode(logo.read_bytes()).decode())

def main():
    output = ROOT / "src/rc_metastudio/images/splash"
    output.mkdir(parents=True, exist_ok=True)
    browser = os.environ.get("RCMS_CHROMIUM") or shutil.which("msedge") or shutil.which("chromium")
    if not browser:
        browser = str(Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe")
    with tempfile.TemporaryDirectory(prefix="rcms-splash-") as temporary:
        page = Path(temporary) / "splash.html"
        page.write_text(html, encoding="utf-8")
        if len(sys.argv) > 1:
            Path(sys.argv[1]).write_text(html, encoding="utf-8")
        for scale in (1, 2):
            target = output / ("splash.png" if scale == 1 else "splash@2x.png")
            subprocess.run([browser, "--headless", "--no-sandbox", "--disable-gpu",
                            "--hide-scrollbars", "--no-first-run",
                            "--default-background-color=00000000", "--window-size=960,600",
                            f"--force-device-scale-factor={scale}",
                            f"--user-data-dir={temporary}/profile-{scale}",
                            f"--screenshot={target}", page.as_uri()], check=True)
            print(target)

if __name__ == "__main__":
    main()
