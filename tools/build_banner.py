#!/usr/bin/env python3
"""Build the profile banner SVGs (light/dark, animated and static).

Run: python tools/build_banner.py
Fonts are embedded from assets/fonts so the SVGs are self-contained;
those woff2 files are glyph subsets covering the banner copy, so new
words fall back to Georgia unless the subset is rebuilt.
"""
import base64
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / 'assets' / 'fonts'
MONO = 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'
SERIF = "CormorantGaramond, Georgia, 'Times New Roman', serif"
W = 1280
CX = 1085

FONTS = [
    ('600', 'normal', 'cormorant-600.woff2'),
    ('500', 'normal', 'cormorant-500.woff2'),
    ('400', 'italic', 'cormorant-400-italic.woff2'),
]

LAYOUTS = {
    364: dict(kicker=86, word=178, word_size=76, rule=204, motto=252, motto_size=34,
              caption=286, domain=334, cy=170, radii=(44, 80, 116, 152)),
    320: dict(kicker=76, word=156, word_size=70, rule=182, motto=228, motto_size=31,
              caption=260, domain=302, cy=146, radii=(36, 66, 96, 124)),
}

THEMES = {
    'light': dict(
        bg0='#f6f9f6', bg1='#e8f0ea', ink='#10131a', kicker='#75837b',
        motto='#4e5f55', caption='#7d8b82', domain='#8a968d',
        rule='#0c0e12', rule_op=0.16, border='#d2dcd5',
        glow='#dcebe1', glow_op=0.9, vig='#dde6df', vig_op=0.5,
        grid='#5e7167', grid_op=0.06, ring='#16a36a', ring_op=0.22,
        accent='#16a36a', star='#1d2a23', halo='#16a36a', halo_op=0.38,
        grain_op=0.05, grain_blend='multiply',
    ),
    'dark': dict(
        bg0='#030604', bg1='#0a120e', ink='#edf3ee', kicker='#5d6f66',
        motto='#a9b7ae', caption='#7e8f86', domain='#5f7067',
        rule='#edf3ee', rule_op=0.15, border='#233229',
        glow='#0e2119', glow_op=0.7, vig='#000000', vig_op=0.5,
        grid='#a3c4b2', grid_op=0.05, ring='#16a36a', ring_op=0.3,
        accent='#16a36a', star='#edf3ee', halo='#3fbf8a', halo_op=0.5,
        grain_op=0.07, grain_blend='overlay',
    ),
}


def font_css():
    blocks = []
    for weight, style, name in FONTS:
        data = base64.b64encode((FONT_DIR / name).read_bytes()).decode()
        blocks.append(
            "    @font-face {\n"
            "      font-family: 'CormorantGaramond';\n"
            f"      src: url(data:font/woff2;base64,{data}) format('woff2');\n"
            f"      font-weight: {weight};\n"
            f"      font-style: {style};\n"
            "    }"
        )
    return '\n'.join(blocks)


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.sin(a), cy - r * math.cos(a)


def arc_path(cx, cy, r, start, sweep):
    x1, y1 = polar(cx, cy, r, start)
    x2, y2 = polar(cx, cy, r, start + sweep)
    return f'M {x1:.1f} {y1:.1f} A {r} {r} 0 0 1 {x2:.1f} {y2:.1f}'


def ticks(cx, cy, r, color, opacity):
    out = []
    for k in range(0, 360, 10):
        major = k % 30 == 0
        length = 8 if major else 3
        x1, y1 = polar(cx, cy, r + 2, k)
        x2, y2 = polar(cx, cy, r + 2 + length, k)
        op = opacity if major else opacity * 0.55
        out.append(f'      <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="{color}" stroke-opacity="{op:.2f}" stroke-width="1"/>')
    return '\n'.join(out)


def astrolabe(t, layout, animated):
    cx, cy = CX, layout['cy']
    radii = layout['radii']
    parts = []
    parts.append(f'  <g fill="none" stroke="{t["ring"]}" stroke-linecap="round">')
    for i, r in enumerate(radii):
        op = t['ring_op'] * (0.75 + 0.12 * i)
        parts.append(f'    <circle cx="{cx}" cy="{cy}" r="{r}" stroke-opacity="{op:.2f}" stroke-width="1"/>')
    parts.append(ticks(cx, cy, radii[-1], t['ring'], t['ring_op'] * 1.1))
    parts.append('  </g>')

    for i, r in enumerate(radii):
        speed = 260 + 45 * i
        start = 37 + 71 * i
        rot = f' transform="rotate({start} {cx} {cy})"'
        anim_rot = ''
        if animated:
            anim_rot = (f'\n      <animateTransform attributeName="transform" type="rotate" '
                        f'from="{start} {cx} {cy}" to="{start + 360} {cx} {cy}" dur="{speed}s" repeatCount="indefinite"/>')
        parts.append(f'    <g fill="none" stroke="{t["ring"]}" stroke-linecap="round"{rot}>{anim_rot}')
        for j in range(3):
            a0 = (23 + 47 * j + 19 * i) % 360
            sweep = 9 + 2.2 * i + 1.6 * j
            base = 0.22 + 0.1 * j
            wide = 1.05 + 0.18 * i
            breathe = ''
            if animated:
                breathe = (f'\n        <animate attributeName="opacity" values="{base:.2f};{base + 0.3:.2f};{base:.2f}" '
                           f'dur="{7 + i + j * 2}s" begin="-{(i * 2.4 + j * 1.7) % 9:.1f}s" repeatCount="indefinite"/>')
            ex, ey = polar(cx, cy, r, a0 + sweep)
            parts.append(f'      <path d="{arc_path(cx, cy, r, a0, sweep)}" stroke-width="{wide:.2f}" '
                         f'stroke-opacity="{base:.2f}">{breathe}</path>')
            parts.append(f'      <circle cx="{ex:.1f}" cy="{ey:.1f}" r="{1.05 + 0.15 * i:.1f}" '
                         f'fill="{t["star"]}" stroke="none" fill-opacity="0.6"/>')
        parts.append('    </g>')

    pulse = ''
    if animated:
        pulse = ('\n      <animate attributeName="r" values="12;21;12" dur="6s" repeatCount="indefinite"/>'
                 '\n      <animate attributeName="stroke-opacity" values="0.03;0.12;0.03" dur="6s" repeatCount="indefinite"/>')
    parts.append(
        f'  <g>\n'
        f'    <circle cx="{cx}" cy="{cy}" r="20" fill="url(#halo)">'
        + ('\n      <animate attributeName="r" values="16;24;16" dur="6s" repeatCount="indefinite"/>' if animated else '')
        + f'\n    </circle>\n'
        f'    <circle cx="{cx}" cy="{cy}" r="2.4" fill="{t["star"]}"/>\n'
        f'    <circle cx="{cx}" cy="{cy}" r="12" fill="none" stroke="{t["halo"]}" stroke-opacity="0.06" stroke-width="1">{pulse}\n    </circle>\n'
        f'  </g>'
    )

    sparks = [(1252, 46, 1.0), (992, 58, 0.8), (1256, 226, 0.9), (962, 252, 0.8),
              (1042, 26, 0.7), (1206, 306, 0.8), (1004, 300, 0.7)]
    parts.append(f'  <g fill="{t["star"]}">')
    for k, (x, y, r) in enumerate(sparks):
        anim = ''
        if animated:
            anim = (f'<animate attributeName="opacity" values="0.12;0.5;0.12" '
                    f'dur="{3.2 + k * 0.6:.1f}s" begin="-{(k * 1.3) % 4:.1f}s" repeatCount="indefinite"/>')
        parts.append(f'    <circle cx="{x}" cy="{y}" r="{r}" opacity="0.3">{anim}</circle>')
    parts.append('  </g>')

    if animated:
        parts.append(
            f'  <g stroke="{t["ring"]}" stroke-linecap="round">\n'
            f'    <line x1="1262" y1="60" x2="1186" y2="142" stroke-width="1.4" stroke-dasharray="58 250" opacity="0">\n'
            f'      <animate attributeName="opacity" values="0;0;0.85;0;0" keyTimes="0;0.5;0.56;0.64;1" dur="13s" begin="4s" repeatCount="indefinite"/>\n'
            f'      <animate attributeName="stroke-dashoffset" from="308" to="0" dur="13s" begin="4s" repeatCount="indefinite"/>\n'
            f'    </line>\n'
            f'    <line x1="1198" y1="24" x2="1264" y2="104" stroke-width="1.4" stroke-dasharray="58 250" opacity="0">\n'
            f'      <animate attributeName="opacity" values="0;0;0.85;0;0" keyTimes="0;0.5;0.56;0.64;1" dur="17s" begin="11s" repeatCount="indefinite"/>\n'
            f'      <animate attributeName="stroke-dashoffset" from="308" to="0" dur="17s" begin="11s" repeatCount="indefinite"/>\n'
            f'    </line>\n'
            f'  </g>'
        )
    return '\n'.join(parts)


def build(theme, height, animated):
    t = THEMES[theme]
    ly = LAYOUTS[height]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-label="Escap1ng — Altiora petamus — Independent developer in Hangzhou">
  <defs>
{font_css()}
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t['bg0']}"/>
      <stop offset="1" stop-color="{t['bg1']}"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.84" cy="0.42" r="0.62">
      <stop offset="0" stop-color="{t['glow']}" stop-opacity="{t['glow_op']}"/>
      <stop offset="1" stop-color="{t['glow']}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="halo" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{t['halo']}" stop-opacity="{t['halo_op']}"/>
      <stop offset="1" stop-color="{t['halo']}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="vig" cx="0.5" cy="0.5" r="0.75">
      <stop offset="0.6" stop-color="{t['vig']}" stop-opacity="0"/>
      <stop offset="1" stop-color="{t['vig']}" stop-opacity="{t['vig_op']}"/>
    </radialGradient>
    <linearGradient id="ruleg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t['rule']}" stop-opacity="{t['rule_op']}"/>
      <stop offset="1" stop-color="{t['rule']}" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="gridfade" cx="0.85" cy="0.45" r="0.68">
      <stop offset="0" stop-color="#ffffff" stop-opacity="1"/>
      <stop offset="0.55" stop-color="#ffffff" stop-opacity="0.4"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 H 0 V 40" fill="none" stroke="{t['grid']}" stroke-opacity="{t['grid_op']}" stroke-width="1"/>
    </pattern>
    <mask id="gridmask"><rect width="{W}" height="{height}" fill="url(#gridfade)"/></mask>
    <filter id="grain" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
    </filter>
    <clipPath id="card"><rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="17"/></clipPath>
  </defs>

  <g clip-path="url(#card)">
  <rect width="{W}" height="{height}" fill="url(#bg)"/>
  <rect width="{W}" height="{height}" fill="url(#glow)"/>
  <rect width="{W}" height="{height}" fill="url(#grid)" mask="url(#gridmask)"/>

{astrolabe(t, ly, animated)}

  <line x1="88" y1="{ly['kicker'] - 4}" x2="104" y2="{ly['kicker'] - 4}" stroke="{t['accent']}" stroke-opacity="0.9" stroke-width="1.5"/>
  <text x="116" y="{ly['kicker']}" font-family="{MONO}" font-size="12" letter-spacing="3.6" fill="{t['kicker']}">ESCAPING NOTES</text>

  <text x="86" y="{ly['word']}" font-family="{SERIF}" font-weight="600" font-size="{ly['word_size']}" letter-spacing="1" fill="{t['ink']}">Escap1ng</text>

  <rect x="90" y="{ly['rule']}" width="520" height="1" fill="url(#ruleg)"/>

  <text x="88" y="{ly['motto']}" font-family="{SERIF}" font-weight="400" font-style="italic" font-size="{ly['motto_size']}" letter-spacing="0.5" fill="{t['motto']}">Altiora petamus</text>

  <text x="90" y="{ly['caption']}" font-family="{MONO}" font-size="13" letter-spacing="3" fill="{t['caption']}">INDEPENDENT DEVELOPER · HANGZHOU</text>

  <text x="1192" y="{ly['domain']}" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="2.4" fill="{t['domain']}">escaping.top</text>

  <rect width="{W}" height="{height}" fill="url(#vig)"/>
  </g>

  <rect width="{W}" height="{height}" filter="url(#grain)" opacity="{t['grain_op']}" style="mix-blend-mode:{t['grain_blend']}"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="17" fill="none" stroke="{t['border']}"/>
</svg>
'''


def main():
    for theme in ('light', 'dark'):
        for height, animated in ((364, True), (320, False)):
            name = f"banner-animated-{theme}.svg" if animated else f"banner-{theme}.svg"
            path = ROOT / 'assets' / name
            path.write_text(build(theme, height, animated), encoding='utf-8')
            print(f'{name}: {path.stat().st_size} bytes')


if __name__ == '__main__':
    main()
