#!/usr/bin/env python3
"""Build the profile hero plate (light/dark).

Run: python tools/build_banner.py

A warm-paper or near-black ground with one green bloom, the astrolabe engraved
in hairlines. On load the instrument surfaces out of the ground (a mask wipe),
its rings draw themselves, the echoes drift, the wordmark rises letter by
letter and the bottom rule sweeps in. Everything is CSS, so the whole plate
comes to rest under prefers-reduced-motion.

The wordmark is Cormorant Light in tracked capitals: a plate title rather than
a logo.
"""
import math

from plates import F, T, ROOT, fit, plate

NAME = "ESCAP1NG"
KICKER = "Escaping Notes"
MOTTO = "Altiora petamus"
CAPTION = "Independent developer · Hangzhou"
DOMAIN = "escaping.top"
ALT = "Escap1ng — Altiora petamus — Independent developer in Hangzhou"

H = 344

THEMES = {
    "light": dict(
        bg0="#f8f5ec", bg1="#efebdf", ink="#191b1b", text="#4e5248",
        kicker="#6f7368", domain="#878a7e",
        halo="#16a36a", halo_op=0.14, rule_green="#2f7a58",
        ring="#191b1b", ring_op=0.30, arc="#2f7a58", arc_op=0.6,
        star="#191b1b", center="#2f7a58",
        grid="#191b1b", grid_op=0.045, border="#191b1b", border_op=0.13,
    ),
    "dark": dict(
        bg0="#121413", bg1="#080a09", ink="#f2f0e8", text="#c3c5ba",
        kicker="#9a9d93", domain="#7e8177",
        halo="#16a36a", halo_op=0.22, rule_green="#4fbf8f",
        ring="#f2f0e8", ring_op=0.26, arc="#4fbf8f", arc_op=0.6,
        star="#f2f0e8", center="#4fbf8f",
        grid="#f2f0e8", grid_op=0.035, border="#f2f0e8", border_op=0.12,
    ),
}

SETS = {
    "w": dict(margin=56, kicker_y=62, name_y=202, name_size=60, name_track=0.16,
              rule_y=220, motto_y=254, motto_size=26, caption_y=282, caption_size=10,
              domain_y=308, domain_size=9.5, centred=False,
              box=dict(x="57%", y="0", w="42%", h="100%", vb="0 0 400 420", cx=200, cy=205),
              radii=(40, 74, 108, 140), detail=True),
    "m": dict(margin=34, kicker_y=48, name_y=174, name_size=50, name_track=0.14,
              rule_y=190, motto_y=220, motto_size=22, caption_y=246, caption_size=9.5,
              domain_y=310, domain_size=9, centred=False,
              box=dict(x="56%", y="0", w="42%", h="100%", vb="0 0 320 420", cx=160, cy=205),
              radii=(30, 56, 82, 108), detail=True),
    "n": dict(margin=22, kicker_y=30, name_y=262, name_size=40, name_track=0.14,
              rule_y=None, motto_y=296, motto_size=18.5, caption_y=322, caption_size=9,
              domain_y=None, domain_size=9, centred=True,
              box=dict(x="0", y="0", w="100%", h="58%", vb="0 0 290 200", cx=145, cy=100),
              radii=(26, 48, 70, 92), detail=False),
    "s": dict(margin=17, kicker_y=26, name_y=256, name_size=34, name_track=0.12,
              rule_y=None, motto_y=288, motto_size=17, caption_y=312, caption_size=8.5,
              domain_y=None, domain_size=8.5, centred=True,
              box=dict(x="0", y="0", w="100%", h="58%", vb="0 0 236 170", cx=118, cy=85),
              radii=(22, 40, 58, 76), detail=False),
}

BASE_CSS = (
    "@keyframes rise{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:translateY(0)}}"
    "@keyframes fade{from{opacity:0}to{opacity:1}}"
    "@keyframes grow{from{opacity:0;transform:scaleX(0)}to{opacity:1;transform:scaleX(1)}}"
    "@keyframes emerge{from{clip-path:inset(100% 0 0 0)}to{clip-path:inset(0 0 0 0)}}"
    "@keyframes bloom{from{opacity:0}to{opacity:1}}"
    "@keyframes drift{from{transform:translate(0,2px)}to{transform:translate(0,-3px)}}"
    "@keyframes twinkle{0%,100%{opacity:0.08}50%{opacity:0.42}}"
    "@keyframes spin{to{transform:rotate(360deg)}}"
    ".rise{animation:rise 1s cubic-bezier(.2,.7,.3,1) both}"
    ".fade{animation:fade 1.2s ease-out both}"
    ".grow{animation:grow 1.4s cubic-bezier(.3,.65,.2,1) both;transform-origin:50% 50%}"
    ".emerge{animation:emerge 1.7s cubic-bezier(.22,.61,.36,1) both}"
    ".bloom{animation:bloom 2.2s ease-out both}"
    ".float{animation:drift 9s ease-in-out infinite alternate}"
    ".twinkle{animation:twinkle 5s ease-in-out infinite}"
    ".orbit{animation:spin 300s linear infinite;transform-box:view-box}"
)


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.sin(a), cy - r * math.cos(a)


def arc_path(cx, cy, r, start, sweep):
    x1, y1 = polar(cx, cy, r, start)
    x2, y2 = polar(cx, cy, r, start + sweep)
    return f"M {x1:.1f} {y1:.1f} A {r} {r} 0 0 1 {x2:.1f} {y2:.1f}"


def ticks(cx, cy, r, colour, opacity):
    out = []
    for k in range(0, 360, 10):
        major = k % 30 == 0
        length = 7 if major else 3
        x1, y1 = polar(cx, cy, r + 2, k)
        x2, y2 = polar(cx, cy, r + 2 + length, k)
        op = opacity if major else opacity * 0.5
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="{colour}" stroke-opacity="{op:.2f}" stroke-width="1"/>')
    return "".join(out)


def echoes(cx, cy, r, colour):
    out = []
    for k, (f, op) in enumerate(((1.08, .09), (1.18, .066), (1.30, .046), (1.44, .032))):
        out.append(f'<g class="float" style="animation-delay:-{k * 2.2:.1f}s">'
                   f'<circle cx="{cx}" cy="{cy}" r="{r * f:.1f}" fill="none" stroke="{colour}" '
                   f'stroke-opacity="{op}" stroke-width="1" class="fade" '
                   f'style="animation-delay:{.7 + .14 * k:.2f}s"/></g>')
    return "".join(out)


STARS = ((1.16, -0.86), (-0.62, -0.78), (1.18, 0.34), (-0.84, 0.52),
         (-0.30, -0.98), (0.82, 0.92), (-0.56, 0.88))


def art(t, s, key):
    b = s["box"]
    cx, cy = b["cx"], b["cy"]
    radii = s["radii"]
    r_out = radii[-1]
    parts = [f'<circle cx="{cx}" cy="{cy}" r="{r_out * 0.62:.1f}" fill="url(#bloomg)" '
             f'class="bloom" style="animation-delay:.1s"/>',
             '<g class="emerge">',
             echoes(cx, cy, r_out, t["ring"])]
    parts.append(f'<g stroke="{t["ring"]}" stroke-opacity="{t["ring_op"] * 0.55:.2f}" stroke-width="1" '
                 f'class="fade" style="animation-delay:.4s">'
                 f'<line x1="{cx - r_out * 1.04:.1f}" y1="{cy}" x2="{cx + r_out * 1.04:.1f}" y2="{cy}"/>'
                 f'<line x1="{cx}" y1="{cy - r_out * 1.04:.1f}" x2="{cx}" y2="{cy + r_out * 1.04:.1f}"/></g>')
    for i, r in enumerate(radii):
        parts.append(f'<circle class="draw-ring r{key}{i}" cx="{cx}" cy="{cy}" r="{r}" '
                     f'fill="none" stroke="{t["ring"]}" '
                     f'stroke-opacity="{t["ring_op"] * (0.8 + 0.12 * i):.3f}" stroke-width="1"/>')
    if s["detail"]:
        parts.append(f'<g class="fade" style="animation-delay:1.05s">'
                     f'{ticks(cx, cy, r_out, t["ring"], t["ring_op"])}</g>')
    for i, r in enumerate(radii[1:]):
        start = 41 + 73 * i
        parts.append(f'<g fill="none" stroke="{t["arc"]}" stroke-linecap="round" '
                     f'stroke-opacity="{t["arc_op"]}" class="orbit fade" '
                     f'style="transform-origin:{cx}px {cy}px;animation-duration:{300 + 70 * i}s;'
                     f'animation-delay:{1 + 0.15 * i:.2f}s">')
        for j in range(3):
            a0 = (start + 19 + 45 * j + 23 * i) % 360
            sweep = 12 + 2 * i + 1.6 * j
            ex, ey = polar(cx, cy, r, a0 + sweep)
            parts.append(f'<path d="{arc_path(cx, cy, r, a0, sweep)}" stroke-width="{1.2 + 0.15 * i:.2f}"/>'
                         f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{1.2 + 0.1 * i:.1f}" '
                         f'fill="{t["star"]}" stroke="none" fill-opacity="0.55"/>')
        parts.append("</g>")
    parts.append(f'<g class="fade" style="animation-delay:.9s">'
                 f'<circle cx="{cx}" cy="{cy}" r="2.6" fill="{t["center"]}"/>'
                 f'<circle cx="{cx}" cy="{cy}" r="9" fill="none" stroke="{t["center"]}" '
                 f'stroke-opacity="0.45" stroke-width="1"/>'
                 f'<circle cx="{cx}" cy="{cy}" r="16" fill="none" stroke="{t["center"]}" '
                 f'stroke-opacity="0.16" stroke-width="1"/></g>')
    parts.append("</g>")
    if s["detail"]:
        parts.append(f'<g fill="{t["star"]}">')
        for i, (dx, dy) in enumerate(STARS):
            parts.append(f'<circle cx="{cx + dx * r_out * 0.98:.1f}" cy="{cy + dy * r_out * 0.98:.1f}" '
                         f'r="{0.8 + 0.15 * (i % 3):.1f}" class="twinkle" '
                         f'style="animation-delay:-{i * 1.4:.1f}s"/>')
        parts.append("</g>")
    return (f'<svg x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" height="{b["h"]}" '
            f'viewBox="{b["vb"]}" preserveAspectRatio="xMidYMid meet" overflow="visible">'
            f'{"".join(parts)}</svg>')


def name_markup(t, s):
    size = s["name_size"]
    avail = s["fits"] - 2 * s["margin"] if s["centred"] else s["fits"] * 0.5 - s["margin"] - 10
    size = fit("thin", NAME, avail, size, s["name_track"])
    xs, width = F["thin"].positions(NAME, size, s["name_track"])
    lead = -width / 2 if s["centred"] else 0.0
    x0 = "50%" if s["centred"] else str(s["margin"])
    out = []
    for i, (ch, x) in enumerate(zip(NAME, xs)):
        out.append(T(x0, s["name_y"], ch, "thin", size, t["ink"], "start",
                     track=s["name_track"], dx=lead + x, lnum=True, cls="rise",
                     style=f"animation-delay:{0.3 + 0.06 * i:.2f}s"))
    return "".join(out)


def header(t, s):
    if s["centred"]:
        return ""
    m = s["margin"]
    return (f'<rect x="{m}" y="{s["kicker_y"] - 4}" width="15" height="1.4" fill="{t["rule_green"]}" '
            f'fill-opacity="0.9" class="fade" style="animation-delay:.15s"/>'
            + T(m + 26, s["kicker_y"], KICKER.upper(), "book", s["caption_size"], t["kicker"],
                "start", track=0.34, cls="fade", style="animation-delay:.18s"))


def body(t, s):
    m = s["margin"]
    if s["centred"]:
        return (T("50%", s["motto_y"], MOTTO, "italic", s["motto_size"], t["text"],
                  cls="fade", style="animation-delay:.9s")
                + T("50%", s["caption_y"], CAPTION.upper(), "book", s["caption_size"],
                    t["kicker"], track=0.26, cls="fade", style="animation-delay:1.05s"))
    return (f'<rect x="{m}" y="{s["rule_y"]}" width="30%" height="1" fill="{t["ring"]}" '
            f'fill-opacity="0.22" class="grow" style="animation-delay:.6s"/>'
            + T(m, s["motto_y"], MOTTO, "italic", s["motto_size"], t["text"],
                "start", cls="fade", style="animation-delay:.85s")
            + T(m + 1, s["caption_y"], CAPTION.upper(), "book", s["caption_size"], t["kicker"],
                "start", track=0.28, cls="fade", style="animation-delay:1s")
            + T("100%", s["domain_y"], DOMAIN, "book", s["domain_size"], t["domain"],
                "end", track=0.22, dx=-m, cls="fade", style="animation-delay:1.1s"))


def setting(t, key):
    s = dict(SETS[key], fits={"w": 720, "m": 460, "n": 290, "s": 236}[key])
    out = [header(t, s), art(t, s, key), name_markup(t, s), body(t, s)]
    return "".join(out), H


def plate_css():
    """Base motion plus one draw keyframe per ring, so the rings trace themselves."""
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
    out.append("@media (prefers-reduced-motion:reduce){.rise,.fade,.grow,.emerge,.bloom,.float,"
               ".twinkle,.orbit,.draw-ring," + ",".join(rings) + "{animation:none}}")
    return "".join(out)


def chrome(t):
    return (
        f'<defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{t["bg0"]}"/><stop offset="1" stop-color="{t["bg1"]}"/></linearGradient>'
        f'<radialGradient id="bloomg" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{t["halo"]}" stop-opacity="{t["halo_op"]}"/>'
        f'<stop offset="1" stop-color="{t["halo"]}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t["rule_green"]}" stop-opacity="0"/>'
        f'<stop offset="0.18" stop-color="{t["rule_green"]}" stop-opacity="0.85"/>'
        f'<stop offset="0.5" stop-color="{t["ink"]}" stop-opacity="0.55"/>'
        f'<stop offset="0.82" stop-color="{t["rule_green"]}" stop-opacity="0.85"/>'
        f'<stop offset="1" stop-color="{t["rule_green"]}" stop-opacity="0"/></linearGradient>'
        f'<radialGradient id="gridfade" cx="0.7" cy="0.45" r="0.8">'
        f'<stop offset="0" stop-color="#ffffff" stop-opacity="1"/>'
        f'<stop offset="0.6" stop-color="#ffffff" stop-opacity="0.5"/>'
        f'<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>'
        f'<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
        f'<path d="M 40 0 H 0 V 40" fill="none" stroke="{t["grid"]}" '
        f'stroke-opacity="{t["grid_op"]}" stroke-width="1"/></pattern>'
        f'<mask id="gridmask"><rect width="100%" height="100%" fill="url(#gridfade)"/></mask>'
        f'<filter id="grain" x="0" y="0" width="100%" height="100%">'
        f'<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/>'
        f'<feColorMatrix type="saturate" values="0"/></filter>'
        f'<clipPath id="card"><rect width="100%" height="100%" rx="16"/></clipPath>'
        f'</defs>'
        f'<g clip-path="url(#card)">'
        f'<rect width="100%" height="100%" fill="url(#bg)"/>'
        f'<rect width="100%" height="100%" fill="url(#grid)" mask="url(#gridmask)"/>'
        f'</g>'
    )


def over(t):
    return (
        f'<g clip-path="url(#card)">'
        f'<rect y="{H - 2}" width="100%" height="2" fill="url(#rule)" class="grow" '
        f'style="animation-delay:.2s"/></g>'
        f'<rect width="100%" height="100%" filter="url(#grain)" opacity="0.05" '
        f'style="mix-blend-mode:{"multiply" if t["bg0"].startswith("#f") else "overlay"}"/>'
        f'<rect x="0.5" y="0.5" width="100%" height="100%" rx="16" fill="none" '
        f'stroke="{t["border"]}" stroke-opacity="{t["border_op"]}"/>'
    )


def build(theme):
    t = THEMES[theme]
    settings = {k: setting(t, k) for k in SETS}
    return plate(ALT, settings, ground=None, rules=chrome(t), over=over(t), css=plate_css())


def main():
    for theme in THEMES:
        svg = build(theme)
        path = ROOT / "assets" / f"banner-animated-{theme}.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"{path.name}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
