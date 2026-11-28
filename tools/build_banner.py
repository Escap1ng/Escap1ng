#!/usr/bin/env python3
"""Build the profile title page (light/dark).

Run: python tools/build_banner.py

A letterpress title page with a printer's device: the astrolabe engraved above
the wordmark, no ground of its own, so the page sits on GitHub's paper like the
contribution sheet below it. One spot colour (green) for the bloom, the arcs and
the hairlines; everything else is ink.

The wordmark is Cormorant SemiBold in tracked capitals. Cormorant's figure 1 is
only 62% of cap height, which reads as a subscript in a wordmark, so it is drawn
at cap height here.

On load the device surfaces, its rings trace themselves, the echoes drift and
the wordmark rises letter by letter. All CSS, so prefers-reduced-motion rests.
"""
import math

from plates import F, T, ROOT, centred_rect, plate

NAME = "ESCAP1NG"
MOTTO = "Altiora petamus"
CAPTION = "Independent developer · Hangzhou"
ALT = "Escap1ng — Altiora petamus — Independent developer in Hangzhou"

THEMES = {
    "light": dict(ink="#191b1b", text="#4e5248", mute="#7d8075",
                  accent="#2f7a58", halo="#16a36a", halo_op=0.13,
                  ring="#191b1b", ring_op=0.34, arc_op=0.62,
                  hatch_op=0.13, numeral="#7d8075"),
    "dark": dict(ink="#f2f0e8", text="#c3c5ba", mute="#8d9086",
                 accent="#4fbf8f", halo="#16a36a", halo_op=0.20,
                 ring="#f2f0e8", ring_op=0.30, arc_op=0.62,
                 hatch_op=0.12, numeral="#8d9086"),
}

FITS = {"w": 720, "m": 460, "n": 290, "s": 236}

SETS = {
    "w": dict(margin=34, name_size=118, name_track=0.10, motto=25, caption=10.5,
              cy=146, radii=(30, 56, 82, 100), detail=True,
              gaps=(22, 18, 22, 18), air=(10, 22)),
    "m": dict(margin=26, name_size=86, name_track=0.09, motto=21, caption=10,
              cy=130, radii=(26, 48, 70, 86), detail=True,
              gaps=(20, 16, 20, 17), air=(10, 20)),
    "n": dict(margin=12, name_size=52, name_track=0.07, motto=19, caption=9,
              cy=136, radii=(24, 45, 66, 80), detail=False,
              gaps=(26, 20, 24, 22), air=(14, 22)),
    "s": dict(margin=9, name_size=42, name_track=0.06, motto=17, caption=8.5,
              cy=140, radii=(22, 42, 62, 76), detail=False,
              gaps=(28, 21, 25, 23), air=(16, 20)),
}

BASE_CSS = (
    "@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}"
    "@keyframes fade{from{opacity:0}to{opacity:1}}"
    "@keyframes emerge{from{clip-path:inset(100% 0 0 0)}to{clip-path:inset(0 0 0 0)}}"
    "@keyframes drift{from{transform:translate(0,2px)}to{transform:translate(0,-3px)}}"
    "@keyframes twinkle{0%,100%{opacity:0.08}50%{opacity:0.42}}"
    "@keyframes spin{to{transform:rotate(360deg)}}"
    ".rise{animation:rise .9s cubic-bezier(.2,.7,.3,1) both}"
    ".fade{animation:fade 1.1s ease-out both}"
    ".emerge{animation:emerge 1.5s cubic-bezier(.22,.61,.36,1) both}"
    ".float{animation:drift 9s ease-in-out infinite alternate}"
    ".twinkle{animation:twinkle 5s ease-in-out infinite}"
    ".orbit{animation:spin 300s linear infinite;transform-box:view-box}"
)

SERIF = F["serif"]
ONE_SCALE = SERIF.cap * SERIF.upem / 386.0


def char_size(ch, size):
    return size * (ONE_SCALE if ch == "1" else 1.0)


def mark_width(size, track):
    w = 0.0
    for ch in NAME:
        w += SERIF.adv[SERIF.glyph(ch)][0] * char_size(ch, size) / SERIF.upem + track * size
    return w - track * size


def wordmark(t, size, track, baseline):
    x = -mark_width(size, track) / 2
    out = []
    for i, ch in enumerate(NAME):
        out.append(T("50%", baseline, ch, "serif", char_size(ch, size), t["ink"],
                     "start", track=track, dx=x, lnum=True, cls="rise",
                     style=f"animation-delay:{0.35 + 0.055 * i:.2f}s"))
        x += SERIF.adv[SERIF.glyph(ch)][0] * char_size(ch, size) / SERIF.upem + track * size
    return "".join(out)


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.sin(a), cy - r * math.cos(a)


def arc_path(cx, cy, r, start, sweep):
    x1, y1 = polar(cx, cy, r, start)
    x2, y2 = polar(cx, cy, r, start + sweep)
    return f"M {x1:.1f} {y1:.1f} A {r} {r} 0 0 1 {x2:.1f} {y2:.1f}"


def ticks(cx, cy, r, colour, opacity):
    out = []
    for k in range(0, 360, 5):
        major = k % 30 == 0
        length = 8 if major else (4 if k % 10 == 0 else 2)
        x1, y1 = polar(cx, cy, r + 3, k)
        x2, y2 = polar(cx, cy, r + 3 + length, k)
        op = opacity if major else opacity * 0.45
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="{colour}" stroke-opacity="{op:.2f}" '
                   f'stroke-width="{1.2 if major else 0.8}"/>')
    return "".join(out)


def hatching(cx, cy, r0, r1, colour, opacity):
    """Engraved shading in the outer annulus: fine radial strokes."""
    out = []
    for k in range(0, 360, 3):
        x1, y1 = polar(cx, cy, r0 + 2, k)
        x2, y2 = polar(cx, cy, r1 - 2, k + 1.2)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="{colour}" stroke-opacity="{opacity}" stroke-width="0.7"/>')
    return "".join(out)


def echoes(cx, cy, r, colour):
    out = []
    for k, (f, op) in enumerate(((1.10, .10), (1.22, .07), (1.36, .05))):
        out.append(f'<g class="float" style="animation-delay:-{k * 2.2:.1f}s">'
                   f'<circle cx="{cx}" cy="{cy}" r="{r * f:.1f}" fill="none" stroke="{colour}" '
                   f'stroke-opacity="{op}" stroke-width="1" class="fade" '
                   f'style="animation-delay:{.7 + .14 * k:.2f}s"/></g>')
    return "".join(out)


NUMERALS = (("XII", 0), ("III", 90), ("VI", 180), ("IX", 270))
STARS = ((1.16, -0.86), (-0.62, -0.78), (1.18, 0.34), (-0.84, 0.52),
         (-0.30, -0.98), (0.82, 0.92), (-0.56, 0.88))


def device(t, s, key):
    """The astrolabe, drawn around a centred origin (x=50%, overflow visible)."""
    cy = s["cy"]
    cx = 0.0
    radii = s["radii"]
    r_out = radii[-1]
    parts = [f'<circle cx="{cx}" cy="{cy}" r="{r_out * 0.72:.1f}" fill="url(#bloomg)" '
             f'class="fade" style="animation-delay:.1s"/>',
             '<g class="emerge">',
             echoes(cx, cy, r_out, t["ring"])]
    parts.append(f'<g stroke="{t["ring"]}" stroke-opacity="{t["ring_op"] * 0.5:.2f}" '
                 f'stroke-width="0.8" class="fade" style="animation-delay:.4s">'
                 f'<line x1="{cx - r_out * 1.02:.1f}" y1="{cy}" x2="{cx + r_out * 1.02:.1f}" y2="{cy}"/>'
                 f'<line x1="{cx}" y1="{cy - r_out * 1.02:.1f}" x2="{cx}" y2="{cy + r_out * 1.02:.1f}"/></g>')
    for i, r in enumerate(radii):
        parts.append(f'<circle class="draw-ring r{key}{i}" cx="{cx}" cy="{cy}" r="{r}" '
                     f'fill="none" stroke="{t["ring"]}" '
                     f'stroke-opacity="{t["ring_op"] * (0.8 + 0.12 * i):.3f}" '
                     f'stroke-width="{1.6 if i == len(radii) - 1 else 1.0}"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_out + 5}" fill="none" stroke="{t["ring"]}" '
                 f'stroke-opacity="{t["ring_op"] * 0.55:.2f}" stroke-width="0.8" '
                 f'class="fade" style="animation-delay:.6s"/>')
    if s["detail"]:
        parts.append(f'<g class="fade" style="animation-delay:.9s">'
                     f'{hatching(cx, cy, radii[-2], r_out, t["ring"], t["hatch_op"])}</g>')
        parts.append(f'<g class="fade" style="animation-delay:1.05s">'
                     f'{ticks(cx, cy, r_out + 5, t["ring"], t["ring_op"])}</g>')
        for label, deg in NUMERALS:
            x, y = polar(cx, cy, r_out + 24, deg)
            parts.append(T(x, y + 3, label, "book", 9, t["numeral"], track=0.12,
                           cls="fade", style="animation-delay:1.15s"))
    for i, r in enumerate(radii[1:]):
        start = 41 + 73 * i
        parts.append(f'<g fill="none" stroke="{t["accent"]}" stroke-linecap="round" '
                     f'stroke-opacity="{t["arc_op"]}" class="orbit fade" '
                     f'stroke-width="{1.3 + 0.15 * i:.2f}" '
                     f'style="transform-origin:{cx}px {cy}px;animation-duration:{300 + 70 * i}s;'
                     f'animation-delay:{1 + 0.15 * i:.2f}s">')
        for j in range(3):
            a0 = (start + 19 + 45 * j + 23 * i) % 360
            sweep = 12 + 2 * i + 1.6 * j
            ex, ey = polar(cx, cy, r, a0 + sweep)
            parts.append(f'<path d="{arc_path(cx, cy, r, a0, sweep)}"/>'
                         f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{1.3 + 0.1 * i:.1f}" '
                         f'fill="{t["ink"]}" stroke="none" fill-opacity="0.55"/>')
        parts.append("</g>")
    parts.append(f'<g class="fade" style="animation-delay:.9s">'
                 f'<circle cx="{cx}" cy="{cy}" r="2.6" fill="{t["accent"]}"/>'
                 f'<circle cx="{cx}" cy="{cy}" r="9" fill="none" stroke="{t["accent"]}" '
                 f'stroke-opacity="0.45" stroke-width="1"/>'
                 f'<circle cx="{cx}" cy="{cy}" r="16" fill="none" stroke="{t["accent"]}" '
                 f'stroke-opacity="0.16" stroke-width="1"/></g>')
    parts.append("</g>")
    if s["detail"]:
        parts.append(f'<g fill="{t["ink"]}">')
        for i, (dx, dy) in enumerate(STARS):
            parts.append(f'<circle cx="{cx + dx * r_out * 0.98:.1f}" cy="{cy + dy * r_out * 0.98:.1f}" '
                         f'r="{0.8 + 0.15 * (i % 3):.1f}" class="twinkle" '
                         f'style="animation-delay:-{i * 1.4:.1f}s"/>')
        parts.append("</g>")
    return f'<svg x="50%" y="0" overflow="visible">{"".join(parts)}</svg>'


def setting(t, key):
    s = SETS[key]
    measure = FITS[key] - 2 * s["margin"]
    size = float(int(min(s["name_size"], measure / mark_width(1.0, s["name_track"]))))
    cap = SERIF.cap
    g1, g2, g3, g4 = s["gaps"]
    bottom = s["air"][1]

    mark = [device(t, s, key)]
    y = s["cy"] + s["radii"][-1] * 1.36 + g1 + cap * size
    mark.append(wordmark(t, size, s["name_track"], y))

    y += g2
    mark.append(f'<g class="fade" style="animation-delay:.8s">'
                + centred_rect(y, 56, 1.4, f'fill="{t["accent"]}" fill-opacity="0.85"')
                + '</g>')

    y += g3 + cap * s["motto"]
    mark.append(T("50%", y, MOTTO, "italic", s["motto"], t["text"],
                  cls="fade", style="animation-delay:.95s"))

    y += g4 + cap * s["caption"]
    mark.append(T("50%", y, CAPTION.upper(), "book", s["caption"], t["mute"],
                  track=0.28, cls="fade", style="animation-delay:1.1s"))

    return "".join(mark), y + bottom


def plate_css():
    out = [BASE_CSS]
    rings = []
    for key, s in SETS.items():
        for i, r in enumerate(s["radii"]):
            c = 2 * math.pi * r
            out.append(f"@keyframes r{key}{i}{{from{{stroke-dashoffset:{c:.1f}}}to{{stroke-dashoffset:0}}}}")
            out.append(f".r{key}{i}{{stroke-dasharray:{c:.1f};"
                       f"animation:r{key}{i} 1.6s cubic-bezier(.25,.6,.3,1) both;"
                       f"animation-delay:{0.2 + 0.18 * i:.2f}s}}")
            rings.append(f".r{key}{i}")
    out.append("@media (prefers-reduced-motion:reduce){.rise,.fade,.emerge,.float,"
               ".twinkle,.orbit,.draw-ring," + ",".join(rings) + "{animation:none}}")
    return "".join(out)


def defs(t):
    return (f'<defs><radialGradient id="bloomg" cx="0.5" cy="0.5" r="0.5">'
            f'<stop offset="0" stop-color="{t["halo"]}" stop-opacity="{t["halo_op"]}"/>'
            f'<stop offset="1" stop-color="{t["halo"]}" stop-opacity="0"/>'
            f'</radialGradient></defs>')


def build(theme):
    t = THEMES[theme]
    settings = {k: setting(t, k) for k in SETS}
    return plate(ALT, settings, rules=defs(t), css=plate_css())


def main():
    for theme in THEMES:
        svg = build(theme)
        path = ROOT / "assets" / f"banner-animated-{theme}.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"{path.name}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()