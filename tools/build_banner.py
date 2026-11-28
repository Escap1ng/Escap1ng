#!/usr/bin/env python3
"""Build the profile hero plate (light/dark, animated).

Run: python tools/build_banner.py

The copy lives below. Type is set by tools/plates.py; the instrument is drawn
in its own nested SVG so it can scale like a picture while the type stays at
its designed size. Each of the four settings is a complete composition, and the
media query in the plate decides which one the reader sees.
"""
from plates import F, T, ROOT, fit, plate

NAME = "Escap1ng"
KICKER = "Escaping Notes"
MOTTO = "Altiora petamus"
CAPTION = "Independent developer · Hangzhou"
DOMAIN = "escaping.top"
ALT = f"{NAME} — {MOTTO} — {CAPTION}"

H = 364
ACCENT = "#16a36a"

THEMES = {
    "light": dict(
        bg0="#f6f9f6", bg1="#e8f0ea", ink="#10131a", kicker="#75837b",
        motto="#4e5f55", caption="#7d8b82", domain="#8a968d",
        rule="#0c0e12", rule_op=0.16, border="#d2dcd5",
        glow="#dcebe1", glow_op=0.9, vig="#dde6df", vig_op=0.5,
        grid="#5e7167", grid_op=0.06, ring="#16a36a", ring_op=0.22,
        accent=ACCENT, star="#1d2a23", halo="#16a36a", halo_op=0.38,
        grain_op=0.05, grain_blend="multiply",
    ),
    "dark": dict(
        bg0="#030604", bg1="#0a120e", ink="#edf3ee", kicker="#5d6f66",
        motto="#a9b7ae", caption="#7e8f86", domain="#5f7067",
        rule="#edf3ee", rule_op=0.15, border="#233229",
        glow="#0e2119", glow_op=0.7, vig="#000000", vig_op=0.5,
        grid="#a3c4b2", grid_op=0.05, ring="#16a36a", ring_op=0.3,
        accent=ACCENT, star="#edf3ee", halo="#3fbf8a", halo_op=0.5,
        grain_op=0.07, grain_blend="overlay",
    ),
}

# One composition per width class. `door` values are px from the left margin;
# `*_y` are baselines. The instrument box is placed as a share of the plate, so
# it scales with the width while everything else is set at a fixed size.
SETS = {
    "w": dict(margin=40, kicker_y=46, name_y=202, name_size=62, name_track=0.0,
              rule_y=220, motto_y=258, motto_size=27, caption_y=291,
              caption_size=11.5, domain_y=336, domain_size=11,
              box=dict(x="52%", y="4%", w="46%", h="92%", vb="0 0 400 336", cx=200, cy=168),
              radii=(38, 68, 98, 128), sparks=True, ticks=True),
    "m": dict(margin=30, kicker_y=42, name_y=188, name_size=52, name_track=0.0,
              rule_y=204, motto_y=240, motto_size=23, caption_y=271,
              caption_size=10.5, domain_y=334, domain_size=10.5,
              box=dict(x="54%", y="8%", w="44%", h="84%", vb="0 0 300 306", cx=150, cy=153),
              radii=(28, 50, 72, 94), sparks=True, ticks=True),
    "n": dict(margin=20, kicker_y=32, name_y=232, name_size=40, name_track=0.0,
              rule_y=None, motto_y=266, motto_size=18.5, caption_y=296,
              caption_size=9.5, domain_y=344, domain_size=9.5,
              box=dict(x="0", y="5%", w="100%", h="45%", vb="0 0 290 170", cx=145, cy=85),
              radii=(20, 38, 56, 74), sparks=False, ticks=False),
    "s": dict(margin=16, kicker_y=30, name_y=228, name_size=34, name_track=0.0,
              rule_y=None, motto_y=260, motto_size=16.5, caption_y=288,
              caption_size=9, domain_y=342, domain_size=9,
              box=dict(x="0", y="5%", w="100%", h="44%", vb="0 0 236 160", cx=118, cy=80),
              radii=(18, 34, 50, 66), sparks=False, ticks=False),
}

# Letters rise into their place one after another; everything else fades. Both
# stop under prefers-reduced-motion, so a reader who asks for stillness gets a
# settled plate.
ANIM_CSS = (
    "@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}"
    "@keyframes fade{from{opacity:0}to{opacity:1}}"
    ".in{animation:rise .95s cubic-bezier(.2,.7,.3,1) both}"
    ".fade{animation:fade 1.1s ease-out both}"
    "@media (prefers-reduced-motion:reduce){.in,.fade{animation:none}}"
)


def polar(cx, cy, r, deg):
    import math
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
        length = 8 if major else 3
        x1, y1 = polar(cx, cy, r + 2, k)
        x2, y2 = polar(cx, cy, r + 2 + length, k)
        op = opacity if major else opacity * 0.55
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="{colour}" stroke-opacity="{op:.2f}" stroke-width="1"/>')
    return "".join(out)


SPARKS = ((1.10, -0.82), (-0.61, -0.74), (1.12, 0.37), (-0.81, 0.54),
          (-0.28, -0.95), (0.80, 0.89), (-0.53, 0.86))


def instrument(t, s):
    """The astrolabe, drawn in the box's own coordinate space."""
    cx, cy = s["box"]["cx"], s["box"]["cy"]
    radii = s["radii"]
    r_out = radii[-1]
    parts = [f'<g fill="none" stroke="{t["ring"]}" stroke-linecap="round">']
    for i, r in enumerate(radii):
        op = t["ring_op"] * (0.75 + 0.12 * i)
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke-opacity="{op:.2f}" stroke-width="1"/>')
    if s["ticks"]:
        parts.append(ticks(cx, cy, r_out, t["ring"], t["ring_op"] * 1.1))
    parts.append("</g>")

    for i, r in enumerate(radii):
        speed = 260 + 45 * i
        start = 37 + 71 * i
        parts.append(f'<g fill="none" stroke="{t["ring"]}" stroke-linecap="round" '
                     f'transform="rotate({start} {cx} {cy})">'
                     f'<animateTransform attributeName="transform" type="rotate" '
                     f'from="{start} {cx} {cy}" to="{start + 360} {cx} {cy}" '
                     f'dur="{speed}s" repeatCount="indefinite"/>')
        for j in range(3):
            a0 = (23 + 47 * j + 19 * i) % 360
            sweep = 9 + 2.2 * i + 1.6 * j
            base = 0.22 + 0.1 * j
            wide = 1.05 + 0.18 * i
            ex, ey = polar(cx, cy, r, a0 + sweep)
            parts.append(f'<path d="{arc_path(cx, cy, r, a0, sweep)}" stroke-width="{wide:.2f}" '
                         f'stroke-opacity="{base:.2f}">'
                         f'<animate attributeName="opacity" values="{base:.2f};{base + 0.3:.2f};{base:.2f}" '
                         f'dur="{7 + i + j * 2}s" begin="-{(i * 2.4 + j * 1.7) % 9:.1f}s" '
                         f'repeatCount="indefinite"/></path>')
            parts.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{1.05 + 0.15 * i:.1f}" '
                         f'fill="{t["star"]}" stroke="none" fill-opacity="0.6"/>')
        parts.append("</g>")

    parts.append(
        f'<g><circle cx="{cx}" cy="{cy}" r="20" fill="url(#halo)">'
        f'<animate attributeName="r" values="16;24;16" dur="6s" repeatCount="indefinite"/></circle>'
        f'<circle cx="{cx}" cy="{cy}" r="2.4" fill="{t["star"]}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="12" fill="none" stroke="{t["halo"]}" stroke-opacity="0.06" '
        f'stroke-width="1"><animate attributeName="r" values="12;21;12" dur="6s" repeatCount="indefinite"/>'
        f'<animate attributeName="stroke-opacity" values="0.03;0.12;0.03" dur="6s" repeatCount="indefinite"/>'
        f'</circle></g>'
    )

    if s["sparks"]:
        k = r_out / 152
        parts.append(f'<g fill="{t["star"]}">')
        for i, (dx, dy) in enumerate(SPARKS):
            parts.append(f'<circle cx="{cx + dx * 152 * k:.1f}" cy="{cy + dy * 152 * k:.1f}" '
                         f'r="{0.7 + 0.1 * (i % 3):.1f}" opacity="0.3">'
                         f'<animate attributeName="opacity" values="0.12;0.5;0.12" '
                         f'dur="{3.2 + i * 0.6:.1f}s" begin="-{(i * 1.3) % 4:.1f}s" '
                         f'repeatCount="indefinite"/></circle>')
        parts.append("</g>")
        # two shooting strokes, relative to the box
        for x1, y1, x2, y2, dur, begin in ((0.89, -0.72, 0.30, -0.18, 13, 4),
                                           (0.31, -0.96, 0.74, -0.43, 17, 11)):
            bx1, by1 = cx + x1 * 152 * k, cy + y1 * 152 * k
            bx2, by2 = cx + x2 * 152 * k, cy + y2 * 152 * k
            parts.append(
                f'<g stroke="{t["ring"]}" stroke-linecap="round">'
                f'<line x1="{bx1:.1f}" y1="{by1:.1f}" x2="{bx2:.1f}" y2="{by2:.1f}" '
                f'stroke-width="1.4" stroke-dasharray="58 250" opacity="0">'
                f'<animate attributeName="opacity" values="0;0;0.85;0;0" '
                f'keyTimes="0;0.5;0.56;0.64;1" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
                f'<animate attributeName="stroke-dashoffset" from="308" to="0" '
                f'dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></line></g>')
    return "".join(parts)


def box_markup(t, s):
    b = s["box"]
    return (f'<svg x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" height="{b["h"]}" '
            f'viewBox="{b["vb"]}" preserveAspectRatio="xMidYMid meet">'
            f'{instrument(t, s)}</svg>')


def name_markup(t, s, centred):
    """The name, letter by letter, each rising on its own beat. Letter x comes
    from kerned advances, so the spacing is the font's own."""
    size = s["name_size"]
    avail = s["box_x_px"] - s["margin"] - 8 if not centred else s["fits"] - 2 * s["margin"]
    size = fit("serif", NAME, avail, size, s["name_track"])
    xs, width = F["serif"].positions(NAME, size, s["name_track"])
    x0, anchor = ("50%", "start") if centred else (str(s["margin"]), "start")
    lead = -width / 2 if centred else 0.0
    out = []
    for i, (ch, x) in enumerate(zip(NAME, xs)):
        delay = 0.25 + 0.055 * i
        out.append(T(x0, s["name_y"], ch, "serif", size, t["ink"], anchor,
                     track=s["name_track"], dx=lead + x, cls="in",
                     style=f"animation-delay:{delay:.2f}s"))
    return "".join(out), size


def header(t, s, centred):
    m = s["margin"]
    if centred:
        return T("50%", s["domain_y"], DOMAIN, "book", s["domain_size"],
                 t["domain"], track=0.2, cls="fade", style="animation-delay:.9s")
    return (
        f'<rect x="{m}" y="{s["kicker_y"] - 4}" width="16" height="1.5" fill="{t["accent"]}" '
        f'fill-opacity="0.9" class="fade" style="animation-delay:.1s"/>'
        + T(m + 28, s["kicker_y"], KICKER.upper(), "book", s["caption_size"], t["kicker"],
            "start", track=0.3, cls="fade", style="animation-delay:.15s")
    )


def body(t, s, centred):
    """Motto and caption under the name."""
    m = s["margin"]
    out = []
    if s["rule_y"] is not None:
        out.append(f'<rect x="{m}" y="{s["rule_y"]}" width="45%" height="1" fill="url(#ruleg)" '
                   f'class="fade" style="animation-delay:.55s"/>')
        out.append(T(m, s["motto_y"], MOTTO, "italic", s["motto_size"], t["motto"],
                     "start", cls="fade", style="animation-delay:.7s"))
        out.append(T(m + 2, s["caption_y"], CAPTION.upper(), "book", s["caption_size"],
                     t["caption"], "start", track=0.24, cls="fade", style="animation-delay:.85s"))
        out.append(T("100%", s["domain_y"], DOMAIN, "book", s["domain_size"], t["domain"],
                     "end", track=0.2, dx=-m, cls="fade", style="animation-delay:.95s"))
    else:
        out.append(T("50%", s["motto_y"], MOTTO, "italic", s["motto_size"], t["motto"],
                     cls="fade", style="animation-delay:.7s"))
        out.append(T("50%", s["caption_y"], CAPTION.upper(), "book", s["caption_size"],
                     t["caption"], track=0.22, cls="fade", style="animation-delay:.85s"))
    return "".join(out)


def setting(t, key):
    s = dict(SETS[key], fits={"w": 720, "m": 460, "n": 290, "s": 236}[key])
    centred = not s.get("rule_y")
    s["box_x_px"] = s["fits"] * (0.52 if key == "w" else 0.54)
    parts = [header(t, s, centred),
             f'<g class="fade" style="animation-delay:.3s">{box_markup(t, s)}</g>']
    letters, _ = name_markup(t, s, centred)
    parts.append(letters)
    parts.append(body(t, s, centred))
    return "".join(parts)


def build(theme):
    t = THEMES[theme]
    settings = {k: (setting(t, k), H) for k in SETS}
    chrome = (
        f'<defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{t["bg0"]}"/><stop offset="1" stop-color="{t["bg1"]}"/></linearGradient>'
        f'<radialGradient id="glow" cx="0.84" cy="0.42" r="0.62">'
        f'<stop offset="0" stop-color="{t["glow"]}" stop-opacity="{t["glow_op"]}"/>'
        f'<stop offset="1" stop-color="{t["glow"]}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="halo" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{t["halo"]}" stop-opacity="{t["halo_op"]}"/>'
        f'<stop offset="1" stop-color="{t["halo"]}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="vig" cx="0.5" cy="0.5" r="0.75">'
        f'<stop offset="0.6" stop-color="{t["vig"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{t["vig"]}" stop-opacity="{t["vig_op"]}"/></radialGradient>'
        f'<linearGradient id="ruleg" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t["rule"]}" stop-opacity="{t["rule_op"]}"/>'
        f'<stop offset="1" stop-color="{t["rule"]}" stop-opacity="0"/></linearGradient>'
        f'<radialGradient id="gridfade" cx="0.85" cy="0.45" r="0.68">'
        f'<stop offset="0" stop-color="#ffffff" stop-opacity="1"/>'
        f'<stop offset="0.55" stop-color="#ffffff" stop-opacity="0.4"/>'
        f'<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>'
        f'<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
        f'<path d="M 40 0 H 0 V 40" fill="none" stroke="{t["grid"]}" '
        f'stroke-opacity="{t["grid_op"]}" stroke-width="1"/></pattern>'
        f'<mask id="gridmask"><rect width="100%" height="100%" fill="url(#gridfade)"/></mask>'
        f'<filter id="grain" x="0" y="0" width="100%" height="100%">'
        f'<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch"/>'
        f'<feColorMatrix type="saturate" values="0"/></filter>'
        f'<clipPath id="card"><rect width="100%" height="100%" rx="17"/></clipPath>'
        f'</defs>'
        f'<g clip-path="url(#card)">'
        f'<rect width="100%" height="100%" fill="url(#bg)"/>'
        f'<rect width="100%" height="100%" fill="url(#glow)"/>'
        f'<rect width="100%" height="100%" fill="url(#grid)" mask="url(#gridmask)"/>'
        f'<rect width="100%" height="100%" fill="url(#vig)"/>'
        f'</g>'
    )
    over = (
        f'<rect width="100%" height="100%" filter="url(#grain)" opacity="{t["grain_op"]}" '
        f'style="mix-blend-mode:{t["grain_blend"]}"/>'
        f'<rect x="0.5" y="0.5" width="100%" height="100%" rx="17" '
        f'fill="none" stroke="{t["border"]}"/>'
    )
    return plate(ALT, settings, ground=None, rules=chrome, over=over, css=ANIM_CSS)


def main():
    for theme in ("light", "dark"):
        svg = build(theme)
        path = ROOT / "assets" / f"banner-animated-{theme}.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"{path.name}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
