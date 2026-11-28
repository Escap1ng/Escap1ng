#!/usr/bin/env python3
"""Typographic engine for the profile plates.

GitHub strips CSS from READMEs, so text blocks are drawn as self-contained SVG
images. Three properties make these images behave like set type:

  * No viewBox. A plate keeps the height it asks for and never scales, so type
    stays at its designed size. Each plate is set at four widths and an internal
    media query shows the setting that fits the space GitHub gives the image.
  * Fonts are embedded per plate, subset to the glyphs that plate uses. Copy
    edits never need a font rebuild, and each plate stays small.
  * Copy lives in the page modules as data. This module only measures and draws.

Measurement happens here (fontTools advances plus GPOS kerning), not in the
browser, so line breaks and fitted sizes are deterministic across machines.
Plates are byte-stable for the same input (no timestamps written).
"""
import base64
import html
from io import BytesIO
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "assets" / "fonts"

NBSP = "\u00a0"
MIDDOT = " · "
TRACK = 0.26          # default letter-spacing for small capitals, in em
TITLE_TRACK = 0.08    # and for serif titles

# The four settings, narrowest plate each may be shown in. A profile README is
# about 880 px wide on a desktop and 240 to 350 on a phone.
FITS = {"w": 720, "m": 460, "n": 290, "s": 236}
CSS_FIT = (".m,.n,.s{display:none}"
           "@media (max-width:719.9px){.w{display:none}.m{display:inline}}"
           "@media (max-width:459.9px){.m{display:none}.n{display:inline}}"
           "@media (max-width:289.9px){.n{display:none}.s{display:inline}}")


def esc(s):
    return html.escape(s, quote=True)


def flat(s):
    """Copy with line breaks taken out, for alt text."""
    return " ".join(s.split())


class Face:
    """An embedded woff2 subset plus a small metrics engine (advances and GPOS
    kerning) so layout can measure text without a browser."""

    def __init__(self, key, family, filename):
        self.key, self.family = key, family
        self.path = FONT_DIR / filename
        self.tt = TTFont(self.path)
        self.upem = self.tt["head"].unitsPerEm
        self.cmap = self.tt.getBestCmap()
        self.adv = self.tt["hmtx"].metrics
        self.cap = self.tt["OS/2"].sCapHeight / self.upem
        self.pairs = self._kern_subtables()

    def _kern_subtables(self):
        out = []
        if "GPOS" not in self.tt:
            return out
        gpos = self.tt["GPOS"].table
        lookups = set()
        for fr in gpos.FeatureList.FeatureRecord:
            if fr.FeatureTag == "kern":
                lookups.update(fr.Feature.LookupListIndex)
        for li in sorted(lookups):
            lk = gpos.LookupList.Lookup[li]
            for st in lk.SubTable:
                if lk.LookupType == 9:
                    st = st.ExtSubTable
                if type(st).__name__ == "PairPos":
                    out.append(st)
        return out

    def kerns(self, g1, g2):
        for st in self.pairs:
            cov = st.Coverage.glyphs
            if g1 not in cov:
                continue
            if st.Format == 1:
                for r in st.PairSet[cov.index(g1)].PairValueRecord:
                    if r.SecondGlyph == g2:
                        return getattr(r.Value1, "XAdvance", 0) or 0
            elif st.Format == 2:
                c1 = st.ClassDef1.classDefs.get(g1, 0)
                c2 = st.ClassDef2.classDefs.get(g2, 0)
                v = getattr(st.Class1Record[c1].Class2Record[c2].Value1, "XAdvance", 0) or 0
                if v:
                    return v
        return 0

    def glyph(self, ch):
        return self.cmap.get(ord(ch), ".notdef")

    def width(self, text, size, track=0.0):
        """Advance width in px. `track` is letter-spacing in px; browsers add it
        after every glyph, the last included."""
        gl = [self.glyph(c) for c in text]
        w = 0.0
        for i, g in enumerate(gl):
            w += self.adv.get(g, (0, 0))[0]
            if i + 1 < len(gl):
                w += self.kerns(g, gl[i + 1])
        return w * size / self.upem + track * len(text)

    def positions(self, text, size, spread=0.0):
        """x of each letter, kerned, with `spread` (em) between letters.
        -> ([x...], total width without the trailing spread)"""
        gl = [self.glyph(c) for c in text]
        xs, x = [], 0.0
        for i, g in enumerate(gl):
            xs.append(x)
            step = self.adv.get(g, (0, 0))[0]
            if i + 1 < len(gl):
                step += self.kerns(g, gl[i + 1])
            x += step * size / self.upem + spread * size
        return xs, x - spread * size

    def face_css(self, chars):
        missing = sorted(c for c in chars if ord(c) not in self.cmap)
        if missing:
            raise SystemExit(f"{self.key} has no glyph for {missing!r}")
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "lnum"]
        opts.hinting = False
        opts.desubroutinize = True
        opts.notdef_outline = True
        opts.name_IDs = [1, 2]
        f = TTFont(self.path, recalcTimestamp=False)
        s = subset.Subsetter(opts)
        s.populate(unicodes=sorted({ord(c) for c in chars} | {0x20}))
        s.subset(f)
        f.flavor = "woff2"
        buf = BytesIO()
        f.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return (f"@font-face{{font-family:'{self.family}';"
                f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")


F = {
    "serif":  Face("serif",  "RdSerif",  "cormorant-600.woff2"),
    "book":   Face("book",   "RdBook",   "cormorant-500.woff2"),
    "italic": Face("italic", "RdItalic", "cormorant-400-italic.woff2"),
}

USED = {}     # face key -> characters used by the plate being built
HEIGHTS = {}  # plate title -> the height each setting asked for


def use(face, s):
    USED.setdefault(face, set()).update(s)


def fit(face, text, max_w, max_size, track=0.0):
    """Largest whole size <= max_size at which the text fits in max_w."""
    one = F[face].width(text, 1.0, track)
    return float(int(min(max_size, max_w / one)))


def wrap(face, size, text, measure, track=0.0, balance=True):
    """Break into centred lines no wider than `measure`, then even the lines out
    so the last is never a stray word. A newline in the copy is a hard break."""
    if "\n" in text:
        return [ln for part in text.split("\n")
                for ln in wrap(face, size, part, measure, track, balance)]
    words = text.split()

    def greedy(limit):
        lines, cur = [], []
        for w in words:
            if cur and F[face].width(" ".join(cur + [w]), size, track * size) > limit:
                lines.append(" ".join(cur))
                cur = [w]
            else:
                cur = cur + [w]
        return lines + [" ".join(cur)] if cur else lines

    lines = greedy(measure)
    if balance and len(lines) > 1:
        lo, hi = 0.0, measure
        for _ in range(20):
            mid = (lo + hi) / 2
            if len(greedy(mid)) <= len(lines):
                hi = mid
            else:
                lo = mid
        lines = greedy(hi)
    return lines


def rows(items, face, size, measure, track=0.0, gap=MIDDOT):
    """Flow a list into centred rows, as few as will fit, as even as they go."""
    def greedy(limit):
        out, cur = [], []
        for it in items:
            if cur and F[face].width(gap.join(cur + [it]), size, track * size) > limit:
                out.append(cur)
                cur = [it]
            else:
                cur = cur + [it]
        return out + [cur] if cur else out

    best = greedy(measure)
    lo, hi = 0.0, measure
    for _ in range(20):
        mid = (lo + hi) / 2
        if len(greedy(mid)) <= len(best):
            hi = mid
        else:
            lo = mid
    return [gap.join(r) for r in greedy(hi)]


def facts(face, size, text, measure):
    """Running facts. Lists joined by middle dots break between the things
    listed, so no line begins or ends on a dot."""
    out = []
    for part in text.split("\n"):
        out += rows(part.split(MIDDOT), face, size, measure, 0.0, MIDDOT) if MIDDOT in part \
            else wrap(face, size, part, measure)
    return out


# ── primitives ──────────────────────────────────────────────────────────────
# No absolute x: a plate may be 240 px wide or 1200. Text hangs from the left
# edge (x in px), a share of the width ("50%") or the right edge ("100%"), and
# is nudged by dx.
def T(x, y, s, face, size, fill, anchor="middle", track=0.0, dx=0.0,
      lnum=False, cls=None, style=None, opacity=None, transform=None):
    """`lnum` asks for lining figures (Cormorant's default old-style 1 reads as
    a small-capital I)."""
    use(face, s)
    ls = track * size
    shift = dx + (ls / 2 if anchor == "middle" else ls if anchor == "end" else 0.0)
    a = [f'x="{x}"', f'y="{y:.1f}"', f'font-family="{F[face].family}"',
         f'font-size="{size:g}"', f'fill="{fill}"']
    if anchor != "start":
        a.append(f'text-anchor="{anchor}"')
    if ls:
        a.append(f'letter-spacing="{ls:.2f}"')
    if abs(shift) > 0.005:
        a.append(f'dx="{shift:.2f}"')
    if lnum:
        a.append("font-feature-settings=\"'lnum'\"")
    if cls:
        a.append(f'class="{cls}"')
    if style:
        a.append(f'style="{style}"')
    if opacity is not None:
        a.append(f'fill-opacity="{opacity:g}"')
    if transform:
        a.append(f'transform="{transform}"')
    return f'<text {" ".join(a)}>{esc(s)}</text>'


def hairline(y, hair):
    """Edge to edge. `hair` is (colour, opacity)."""
    return f'<rect y="{y:g}" width="100%" height="1" fill="{hair[0]}" fill-opacity="{hair[1]:g}"/>'


def upright(x, y, h, hair):
    return f'<rect x="{x}" y="{y:g}" width="1" height="{h:g}" fill="{hair[0]}" fill-opacity="{hair[1]:g}"/>'


def centred_rect(y, w, h, attrs):
    return (f'<rect x="50%" y="{y:g}" width="{w:g}" height="{h:g}" '
            f'transform="translate({-w / 2:g} 0)" {attrs}/>')


def dash(y, colour, w=28):
    """A short rule in the middle: the pause between two things of the same kind."""
    return centred_rect(y, w, 1, f'fill="{colour}"')


def plaque(y, label, w, h, ink, size=10.5, track=TRACK):
    """A sharp-cornered rectangle drawn in outline, with a word in it: a door."""
    box = centred_rect(y + .5, w - 1, h - 1,
                       f'fill="none" stroke="{ink}" shape-rendering="crispEdges"')
    return box + T("50%", y + h / 2 + F["book"].cap * size / 2, label.upper(),
                   "book", size, ink, track=track)


def plaque_width(label, size, track=TRACK, pad=28):
    w = F["book"].width(label.upper(), size, track * size) - track * size + 2 * pad
    return float(int(w + 1) // 2 * 2)


class Column:
    """Lines stacked down the middle of a plate. `y` is always the last baseline;
    a gap is measured from there to the top of the next capitals."""

    def __init__(self):
        self.y, self.b = 0.0, []

    def gap(self, h):
        self.y += h
        return self

    def lines(self, lines, face, size, fill, leading, track=0.0, upper=False):
        self.y += F[face].cap * size
        for i, ln in enumerate(lines):
            self.y += leading if i else 0
            self.b.append(T("50%", self.y, ln.upper() if upper else ln, face, size, fill, track=track))
        return self

    def caps(self, s, size, fill, track=TRACK, measure=None):
        lines = wrap("book", size, s.upper(), measure, track) if measure else [s]
        return self.lines(lines, "book", size, fill, size * 1.9, track, upper=True)

    def title(self, s, size, fill):
        return self.lines([s], "serif", size, fill, 0, TITLE_TRACK, upper=True)

    def add(self, markup, h):
        self.b.append(markup(self.y))
        self.y += h
        return self


def plate(title, settings, ground=None, rules="", css="", pad=(0, 0), airs=None, over="",
          valign="middle"):
    """The same column in each setting, in one fixed height (an <img> cannot
    change its height by media query): the tallest setting decides, the others
    share out the slack. `settings` maps "w"/"m"/"n"/"s" to a Column, or to
    (markup, height). `pad` is the room above and below at full air; `rules`
    sits under the type, `over` above it (grain, borders). `valign` places the
    slack of a shorter setting below it instead of above and below."""
    airs = airs or {}
    done = {k: ("".join(v.b), v.y) if isinstance(v, Column) else v for k, v in settings.items()}
    need = {k: h + (pad[0] + pad[1]) * airs.get(k, 1.0) for k, (_, h) in done.items()}
    height = int(round(max(need.values())))
    HEIGHTS[title] = {k: round(v) for k, v in need.items()}
    body = []
    for k, (markup, h) in done.items():
        slack = 0 if valign == "top" else (height - need[k]) / 2
        top = pad[0] * airs.get(k, 1.0) + slack
        body.append(f'<g class="{k}" transform="translate(0 {top:.1f})">{markup}</g>')
    faces = "".join(F[k].face_css("".join(sorted(USED[k]))) for k in F if USED.get(k))
    USED.clear()
    bg = f'<rect width="100%" height="100%" fill="{ground}"/>' if ground else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="{height}" '
            f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
            f'<style>{faces}{CSS_FIT}{css}</style>{bg}{rules}{"".join(body)}{over}</svg>')


def img(src, alt):
    return f'<img src="{src}" alt="{esc(alt)}" width="100%" align="top">'


def themed(pattern, alt):
    """`pattern` contains {theme}: the light drawing is the fallback, the dark one
    a <source>."""
    return (f'<picture><source media="(prefers-color-scheme: dark)" '
            f'srcset="{pattern.format(theme="dark")}">'
            f'{img(pattern.format(theme="light"), alt)}</picture>')


def link(href, inner):
    return f'<a href="{href}">{inner}</a>'
