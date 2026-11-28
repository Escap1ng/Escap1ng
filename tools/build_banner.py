#!/usr/bin/env python3
"""Build the profile hero plate (light/dark).

Run: python tools/build_banner.py

The manner follows the altiora-agent brand plate: a quiet ground, one green
halo, an engraved instrument drawn in hairlines, and the title set wide. Green
is an accent here, never a field. On load the rings draw themselves, the echoes
breathe, the letters rise and the rule sweeps in; everything settles under
prefers-reduced-motion.
"""
import math

from plates import F, T, ROOT, fit, hairline, plate

NAME = "Escap1ng"
KICKER = "Escaping Notes"
MOTTO = "Altiora petamus"
CAPTION = "Independent developer · Hangzhou"
DOMAIN = "escaping.top"
ALT = f"{NAME} — {MOTTO} — {CAPTION}"

H = 344

THEMES = {
    "light": dict(
        bg0="#f8f5ec", bg1="#efebdf", ink="#191b1b", text="#4e5248",
        kicker="#6f7368", mute="#7d8075", domain="#878a7e",
        halo="#16a36a", halo_op=0.13, rule_green="#2f7a58",
        grid="#191b1b", grid_op=0.045, border="#191b1b", border_op=0.13,
        ring="#191b1b", ring_op=0.30, arc="#2f7a58", arc_op=0.55,
        star="#191b1b", center="#2f7a58",
    ),
    "dark": dict(
        bg0="#121413", bg1="#080a09", ink="#f2f0e8", text="#c3c5ba",
        kicker="#9a9d93", mute="#8d9086", domain="#7e8177",
        halo="#16a36a", halo_op=0.22, rule_green="#4fbf8f",
        grid="#f2f0e8", grid_op=0.035, border="#f2f0e8", border_op=0.12,
        ring="#f2f0e8", ring_op=0.26, arc="#4fbf8f", arc_op=0.55,
        star="#f2f0e8", center="#4fbf8f",
    ),
}

# One composition per width class. `box` is the instrument's own nested SVG,
# placed as a share of the plate so it scales while the type does not.
SETS = {
    "w": dict(margin=56, kicker_y=64, name_y=188, name_size=68, name_track=0.03,
              rule_y=None, motto_y=230, motto_size=27, caption_y=258, caption_size=10.5,
              domain_y=308, domain_size=9.5, halo_y=326,
              box=dict(x="57%", y="0", w="42%", h="100%", vb="0 0 400 420", cx=200, cy=205),
              radii=(40, 74, 108, 140), detail=True, centred=False),
    "m": dict(margin=34, kicker_y=48, name_y=168, name_size=52, name_track=0.03,
              rule_y=184, motto_y=214, motto_size=22, caption_y=240, caption_size=9.5,
              domain_y=310, domain_size=9, halo_y=326,
              box=dict(x="56%", y="0", w="42%", h="100%", vb="0 0 320 420", cx=160, cy=205),
              radii=(30, 56, 82, 108), detail=True, centred=False),
    "n": dict(margin=22, kicker_y=30, name_y=250, name_size=42, name_track=0.03,
              rule_y=None, motto_y=284, motto_size=19, caption_y=310, caption_size=9,
              domain_y=None, domain_size=9, halo_y=None,
              box=dict(x="0", y="0", w="100%", h="58%", vb="0 0 290 200", cx=145, cy=100),
              radii=(26, 48, 70, 92), detail=False, centred=True),
    "s": dict(margin=17, kicker_y=26, name_y=244, name_size=36, name_track=0.03,
              rule_y=None, motto_y=276, motto_size=17, caption_y=300, caption_size=8.5,
              domain_y=None, domain_size=8.5, halo_y=None,
              box=dict(x="0", y="0", w="100%", h="58%", vb="0 0 236 170", cx=118, cy=85),
              radii=(22, 40, 58, 76), detail=False, centred=True),
}

CSS = (
    "@keyframes rise{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}"
    "@keyframes fade{from{opacity:0}to{opacity:1}}"
    "@keyframes grow{from{opacity:0;transform:scaleX(0)}to{opacity:1;transform:scaleX(1)}}"
    ".rise{animation:rise 1s cubic-bezier(.2,.7,.3,1) both}"
    ".fade{animation:fade 1.1s ease-out both}"
    ".grow{animation:grow 1.4s cubic-bezier(.3,.65,.2,1) both;transform-origin:50% 50%}"
    "@media (prefers-reduced-motion:reduce){.rise,.fade,.grow{animation:none}}"
)


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.sin(a), cy - r * math.cos(a)


def arc_path(cx, cy, r, start, sweep):
    x1, y1 = polar(cx, cy, r, start)
    x2, y2 = polar(cx, cy, r, start + sweep)
    return f"M {x1:.1f} {y1:.1f} A {r} {r} 0 0 1 {x2:.1f} {y2:.1f}"


def drawn_ring(cx, cy, r, colour, opacity, delay):
    """A circle that draws itself once, then stays."""
    c = 2 * math.pi * r
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{colour}" '
            f'stroke-opacity="{opacity}" stroke-width="1" '
            f'stroke-dasharray="{c:.1f} {c:.1f}" stroke-dashoffset="{c:.1f}">'
            f'<animate attributeName="stroke-dashoffset" from="{c:.1f}" to="0" dur="1.5s" '
            f'begin="{delay:.2f}s" fill="freeze"/></circle>')


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
    """Faint rings breathing outward: the instrument's own ripple."""
    out = []
    for k, (f, op) in enumerate(((1.08, .09), (1.19, .065), (1.32, .045), (1.47, .03))):
        rr = r * f
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{rr:.1f}" fill="none" stroke="{colour}" '
                   f'stroke-opacity="{op}" stroke-width="1">'
                   f'<animate attributeName="r" values="{rr:.1f};{rr * 1.05:.1f};{rr:.1f}" '
                   f'dur="{9 + 2 * k}s" begin="-{k * 2.2:.1f}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="stroke-opacity" values="{op};{op * 2.4:.3f};{op}" '
                   f'dur="{9 + 2 * k}s" begin="-{k * 2.2:.1f}s" repeatCount="indefinite"/>'
                   f'</circle>')
    return "".join(out)


STARS = ((1.16, -0.86), (-0.62, -0.78), (1.18, 0.34), (-0.84, 0.52),
         (-0.30, -0.98), (0.82, 0.92), (-0.56, 0.88))


def instrument(t, s):
    cx, cy = s["box"]["cx"], s["box"]["cy"]
    radii = s["radii"]
    r_out = radii[-1]
    parts = [echoes(cx, cy, r_out, t["ring"])]
    # crosshair, then the rings, drawn one after another
    parts.append(f'<g stroke="{t["ring"]}" stroke-opacity="{t["ring_op"] * 0.5:.2f}" stroke-width="1" '
                 f'class="fade" style="animation-delay:.5s">'
                 f'<line x1="{cx - r_out * 1.05:.1f}" y1="{cy}" x2="{cx + r_out * 1.05:.1f}" y2="{cy}"/>'
                 f'<line x1="{cx}" y1="{cy - r_out * 1.05:.1f}" x2="{cx}" y2="{cy + r_out * 1.05:.1f}"/></g>')
    for i, r in enumerate(radii):
        parts.append(drawn_ring(cx, cy, r, t["ring"], t["ring_op"] * (0.8 + 0.12 * i), 0.15 + 0.18 * i))
    if s["detail"]:
        parts.append(f'<g class="fade" style="animation-delay:1s">'
                     f'{ticks(cx, cy, r_out, t["ring"], t["ring_op"])}</g>')

    # three orbit arcs per ring, turning slowly
    for i, r in enumerate(radii[1:]):
        speed = 300 + 60 * i
        start = 41 + 73 * i
        parts.append(f'<g fill="none" stroke="{t["arc"]}" stroke-linecap="round" '
                     f'stroke-opacity="{t["arc_op"]}" transform="rotate({start} {cx} {cy})" '
                     f'class="fade" style="animation-delay:{1 + 0.15 * i:.2f}s">'
                     f'<animateTransform attributeName="transform" type="rotate" '
                     f'from="{start} {cx} {cy}" to="{start + 360} {cx} {cy}" '
                     f'dur="{speed}s" repeatCount="indefinite"/>')
        for j in range(3):
            a0 = (19 + 45 * j + 23 * i) % 360
            sweep = 12 + 2 * i + 1.6 * j
            ex, ey = polar(cx, cy, r, a0 + sweep)
            parts.append(f'<path d="{arc_path(cx, cy, r, a0, sweep)}" stroke-width="{1.2 + 0.15 * i:.2f}">'
                         f'<animate attributeName="stroke-opacity" values="{t["arc_op"]};0.15;{t["arc_op"]}" '
                         f'dur="{8 + i + j * 2}s" begin="-{(i * 2.6 + j) % 7:.1f}s" '
                         f'repeatCount="indefinite"/></path>'
                         f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{1.2 + 0.1 * i:.1f}" '
                         f'fill="{t["star"]}" stroke="none" fill-opacity="0.55"/>')
        parts.append("</g>")

    # soft halo and the centre
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r_out * 0.55:.1f}" fill="url(#halo)">'
        f'<animate attributeName="r" values="{r_out * 0.5:.1f};{r_out * 0.6:.1f};{r_out * 0.5:.1f}" '
        f'dur="7s" repeatCount="indefinite"/></circle>'
        f'<g class="fade" style="animation-delay:.9s">'
        f'<circle cx="{cx}" cy="{cy}" r="2.6" fill="{t["center"]}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="9" fill="none" stroke="{t["center"]}" '
        f'stroke-opacity="0.45" stroke-width="1"/>'
        f'<circle cx="{cx}" cy="{cy}" r="16" fill="none" stroke="{t["center"]}" '
        f'stroke-opacity="0.16" stroke-width="1"/></g>')

    if s["detail"]:
        parts.append(f'<g fill="{t["star"]}" class="fade" style="animation-delay:1.1s">')
        for i, (dx, dy) in enumerate(STARS):
            parts.append(f'<circle cx="{cx + dx * r_out * 0.98:.1f}" cy="{cy + dy * r_out * 0.98:.1f}" '
                         f'r="{0.8 + 0.15 * (i % 3):.1f}" opacity="0.22">'
                         f'<animate attributeName="opacity" values="0.1;0.45;0.1" '
                         f'dur="{3.4 + i * 0.7:.1f}s" begin="-{(i * 1.4) % 4:.1f}s" '
                         f'repeatCount="indefinite"/></circle>')
        parts.append("</g>")
    return "".join(parts)


def box_markup(t, s):
    b = s["box"]
    return (f'<svg x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" height="{b["h"]}" '
            f'viewBox="{b["vb"]}" preserveAspectRatio="xMidYMid meet" overflow="visible">'
            f'{instrument(t, s)}</svg>')


def name_markup(t, s, centred):
    size = s["name_size"]
    avail = (s["fits"] - 2 * s["margin"]) if centred else (s["fits"] * 0.56 - s["margin"] - 8)
    size = fit("serif", NAME, avail, size, s["name_track"])
    xs, width = F["serif"].positions(NAME, size, s["name_track"])
    lead = -width / 2 if centred else 0.0
    x0 = "50%" if centred else str(s["margin"])
    out = []
    for i, (ch, x) in enumerate(zip(NAME, xs)):
        out.append(T(x0, s["name_y"], ch, "serif", size, t["ink"], "start",
                     track=s["name_track"], dx=lead + x, cls="rise",
                     style=f"animation-delay:{0.22 + 0.06 * i:.2f}s"))
    return "".join(out)


def header(t, s, centred):
    m = s["margin"]
    if centred:
        return ""
    return (f'<rect x="{m}" y="{s["kicker_y"] - 4}" width="15" height="1.4" fill="{t["rule_green"]}" '
            f'fill-opacity="0.9" class="fade" style="animation-delay:.1s"/>'
            + T(m + 26, s["kicker_y"], KICKER.upper(), "book", s["caption_size"], t["kicker"],
                "start", track=0.34, cls="fade", style="animation-delay:.12s"))


def body(t, s, centred):
    m = s["margin"]
    out = []
    if centred:
        out.append(T("50%", s["motto_y"], MOTTO, "italic", s["motto_size"], t["text"],
                     cls="fade", style="animation-delay:.8s"))
        out.append(T("50%", s["caption_y"], CAPTION.upper(), "book", s["caption_size"],
                     t["caption"] if "caption" in t else t["kicker"], track=0.26,
                     cls="fade", style="animation-delay:.95s"))
        return "".join(out)
    out.append(f'<rect x="{m}" y="{s["rule_y"]}" width="34%" height="1" fill="{t["ring"]}" '
               f'fill-opacity="{t["ring_op"] * 0.6:.2f}" class="grow" style="animation-delay:.5s"/>')
    out.append(T(m, s["motto_y"], MOTTO, "italic", s["motto_size"], t["text"],
                 "start", cls="fade", style="animation-delay:.75s"))
    out.append(T(m + 1, s["caption_y"], CAPTION.upper(), "book", s["caption_size"], t["kicker"],
                 "start", track=0.28, cls="fade", style="animation-delay:.9s"))
    if s["domain_y"]:
        out.append(T("100%", s["domain_y"], DOMAIN, "book", s["domain_size"], t["domain"],
                     "end", track=0.22, dx=-m, cls="fade", style="animation-delay:1s"))
    return "".join(out)


def setting(t, key):
    s = dict(SETS[key], fits={"w": 720, "m": 460, "n": 290, "s": 236}[key])
    out = [header(t, s, s["centred"]),
           f'<g class="fade" style="animation-delay:.25s">{box_markup(t, s)}</g>',
           name_markup(t, s, s["centred"]),
           body(t, s, s["centred"])]
    return "".join(out), H


def chrome(t):
    return (
        f'<defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{t["bg0"]}"/><stop offset="1" stop-color="{t["bg1"]}"/></linearGradient>'
        f'<radialGradient id="halo" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{t["halo"]}" stop-opacity="{t["halo_op"]}"/>'
        f'<stop offset="1" stop-color="{t["halo"]}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t["rule_green"]}" stop-opacity="0"/>'
        f'<stop offset="0.18" stop-color="{t["rule_green"]}" stop-opacity="0.85"/>'
        f'<stop offset="0.5" stop-color="{t["ink"]}" stop-opacity="0.55"/>'
        f'<stop offset="0.82" stop-color="{t["rule_green"]}" stop-opacity="0.85"/>'
        f'<stop offset="1" stop-color="{t["rule_green"]}" stop-opacity="0"/></linearGradient>'
        f'<radialGradient id="gridfade" cx="0.72" cy="0.45" r="0.75">'
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
        f'style="animation-delay:.15s"/></g>'
        f'<rect width="100%" height="100%" filter="url(#grain)" opacity="0.05" '
        f'style="mix-blend-mode:{"multiply" if t["bg0"].startswith("#f") else "overlay"}"/>'
        f'<rect x="0.5" y="0.5" width="100%" height="100%" rx="16" fill="none" '
        f'stroke="{t["border"]}" stroke-opacity="{t["border_op"]}"/>'
    )


def build(theme):
    t = THEMES[theme]
    settings = {k: setting(t, k) for k in SETS}
    return plate(ALT, settings, ground=None, rules=chrome(t), over=over(t), css=CSS)


def main():
    for theme in THEMES:
        svg = build(theme)
        path = ROOT / "assets" / f"banner-animated-{theme}.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"{path.name}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
