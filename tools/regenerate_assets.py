#!/usr/bin/env python3
"""Regenerate the contribution sheet from live GitHub data.

A chart on paper rather than a card: the year's contributions as one long
isometric carpet across the full width, the contribution-type radar and the
language ring in the empty corners, and the figures underneath. No panel, no
rounded box; it sits directly on the page ground.

Run locally with the gh CLI logged in, or with GITHUB_TOKEN set:
    python tools/regenerate_assets.py
Scheduled in CI (.github/workflows/refresh.yml).
"""
import math
from datetime import datetime, timezone

from gh_api import USER as GH_USER, graphql
from plates import F, T, ROOT, plate

QUERY = """query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      nodes {
        name stargazerCount forkCount
        languages(first: 8, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalRepositoryContributions
      contributionCalendar { weeks { contributionDays { contributionCount date } } }
    }
  }
}"""


def fetch():
    u = graphql(QUERY, {"login": GH_USER})["user"]
    cc = u["contributionsCollection"]
    days = [{"c": d["contributionCount"], "d": d["date"]}
            for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    langs = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    return {
        "days": days,
        "radar": [cc["totalCommitContributions"], cc["totalIssueContributions"],
                  cc["totalPullRequestContributions"], cc["totalPullRequestReviewContributions"],
                  cc["totalRepositoryContributions"]],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "forks": sum(r["forkCount"] for r in u["repositories"]["nodes"]),
        "followers": u["followers"]["totalCount"],
        "projects": len(u["repositories"]["nodes"]),
        "languages": sorted(langs.items(), key=lambda kv: -kv[1]),
    }

# ── ink ─────────────────────────────────────────────────────────────────────
# Paper and ink; the five greens are the data's own ink, quiet enough to sit
# on a page.
THEMES = {
    "light": dict(
        ink="#191b1b", text="#4e5248", mute="#7d8075", hair="#191b1b", hair_op=0.12,
        ramp=["#e9ece2", "#cfdccc", "#a4c0ab", "#679275", "#2c5a43"],
        accent="#2f7a58", radar_fill=0.10, dash=0.55,
        shade=(-0.20, -0.40), shadow=("#101a14", 0.10), zero_op=0.55,
    ),
    "dark": dict(
        ink="#f2f0e8", text="#c3c5ba", mute="#8d9086", hair="#f2f0e8", hair_op=0.14,
        ramp=["#131a16", "#1a2e22", "#234a35", "#356a50", "#86b39a"],
        accent="#4fbf8f", radar_fill=0.12, dash=0.5,
        shade=(-0.14, -0.30), shadow=("#000000", 0.38), zero_op=0.95,
    ),
}

SNAP = ""
COS30 = math.cos(math.radians(30))

SET = {
    "w": dict(fits=720, design=880, margin=24, weeks=53, bar=1.55, band=500, top=52,
              labels_y=22, radar=(66, 240, 240, 118, True, 9.5), donut=(46, 244, 196),
              legend=True, months=True, bottom=100),
    "m": dict(fits=460, design=700, margin=20, weeks=40, bar=1.5, band=430, top=44,
              labels_y=20, radar=(52, 200, 210, 100, True, 8.5), donut=(38, 210, 170),
              legend=True, months=True, bottom=92),
    "n": dict(fits=290, design=290, margin=17, weeks=20, bar=1.4, band=210, top=32,
              labels_y=18, radar=(46, 172, 200, 94, False, 8), donut=(34, 108, 104),
              legend=False, months=False, bottom=330),
    "s": dict(fits=236, design=236, margin=14, weeks=14, bar=1.35, band=176, top=28,
              labels_y=16, radar=(42, 160, 180, 86, False, 7.5), donut=(30, 100, 96),
              legend=False, months=False, bottom=360),
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def level(c):
    if c == 0:
        return 0
    if c <= 3:
        return 1
    if c <= 8:
        return 2
    if c <= 16:
        return 3
    return 4


def shade(colour, k):
    r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    if k < 0:
        f = 1 + k
        r, g, b = r * f, g * f, b * f
    else:
        r, g, b = r + (255 - r) * k, g + (255 - g) * k, b + (255 - b) * k
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def fmt(n):
    return f"{n:,}"


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.sin(a), cy - r * math.cos(a)


def line(x, y, parts):
    out, cx = [], x
    for part in parts:
        text, face, size, fill, track = part[:5]
        gap = part[5] if len(part) > 5 else 0
        cx += gap
        out.append(T(cx, y, text, face, size, fill, "start", track=track))
        cx += F[face].width(text, size, track * size)
    return "".join(out), cx


# ── the carpet ──────────────────────────────────────────────────────────────
def strip(st, t, days):
    s = (st["design"] - 2 * st["margin"]) / ((st["weeks"] + 7) * COS30)
    ux, uy = COS30 * s, 0.5 * s
    x0 = st["margin"]
    span = (st["weeks"] - 1 + 6) * uy + uy + st["bar"] * s
    y0 = max(8.0, (st["band"] - span) / 2) + 6
    top = max(d["c"] for d in days) or 1
    cells = []
    for i, day in enumerate(days):
        wi, di = divmod(i, 7)
        cells.append((wi - di, wi, di, day))
    cells.sort()
    out, labels, last_month = [], [], None
    for _, wi, di, day in cells:
        cx = x0 + (wi + di) * ux
        cy = y0 + (wi - di + 6) * uy
        c = day["c"]
        col = t["ramp"][level(c)]
        h = 0.0 if c == 0 else st["bar"] * s * max(0.12, (c / top) ** 0.55)
        k = 0.92
        p = [f"{cx:.1f} {cy - uy * k - h:.1f}", f"{cx + ux * k:.1f} {cy - h:.1f}",
             f"{cx:.1f} {cy + uy * k - h:.1f}", f"{cx - ux * k:.1f} {cy - h:.1f}"]
        if h > 0:
            dk1, dk2 = t["shade"]
            sx, sy = ux * 0.42, uy * 0.85
            out.append(f'<polygon points="{cx + sx:.1f} {cy - uy * k + sy:.1f} '
                       f'{cx + ux * k + sx:.1f} {cy + sy:.1f} {cx + sx:.1f} {cy + uy * k + sy:.1f} '
                       f'{cx - ux * k + sx:.1f} {cy + sy:.1f}" '
                       f'fill="{t["shadow"][0]}" fill-opacity="{t["shadow"][1]:g}"/>')
            out.append(f'<polygon points="{cx - ux * k:.1f} {cy - h:.1f} {cx:.1f} {cy + uy * k - h:.1f} '
                       f'{cx:.1f} {cy + uy * k:.1f} {cx - ux * k:.1f} {cy:.1f}" fill="{shade(col, dk1)}"/>')
            out.append(f'<polygon points="{cx:.1f} {cy + uy * k - h:.1f} {cx + ux * k:.1f} {cy - h:.1f} '
                       f'{cx + ux * k:.1f} {cy:.1f} {cx:.1f} {cy + uy * k:.1f}" fill="{shade(col, dk2)}"/>')
            out.append(f'<polygon points="{" ".join(p)}" fill="{col}" stroke="{shade(col, 0.16)}" '
                       f'stroke-opacity="0.45" stroke-width="0.5"/>')
        else:
            out.append(f'<polygon points="{" ".join(p)}" fill="{col}" fill-opacity="{t["zero_op"]:g}" '
                       f'stroke="{t["hair"]}" stroke-opacity="0.22" stroke-width="0.5"/>')
    if st["months"]:
        for wi in range(st["weeks"]):
            month = int(days[wi * 7]["d"][5:7])
            if month != last_month:
                lx = x0 + wi * ux
                ly = y0 + (wi + 6) * uy + 26
                labels.append((lx, MONTHS[month - 1], ly))
                last_month = month
        squeezed = []
        for lx, name, ly in labels:
            if squeezed and lx - squeezed[-1][0] < 34:
                squeezed[-1] = (lx, name, ly)
            else:
                squeezed.append((lx, name, ly))
        out.append("".join(T(lx, ly, name.upper(), "book", 7.5, t["mute"], "middle", track=0.14,
                             transform=f"rotate(30 {lx:.1f} {ly:.1f})")
                           for lx, name, ly in squeezed))
    return (f'<svg x="0" y="{st["top"]}" width="100%" height="{st["band"]}" '
            f'viewBox="0 0 {st["design"]} {st["band"]}" preserveAspectRatio="xMidYMid meet">'
            f'{"".join(out)}</svg>')


# ── the corners ─────────────────────────────────────────────────────────────
def radar(values, st, t, x_attr, y, right=True, centre=False):
    r, bw, bh, cy, ticks, lab = st["radar"]
    cx = bw / 2
    angs = [72 * i for i in range(5)]
    names = ["Commit", "Issue", "PullReq", "Review", "Repo"]
    out = [f'<g fill="none" stroke="{t["mute"]}" stroke-opacity="0.5">']
    for f in (0.25, 0.5, 0.75, 1):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (polar(cx, cy, r * f, a) for a in angs))
        out.append(f'<polygon points="{pts}" stroke-dasharray="{2 * t["dash"]:.1f} {3 * t["dash"]:.1f}"/>')
    for a in angs:
        x1, y1 = polar(cx, cy, r, a)
        out.append(f'<line x1="{cx}" y1="{cy}" x2="{x1:.1f}" y2="{y1:.1f}"/>')
    out.append("</g>")
    fr = [min(1.0, math.log10(v + 1) / 4) if v > 0 else 0.0 for v in values]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (polar(cx, cy, r * f, a) for a, f in zip(angs, fr)))
    out.append(f'<polygon points="{pts}" fill="{t["accent"]}" fill-opacity="{t["radar_fill"]}" '
               f'stroke="{t["accent"]}" stroke-width="1.2" stroke-linejoin="round"/>')
    for a, f in zip(angs, fr):
        x1, y1 = polar(cx, cy, r * f, a)
        out.append(f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="1.6" fill="{t["accent"]}"/>')
    if ticks:
        for f, label in ((0.25, "10"), (0.5, "100"), (0.75, "1K"), (1.0, "10K")):
            out.append(T(cx - 4, cy - r * f + 2.5, label, "book", 6.5, t["mute"], "end"))
    for a, name in zip(angs, names):
        x1, y1 = polar(cx, cy, r * 1.16, a)
        side = math.sin(math.radians(a))
        anchor = "start" if side > 0.01 else ("end" if side < -0.01 else "middle")
        out.append(T(round(x1, 1), y1 + 3, name.upper(), "book", lab, t["ink"],
                     anchor, track=0.16, opacity=0.8))
    if right:
        pin, x = f'style="transform:translateX(-{bw + st["margin"]}px)"', "100%"
    elif centre:
        pin, x = f'style="transform:translateX(-{bw / 2}px)"', "50%"
    else:
        pin, x = "", str(x_attr)
    return (f'<svg x="{x}" y="{y}" width="{bw}" height="{bh}" viewBox="0 0 {bw} {bh}" '
            f'overflow="visible" {pin}>{"".join(out)}</svg>')


def wedge(cx, cy, r1, r0, a0, a1):
    x0o, y0o = polar(cx, cy, r1, a0)
    x1o, y1o = polar(cx, cy, r1, a1)
    x1i, y1i = polar(cx, cy, r0, a1)
    x0i, y0i = polar(cx, cy, r0, a0)
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return (f"M {x0o:.1f} {y0o:.1f} A {r1} {r1} 0 {large} 1 {x1o:.1f} {y1o:.1f} "
            f"L {x1i:.1f} {y1i:.1f} A {r0} {r0} 0 {large} 0 {x0i:.1f} {y0i:.1f} Z")


def donut(langs, st, t, x, y, pin="left"):
    r, bw, bh = st["donut"]
    top = langs[:5]
    rest = sum(v for _, v in langs[5:])
    if rest:
        top.append(("other", rest))
    total = sum(v for _, v in top) or 1
    cx, cy, r0 = bw * 0.32, bh * 0.52, r * 0.62
    out, a0 = [], -90.0
    for i, (name, size) in enumerate(top):
        share = 360 * size / total
        col = t["ramp"][max(0, 4 - i)] if name != "other" else t["ramp"][0]
        out.append(f'<path d="{wedge(cx, cy, r, r0, a0, a0 + max(share - 0.6, 0.6))}" '
                   f'fill="{col}" stroke="{t["hair"]}" stroke-opacity="0.25" stroke-width="0.5"/>')
        a0 += share
    if st["legend"]:
        lx, ly = bw * 0.52, cy - (len(top) - 1) * 7.5
        for i, (name, size) in enumerate(top):
            col = t["ramp"][max(0, 4 - i)] if name != "other" else t["ramp"][0]
            out.append(f'<rect x="{lx:.1f}" y="{ly + i * 15 - 6:.1f}" width="6" height="6" rx="1" fill="{col}"/>')
            out.append(T(lx + 11, ly + i * 15, name, "book", 7.5, t["text"], "start"))
    if pin == "right":
        place = f'x="100%" style="transform:translateX(-{bw + st["margin"]}px)"'
    elif pin == "centre":
        place = f'x="50%" style="transform:translateX(-{bw / 2}px)"'
    else:
        place = f'x="{x}"'
    return (f'<svg {place} y="{y}" width="{bw}" height="{bh}" viewBox="0 0 {bw} {bh}" '
            f'overflow="visible">{"".join(out)}</svg>')


def counts_svg(d, total, y, bw, num_size, t, label="CONTRIBUTIONS IN TWELVE MONTHS"):
    """Number, label and the two marks, in a box pinned to the centre."""
    cx = bw / 2
    body = [T(cx, 32, fmt(total), "serif", num_size, t["ink"], "middle", lnum=True),
            T(cx, 48, label, "book", 7.5, t["mute"], track=0.22),
            star_icon(cx - 48, 70, 5.6, t["ink"]),
            T(cx - 37, 73, fmt(d["stars"]), "serif", 12, t["ink"], "start", lnum=True),
            fork_icon(cx + 16, 70, 5.0, t["ink"]),
            T(cx + 28, 73, fmt(d["forks"]), "serif", 12, t["ink"], "start", lnum=True)]
    return (f'<svg x="50%" y="{y}" width="{bw}" height="86" viewBox="0 0 {bw} 86" '
            f'overflow="visible" style="transform:translateX(-{cx}px)">'
            f'{"".join(body)}</svg>')


def star_icon(x, y, r, fill):
    pts = []
    for i in range(10):
        ang = math.radians(-90 + 36 * i)
        rr = r if i % 2 == 0 else r * 0.42
        pts.append(f"{x + rr * math.cos(ang):.1f},{y + rr * math.sin(ang):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}"/>'


def fork_icon(x, y, r, fill):
    """A Y: three nodes and two branches, the shape of a fork."""
    mid = y - r * 0.1
    return (f'<g fill="none" stroke="{fill}" stroke-width="1.1" stroke-linecap="round">'
            f'<path d="M {x} {y + r * 0.75:.1f} L {x} {mid:.1f} L {x - r:.1f} {y - r * 0.75:.1f}"/>'
            f'<path d="M {x} {mid:.1f} L {x + r:.1f} {y - r * 0.75:.1f}"/></g>'
            + "".join(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.26:.1f}" fill="{fill}"/>'
                      for cx, cy in ((x - r, y - r), (x + r, y - r), (x, y + r))))


def figures(days):
    total = sum(d["c"] for d in days)
    best = max(days, key=lambda d: d["c"])
    best_fmt = datetime.strptime(best["d"], "%Y-%m-%d").strftime("%b %d")
    active = sum(1 for d in days if d["c"] > 0)
    streak = best_streak = 0
    for d in days:
        streak = streak + 1 if d["c"] > 0 else 0
        best_streak = max(best_streak, streak)
    return total, best, best_fmt, best_streak, active


def stats_block(d, st, t, y, width):
    total, best, best_fmt, streak, active = figures(d["days"])
    rows = [(fmt(best["c"]), f"best day, {best_fmt}"),
            (f"{streak}d", "longest streak"),
            (fmt(active), "active days")]
    m = st["margin"]
    out = []
    for i, (value, label) in enumerate(rows):
        yy = y + i * 24
        out.append(T("100%", yy, label.upper(), "book", 7, t["mute"], "start", track=0.14,
                     dx=-m - width))
        out.append(T("100%", yy, value, "serif", 13, t["ink"], "end", dx=-m, lnum=True))
    return "".join(out)


def labels_top(d, st, t):
    m = st["margin"]
    date = datetime.strptime(d["days"][-1]["d"], "%Y-%m-%d").strftime("%d %B %Y").upper()
    first = datetime.strptime(d["days"][0]["d"], "%Y-%m-%d").strftime("%d %b %Y").upper()
    last = datetime.strptime(d["days"][-1]["d"], "%Y-%m-%d").strftime("%d %b %Y").upper()
    if st["design"] <= 290:
        return T("50%", st["labels_y"], "RECKONED " + date, "book", 7.5, t["mute"], track=0.2)
    return (T(m, st["labels_y"], "GITHUB ACTIVITY", "book", 8, t["mute"], "start", track=0.24)
            + T("50%", st["labels_y"], "RECKONED " + date, "book", 7.5, t["mute"], track=0.2)
            + T("100%", st["labels_y"], f"{first} — {last}", "book", 7.5,
                t["mute"], "end", track=0.14, dx=-m))


def setting(d, st, t, key):
    m = st["margin"]
    days = d["days"][-st["weeks"] * 7:]
    out = [labels_top(d, st, t), strip(st, t, days)]
    total, best, best_fmt, streak, active = figures(d["days"])
    if key in ("w", "m"):
        out.append(radar(d["radar"], st, t, "100%", st["top"] + 12))
        out.append(donut(d["languages"], st, t, m, st["top"] + st["band"] - st["donut"][2] + 6))
        out.append(stats_block(d, st, t, st["top"] + st["band"] + 22, 170))
        y = st["top"] + st["band"] + 50
        out.append(counts_svg(d, total, y - 30, 240, 26, t))
        height = st["top"] + st["band"] + st["bottom"]
    else:
        if key == "s":
            # no room for the corners side by side: stack them
            out.append(radar(d["radar"], st, t, "0",
                             st["top"] + st["band"] + 14, right=False, centre=True))
            out.append(donut(d["languages"], st, t, 0,
                             st["top"] + st["band"] + st["radar"][2] + 24, pin="centre"))
            y = st["top"] + st["band"] + st["radar"][2] + st["donut"][2] + 84
        else:
            out.append(radar(d["radar"], st, t, "0", st["top"] + st["band"] + 16, right=False))
            out.append(donut(d["languages"], st, t, 0, st["top"] + st["band"] + 30, pin="right"))
            y = st["top"] + st["band"] + 236
        out.append(counts_svg(d, total, y - 26, 236, 22, t, "IN TWELVE MONTHS"))
        out.append(T("50%", y + 64, f"BEST DAY {fmt(best['c'])} · STREAK {streak}D · ACTIVE {active}",
                     "book", 7, t["mute"], track=0.16))
        height = y + 96
    return "".join(out), height


def build(d):
    out = {}
    for theme, t in THEMES.items():
        settings = {k: setting(d, dict(SET[k]), t, k) for k in SET}
        total = sum(x["c"] for x in d["days"])
        title = f"GitHub activity: {total} contributions in twelve months, reckoned {SNAP}"
        out[theme] = plate(title, settings, ground=None, valign="top")
    return out


def main():
    global SNAP
    d = fetch()
    SNAP = datetime.now(timezone.utc).strftime("%d %B %Y")
    svgs = build(d)
    for theme, svg in svgs.items():
        path = ROOT / "assets" / f"activity-{theme}.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"activity-{theme}.svg: {path.stat().st_size} bytes")
    total, best, best_fmt, streak, active = figures(d["days"])
    print(f"reckoned {SNAP}: {total} contributions, best {best['c']} ({best_fmt}), "
          f"streak {streak}d, active {active}; languages: {len(d['languages'])}")


if __name__ == "__main__":
    main()
