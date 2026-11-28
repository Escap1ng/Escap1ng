#!/usr/bin/env python3
"""Fetch Cormorant Garamond (OFL) and cut the three faces the plates set.

    python tools/fetch_fonts.py [--force]

Downloads the variable fonts from google/fonts once, instantiates the weights
the page uses (500, 600, 400 italic), subsets them to Latin plus the dashes and
quotes a page might need, and writes woff2 into assets/fonts. The OFL licence
is fetched alongside. This script is the record of where the faces came from;
run it again to refresh them.
"""
import sys
import urllib.request
from io import BytesIO
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "fonts"
BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/"

FACES = [
    ("CormorantGaramond%5Bwght%5D.ttf", 500, "cormorant-500.woff2"),
    ("CormorantGaramond%5Bwght%5D.ttf", 600, "cormorant-600.woff2"),
    ("CormorantGaramond-Italic%5Bwght%5D.ttf", 400, "cormorant-400-italic.woff2"),
]

UNICODES = (list(range(0x20, 0x7F)) + list(range(0xA0, 0x100))
            + list(range(0x2010, 0x2028)) + list(range(0x2032, 0x203B))
            + [0x2026, 0x203C])


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def main():
    force = "--force" in sys.argv
    wanted = {name for _, _, name in FACES} | {"OFL.txt"}
    if not force and all((OUT / n).exists() for n in wanted):
        print("faces already present; pass --force to refresh")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    cache = {}
    for src, weight, name in FACES:
        if not force and (OUT / name).exists():
            print(f"{name}: present")
            continue
        if src not in cache:
            cache[src] = TTFont(BytesIO(fetch(BASE + src)))
        f = instantiateVariableFont(cache[src], {"wght": weight}, inplace=False)
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "lnum"]
        opts.hinting = False
        opts.desubroutinize = True
        opts.notdef_outline = True
        s = subset.Subsetter(opts)
        s.populate(unicodes=sorted(set(UNICODES)))
        s.subset(f)
        f.flavor = "woff2"
        buf = BytesIO()
        f.save(buf)
        (OUT / name).write_bytes(buf.getvalue())
        print(f"{name}: {len(buf.getvalue())} bytes")
    if force or not (OUT / "OFL.txt").exists():
        (OUT / "OFL.txt").write_bytes(fetch(BASE + "OFL.txt"))
        print("OFL.txt: written")


if __name__ == "__main__":
    main()
