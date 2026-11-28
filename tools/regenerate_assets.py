#!/usr/bin/env python3
"""Regenerate the contribution plate and README star chips from live GitHub data.

The plate is three things in one card: an isometric carpet of the last half year
(bar height and tone follow the day's count), a five-axis radar of contribution
types over the last year, and the precise figures (best day, longest streak,
active days). Every setting is complete at its own width; type never scales.

Run locally with the gh CLI logged in, or with GITHUB_TOKEN set:
    python tools/regenerate_assets.py
Scheduled in CI (.github/workflows/refresh.yml).
"""
import json
import math
import os
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from plates import F, T, MIDDOT, ROOT, hairline, plate

GH_USER = "Escap1ng"

QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalRepositoryContributions
      contributionCalendar {
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}"""


def gql(login):
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
            headers={"Authorization": f"Bearer {token}",
                     "User-Agent": "profile-assets-refresh",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.load(r)
    else:
        out = subprocess.check_output(
            ["gh", "api", "graphql", "-f", f"query={QUERY}", "-f", f"login={login}"])
        payload = json.loads(out)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]


def rest(path, token):
    if token:
        req = urllib.request.Request(
            f"https://api.github.com/{path}",
            headers={"Authorization": f"Bearer {token}",
                     "User-Agent": "profile-assets-refresh",
                     "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    return json.loads(subprocess.check_output(["gh", "api", path]))


def fetch():
    token = os.environ.get("GITHUB_TOKEN")
    user = gql(GH_USER)
    cc = user["contributionsCollection"]
    repos = rest(f"users/{GH_USER}/repos?per_page=100", token)
    profile = rest(f"users/{GH_USER}", token)
    days = [{"c": d["contributionCount"], "d": d["date"]}
            for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    radar = [cc["totalCommitContributions"], cc["totalIssueContributions"],
             cc["totalPullRequestContributions"], cc["totalPullRequestReviewContributions"],
             cc["totalRepositoryContributions"]]
    return {
        "days": days[-26 * 7:],
        "radar": [v or 0 for v in radar],
        "stars": sum(r["stargazers_count"] for r in repos if not r["fork"]),
        "forks": sum(r["forks_count"] for r in repos if not r["fork"]),
        "followers": profile["followers"],
        "projects": len([r for r in repos if not r["fork"]]),
        "all_repos": repos,
    }

# ── ink ─────────────────────────────────────────────────────────────────────
# The five tones of the carpet, dark to light. Faces are shaded from the top
# tone, so a bar reads as a solid standing on the plate.
THEMES = {
    "light": dict(
        bg0="#f7faf8", bg1="#e9f0eb", border="#d2dcd5", ink="#10131a",
        text="#55645b", mute="#7d8b82", hair="#0c0e12", hair_op=0.12,
        ramp=["#dfe8e2", "#c4e0d0", "#8ccfae", "#3aa87c", "#0b563b"],
        accent="#16a36a", radar_fill=0.10, dash=0.55,
        shade=(-0.14, -0.27), grain=None,
    ),
    "dark": dict(
        bg0="#030604", bg1="#0a120e", border="#233229", ink="#e9f1ec",
        text="#b3c1b8", mute="#8a9992", hair="#edf3ee", hair_op=0.14,
        ramp=["#121a16", "#17392a", "#1c6349", "#16a36a", "#6fd3a6"],
        accent="#3fbf8a", radar_fill=0.12, dash=0.5,
        shade=(-0.10, -0.22), grain=None,
    ),
}

COS30 = math.cos(math.radians(30))

SET = {
    "w": dict(fits=720, margin=26, weeks=26, s=15.0, bar=0.72, radar_r=62,
              radar_cy=196, stats_top=286, header_y=44, hair_y=58, carpet_y=92,
              legend_gap=26, snap=True),
    "m": dict(fits=460, margin=20, weeks=18, s=11.5, bar=0.72, radar_r=50,
              radar_cy=180, stats_top=258, header_y=40, hair_y=54, carpet_y=80,
              legend_gap=22, snap=True),
    "n": dict(fits=290, margin=17, weeks=13, s=12.5, bar=0.7, radar_r=44,
              radar_cy=None, stats_top=None, header_y=38, hair_y=64, carpet_y=84,
              legend_gap=20, snap=False),
    "s": dict(fits=236, margin=14, weeks=10, s=11.5, bar=0.7, radar_r=40,
              radar_cy=None, stats_top=None, header_y=36, hair_y=62, carpet_y=80,
              legend_gap=18, snap=False),
}

FADE = ("@keyframes f{from{opacity:0}}"
        ".f{animation:f .8s ease-out both}"
        "@media (prefers-reduced-motion:reduce){.f{animation:none}}")


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


def shade(hex_colour, k):
    """Negative k darkens toward black, positive toward white."""
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    if k < 0:
        f = 1 + k
        r, g, b = r * f, g * f, b * f
    else:
        r, g, b = r + (255 - r) * k, g + (255 - g) * k, b + (255 - b) * k
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def fmt(n):
    return f"{n:,}"


def line(x, y, parts):
    """Parts left to right: (text, face, size, fill, track[, gap]). -> (markup, end x)"""
    out, cx = [], x
    for part in parts:
        text, face, size, fill, track = part[:5]
        gap = part[5] if len(part) > 5 else 0
        cx += gap
        out.append(T(cx, y, text, face, size, fill, "start", track=track))
        cx += F[face].width(text, size, track * size)
    return "".join(out), cx


def header_block(d, st, t):
    m = st["margin"]
    if st["snap"]:
        parts = []
        for value, label in ((fmt(d["stars"]), "stars"), (fmt(d["forks"]), "forks"),
                             (fmt(d["followers"]), "followers"), (fmt(d["projects"]), "projects")):
            if parts:
                parts.append((MIDDOT, "book", 10, t["mute"], 0, 8))
            parts += [(value, "serif", 16, t["ink"], 0), (label, "book", 9.5, t["mute"], 0, 5)]
        totals, _ = line(m, st["header_y"], parts)
        snap = T("100%", st["header_y"], SNAPSHOT, "book", 8, t["mute"], "end",
                 track=0.16, dx=-m)
        return (f'<g class="f" style="animation-delay:.05s">{totals}{snap}</g>'
                + hairline(st["hair_y"], (t["hair"], t["hair_op"])))
    width = st["fits"] - 2 * m
    tokens = ((fmt(d["stars"]), " stars"), (fmt(d["forks"]), " forks"),
              (fmt(d["followers"]), " followers"), (fmt(d["projects"]), " projects"))
    lines, cur, curw = [], [], 0.0
    for value, label in tokens:
        seg = [(value, "serif", 15, t["ink"], 0), (label, "book", 9.5, t["mute"], 0, 3)]
        w = F["serif"].width(value, 15) + F["book"].width(label, 9.5)
        dot = F["book"].width(MIDDOT, 9.5)
        if cur and curw + dot + w > width:
            lines.append(cur)
            cur, curw = list(seg), w
        else:
            if cur:
                cur = cur + [(MIDDOT, "book", 9.5, t["mute"], 0, 7)]
                curw += dot + 7
            cur = cur + seg
            curw += w
    if cur:
        lines.append(cur)
    out = []
    for i, parts in enumerate(lines):
        markup, _ = line(m, st["header_y"] + i * 21, parts)
        out.append(markup)
    snap_y = st["header_y"] + len(lines) * 21 + 6
    out.append(T("100%", snap_y, SNAPSHOT, "book", 7.5, t["mute"], "end",
                 track=0.16, dx=-m))
    return (f'<g class="f" style="animation-delay:.05s">{"".join(out)}</g>'
            + hairline(snap_y + 12, (t["hair"], t["hair_op"])))


def carpet_block(days, st, t, x0, y0):
    s = st["s"]
    ux, uy = COS30 * s, 0.5 * s
    weeks = len(days) // 7
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
        h = 0.0 if c == 0 else st["bar"] * s * max(0.14, (c / top) ** 0.5)
        k = 0.94  # inset, so the tiles keep a hairline gap like the stock drawing
        p = [f"{cx:.1f} {cy - uy * k - h:.1f}", f"{cx + ux * k:.1f} {cy - h:.1f}",
             f"{cx:.1f} {cy + uy * k - h:.1f}", f"{cx - ux * k:.1f} {cy - h:.1f}"]
        if h > 0:
            dk1, dk2 = t["shade"]
            out.append(f'<polygon points="{" ".join(p)}" fill="{col}"/>')
            out.append(f'<polygon points="{cx - ux * k:.1f} {cy - h:.1f} {cx:.1f} {cy + uy * k - h:.1f} '
                       f'{cx:.1f} {cy + uy * k:.1f} {cx - ux * k:.1f} {cy:.1f}" fill="{shade(col, dk1)}"/>')
            out.append(f'<polygon points="{cx:.1f} {cy + uy * k - h:.1f} {cx + ux * k:.1f} {cy - h:.1f} '
                       f'{cx + ux * k:.1f} {cy:.1f} {cx:.1f} {cy + uy * k:.1f}" fill="{shade(col, dk2)}"/>')
        else:
            out.append(f'<polygon points="{" ".join(p)}" fill="{col}"/>')
    if weeks >= 26:
        for wi in range(weeks):
            day = days[wi * 7]
            month = int(day["d"][5:7])
            if month != last_month:
                lx = x0 + wi * ux
                ly = y0 + (wi + 6) * uy + 20
                labels.append((lx, MONTHS[month - 1], ly))
                last_month = month
    squeezed = []
    for lx, name, ly in labels:
        if squeezed and lx - squeezed[-1][0] < 30:
            squeezed[-1] = (lx, name, ly)
        else:
            squeezed.append((lx, name, ly))
    months = "".join(T(lx, ly, name.upper(), "book", 7.5, t["mute"], "middle", track=0.14,
                       transform=f"rotate(30 {lx:.1f} {ly:.1f})")
                     for lx, name, ly in squeezed)
    bar_max = st["bar"] * s
    width = (weeks - 1 + 6) * ux + 2 * ux
    height = (weeks - 1 + 6) * uy + uy + bar_max
    return "".join(out) + months, width, height


def radar_block(values, cx, cy, r, t, names=True, ticks=True):
    angs = [72 * i for i in range(5)]
    def pt(a, f):
        rad = math.radians(a)
        return cx + r * f * math.sin(rad), cy - r * f * math.cos(rad)
    out = [f'<g fill="none" stroke="{t["mute"]}" stroke-opacity="0.55">']
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(a, 1) for a in angs))
    out.append(f'<polygon points="{poly}" stroke-dasharray="{2 * t["dash"]:.1f} {3 * t["dash"]:.1f}"/>')
    for f in (0.25, 0.5, 0.75):
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(a, f) for a in angs))
        out.append(f'<polygon points="{poly}" stroke-dasharray="{2 * t["dash"]:.1f} {3 * t["dash"]:.1f}"'
                   f' stroke-opacity="0.7"/>')
    for a in angs:
        x, y = pt(a, 1)
        out.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}"/>')
    out.append("</g>")
    fr = [min(1.0, math.log10(v + 1) / 4) if v > 0 else 0.0 for v in values]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(a, f) for a, f in zip(angs, fr)))
    out.append(f'<polygon points="{poly}" fill="{t["accent"]}" fill-opacity="{t["radar_fill"]}" '
               f'stroke="{t["accent"]}" stroke-width="1.2" stroke-linejoin="round"/>')
    for a, f in zip(angs, fr):
        x, y = pt(a, f)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.6" fill="{t["accent"]}"/>')
    if names:
        for a, name in zip(angs, ["Commit", "Issue", "PullReq", "Review", "Repo"]):
            x, y = pt(a, 1.16)
            side = math.sin(math.radians(a))
            anchor = "start" if side > 0.01 else ("end" if side < -0.01 else "middle")
            out.append(T(round(x, 1), y + 3, name.upper(), "book", 7.5, t["mute"],
                         anchor, track=0.14))
    return "".join(out)


def stats_block(rows, x, y, t, width=None, align="left"):
    """(value, label) rows; value serif, label small caps."""
    out = []
    for i, (value, label) in enumerate(rows):
        yy = y + i * 26
        if align == "left":
            out.append(T(x, yy, label.upper(), "book", 7.5, t["mute"], "start", track=0.16))
            out.append(T(x + width, yy, value, "serif", 14, t["ink"], "end", lnum=True))
        else:
            out.append(T(x, yy, label.upper(), "book", 7.5, t["mute"], "middle", track=0.16))
            out.append(T(x, yy + 15, value, "serif", 14, t["ink"], "middle", lnum=True))
    return "".join(out)


def legend_block(t, x, y):
    out = [T(x, y, "LESS", "book", 6.5, t["mute"], "start", track=0.14)]
    cx = x + 30
    for i in range(5):
        out.append(f'<rect x="{cx + i * 11:.1f}" y="{y - 6.5:.1f}" width="7" height="7" rx="1.6" '
                   f'fill="{t["ramp"][i]}"/>')
    out.append(T(cx + 5 * 11 + 4, y, "MORE", "book", 6.5, t["mute"], "start", track=0.14))
    return "".join(out)


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


def setting(d, st, t, key):
    m = st["margin"]
    days = d["days"][-st["weeks"] * 7:]
    total, best, best_fmt, streak, active = figures(days)
    out = [header_block(d, st, t)]
    cw_est = (st["weeks"] - 1 + 6) * COS30 * st["s"] + 2 * COS30 * st["s"]
    col_w = 152 if key == "w" else 128
    wr = col_w + 2 * m if key in ("w", "m") else 0
    if key in ("w", "m"):
        band = st["fits"] - wr - m
        x0 = m + max(0.0, (band - cw_est) / 2)
    else:
        x0 = (st["fits"] - cw_est) / 2
    carpet, cw, ch = carpet_block(days, st, t, x0, st["carpet_y"])
    out.append(f'<g class="f" style="animation-delay:.15s">{carpet}</g>')
    if key in ("w", "m"):
        # the right column is pinned to the right margin at every width: a nested
        # SVG of fixed width, moved left by its own width from 100%.
        legend_y = st["carpet_y"] + ch + st["legend_gap"]
        out.append(f'<g class="f" style="animation-delay:.7s">{legend_block(t, m, legend_y)}</g>')
        height = legend_y + 40
        rows = [(fmt(best["c"]), f"best day, {best_fmt}"),
                (f"{streak}d", "longest streak"),
                (fmt(active), "active days"),
                (fmt(total), "in six months")]
        inner = (f'<g class="f" style="animation-delay:.55s">'
                 f'{radar_block(d["radar"], m + col_w / 2, st["radar_cy"], st["radar_r"], t)}</g>'
                 f'<g class="f" style="animation-delay:.6s">'
                 f'{stats_block(rows, m, st["stats_top"], t, width=col_w)}</g>')
        out.append(f'<svg x="100%" y="0" width="{wr}" height="{height}" viewBox="0 0 {wr} {height}" '
                   f'overflow="visible" style="transform:translateX(-{wr}px)">{inner}</svg>')
    else:
        legend_y = st["carpet_y"] + ch + st["legend_gap"]
        if key == "s":
            lg = 104
            legend_x = (st["fits"] - lg) / 2
        else:
            legend_x = m
        out.append(f'<g class="f" style="animation-delay:.7s">{legend_block(t, legend_x, legend_y)}</g>')
        rows = [(fmt(best["c"]), f"best day, {best_fmt}"),
                (f"{streak}d", "longest streak"),
                (fmt(active), "active days")]
        if key == "n":
            band_y = legend_y + 26
            rcx = m + st["radar_r"] + 16
            out.append(f'<g class="f" style="animation-delay:.55s">'
                       f'{radar_block(d["radar"], rcx, band_y + st["radar_r"], st["radar_r"], t)}</g>')
            sx = rcx + st["radar_r"] + 34
            out.append(f'<g class="f" style="animation-delay:.6s">'
                       f'{stats_block(rows, sx, band_y + 14, t, width=st["fits"] - m - sx)}</g>')
            height = band_y + 2 * st["radar_r"] + 34
        else:
            band_y = legend_y + 24
            out.append(f'<g class="f" style="animation-delay:.55s">'
                       f'{radar_block(d["radar"], st["fits"] / 2, band_y + st["radar_r"], st["radar_r"], t)}</g>')
            sy = band_y + 2 * st["radar_r"] + 30
            out.append(f'<g class="f" style="animation-delay:.6s">'
                       f'{stats_block(rows, m, sy, t, width=st["fits"] - 2 * m)}</g>')
            height = sy + 2 * 26 + 14
    return "".join(out), height


def chrome(t):
    return (
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{t["bg0"]}"/><stop offset="1" stop-color="{t["bg1"]}"/>'
        f'</linearGradient></defs>'
        f'<rect x="0.5" y="0.5" width="100%" height="100%" rx="14" fill="url(#bg)" '
        f'stroke="{t["border"]}"/>'
    )


SNAPSHOT = ""
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def build(d):
    out = {}
    for key, t in THEMES.items():
        settings = {k: setting(d, dict(SET[k], fits=SET[k]["fits"]), t, k) for k in SET}
        title = (f"GitHub contributions: {sum(x['c'] for x in d['days'])} in the last six months, "
                 f"snapshot {SNAPSHOT}")
        out[key] = plate(title, settings, ground=None, rules=chrome(t), css=FADE, valign="top")
    return out


def update_readme_chips(repos):
    counts = {r["name"]: r["stargazers_count"] for r in repos if not r["fork"]}
    p = ROOT / "README.md"
    out, changed = [], False
    link_re = re.compile(r"^\s*(?:[-*]\s+)?\*\*\[([\w-]+)\]\(https://github\.com/Escap1ng/[\w-]+\)\*\*")
    for line_t in p.read_text(encoding="utf-8").splitlines():
        m = link_re.match(line_t)
        if m and m.group(1) in counts:
            new = re.sub(r"`★ \d+`", f"`★ {counts[m.group(1)]}`", line_t)
            changed |= new != line_t
            line_t = new
        out.append(line_t)
    if changed:
        p.write_text("\n".join(out) + "\n", encoding="utf-8")
    return changed


def main():
    global SNAPSHOT
    d = fetch()
    SNAPSHOT = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    svgs = build(d)
    for theme, svg in svgs.items():
        path = ROOT / "assets" / f"activity-{theme}.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"activity-{theme}.svg: {path.stat().st_size} bytes")
    changed = update_readme_chips(d["all_repos"])
    total, best, best_fmt, streak, active = figures(d["days"])
    print(f"snapshot {SNAPSHOT}: {total} contributions, best {best['c']} ({best_fmt}), "
          f"streak {streak}d, active {active}; readme chips updated: {changed}")


if __name__ == "__main__":
    main()
