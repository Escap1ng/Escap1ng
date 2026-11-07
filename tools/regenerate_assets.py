#!/usr/bin/env python3
"""Regenerate the contribution panel and README star chips from live GitHub data.

Scheduled in CI (.github/workflows/refresh.yml); locally run with
GITHUB_TOKEN=<token> python tools/regenerate_assets.py
"""
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

QUERY = """query {
  viewer {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 50) {
      totalCount
      nodes { name stargazerCount forkCount isPrivate }
    }
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}"""


def fetch_viewer():
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': QUERY}).encode(),
        headers={
            'Authorization': f'Bearer {os.environ["GITHUB_TOKEN"]}',
            'User-Agent': 'profile-assets-refresh',
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        body = json.loads(r.read())
    if body.get('errors'):
        raise RuntimeError(body['errors'])
    return body['data']['viewer']


W, H = 760, 216
X0, Y0, PITCH, CELL = 42, 78, 13, 11
MONO = 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

THEMES = {
    'light': dict(bg0='#f2f5f9', bg1='#e9eef5', border='#d1d9e0', L0='#e2eaf2', L1='#c2d1e1',
                  L2='#8fa9c3', L3='#54718f', L4='#14283d', label='#7e8a9b', ink='#10131a',
                  sweep='#7fa8d9'),
    'dark': dict(bg0='#04060b', bg1='#0a1019', border='#24303f', L0='#121924', L1='#1d2c40',
                 L2='#31496a', L3='#52769f', L4='#a9c3e6', label='#8a96a8', ink='#e6edf3',
                 sweep='#88bfff'),
}


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


def panel_svg(viewer, snapshot):
    days = [{'c': d['contributionCount'], 'd': d['date']}
            for w in viewer['contributionsCollection']['contributionCalendar']['weeks']
            for d in w['contributionDays']][-26 * 7:]
    repos = [r for r in viewer['repositories']['nodes'] if not r['isPrivate']]
    total_stars = sum(r['stargazerCount'] for r in repos)
    total_forks = sum(r['forkCount'] for r in repos)
    followers = viewer['followers']['totalCount']
    n_repos = len(repos)
    total = sum(d['c'] for d in days)
    best = max(days, key=lambda d: d['c'])
    best_fmt = datetime.strptime(best['d'], '%Y-%m-%d').strftime('%b %d')
    active = sum(1 for d in days if d['c'] > 0)
    streak = best_streak = 0
    for d in days:
        streak = streak + 1 if d['c'] > 0 else 0
        best_streak = max(best_streak, streak)

    def build(theme):
        t = THEMES[theme]
        rects, labels, last_month = [], [], None
        for i, d in enumerate(days):
            wi, di = divmod(i, 7)
            if di == 0:
                m = int(d['d'][5:7])
                if m != last_month:
                    labels.append((X0 + wi * PITCH, MONTHS[m - 1]))
                    last_month = m
            rects.append(
                f'  <rect x="{X0 + wi * PITCH}" y="{Y0 + di * PITCH}" width="{CELL}" height="{CELL}" rx="3" '
                f'fill="{t["L" + str(level(d["c"]))]}"><title>{d["d"]}: {d["c"]} contributions</title></rect>'
            )
        months = ''.join(
            f'  <text x="{x}" y="{Y0 - 8}" font-family="{MONO}" font-size="10" fill="{t["label"]}">{name}</text>'
            for x, name in labels
        )
        legend_y = Y0 + 7 * PITCH + 22
        legend = (
            f'  <text x="{X0}" y="{legend_y}" font-family="{MONO}" font-size="10" fill="{t["label"]}">less</text>\n'
            f'  <rect x="{X0 + 32}" y="{legend_y - 10}" width="{CELL}" height="{CELL}" rx="3" fill="{t["L0"]}"/>\n'
            f'  <rect x="{X0 + 46}" y="{legend_y - 10}" width="{CELL}" height="{CELL}" rx="3" fill="{t["L1"]}"/>\n'
            f'  <rect x="{X0 + 60}" y="{legend_y - 10}" width="{CELL}" height="{CELL}" rx="3" fill="{t["L2"]}"/>\n'
            f'  <rect x="{X0 + 74}" y="{legend_y - 10}" width="{CELL}" height="{CELL}" rx="3" fill="{t["L3"]}"/>\n'
            f'  <rect x="{X0 + 88}" y="{legend_y - 10}" width="{CELL}" height="{CELL}" rx="3" fill="{t["L4"]}"/>\n'
            f'  <text x="{X0 + 103}" y="{legend_y}" font-family="{MONO}" font-size="10" fill="{t["label"]}">more</text>'
        )
        stats = (
            f'  <text x="460" y="{Y0 + 15}" font-family="{MONO}" font-size="10" fill="{t["label"]}">best day · {best_fmt}</text>\n'
            f'  <text x="718" y="{Y0 + 15}" font-family="{MONO}" font-size="13" fill="{t["ink"]}" font-weight="600" text-anchor="end">{best["c"]}</text>\n'
            f'  <text x="460" y="{Y0 + 50}" font-family="{MONO}" font-size="10" fill="{t["label"]}">longest streak</text>\n'
            f'  <text x="718" y="{Y0 + 50}" font-family="{MONO}" font-size="13" fill="{t["ink"]}" font-weight="600" text-anchor="end">{best_streak}d</text>\n'
            f'  <text x="460" y="{Y0 + 85}" font-family="{MONO}" font-size="10" fill="{t["label"]}">active days</text>\n'
            f'  <text x="718" y="{Y0 + 85}" font-family="{MONO}" font-size="13" fill="{t["ink"]}" font-weight="600" text-anchor="end">{active}</text>'
        )
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub activity: {total} contributions in the last six months, snapshot {snapshot}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t['bg0']}"/>
      <stop offset="1" stop-color="{t['bg1']}"/>
    </linearGradient>
    <linearGradient id="sweepg">
      <stop stop-color="{t['sweep']}" stop-opacity="0"/>
      <stop offset=".5" stop-color="{t['sweep']}" stop-opacity=".16"/>
      <stop offset="1" stop-color="{t['sweep']}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="gclip"><rect x="{X0 - 4}" y="{Y0 - 6}" width="{(len(days) // 7 - 1) * PITCH + CELL + 100}" height="{7 * PITCH + 12}"/></clipPath>
  </defs>
  <style>@media (prefers-reduced-motion: reduce){{.sweep{{display:none}}}}</style>

  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="url(#bg)" stroke="{t['border']}"/>
  <text x="{X0 - 2}" y="42" font-family="{MONO}" font-size="15" fill="{t['ink']}" font-weight="600">{total_stars}<tspan font-weight="400" font-size="12" fill="{t['label']}"> stars · </tspan>{total_forks}<tspan font-weight="400" font-size="12" fill="{t['label']}"> forks · </tspan>{followers}<tspan font-weight="400" font-size="12" fill="{t['label']}"> followers · </tspan>{n_repos}<tspan font-weight="400" font-size="12" fill="{t['label']}"> projects</tspan></text>
  <text x="{W - 42}" y="42" text-anchor="end" font-family="{MONO}" font-size="10" fill="{t['label']}">snapshot {snapshot}</text>
{months}{chr(10).join(rects)}
  <g clip-path="url(#gclip)"><rect class="sweep" x="{X0}" y="{Y0 - 6}" width="90" height="{7 * PITCH + 12}" fill="url(#sweepg)"><animateTransform attributeName="transform" type="translate" from="-110 0" to="{(len(days) // 7 - 1) * PITCH + CELL + 110} 0" dur="13s" repeatCount="indefinite"/></rect></g>
{legend}
{stats}
</svg>
'''

    return {theme: build(theme) for theme in THEMES}, total, best, best_streak, active


def update_readme_chips(repos):
    counts = {r['name']: r['stargazerCount'] for r in repos}
    p = ROOT / 'README.md'
    out, changed = [], False
    link_re = re.compile(r'^\*\*\[([\w-]+)\]\(https://github\.com/Escap1ng/[\w-]+\)\*\*')
    for line in p.read_text(encoding='utf-8').splitlines():
        m = link_re.match(line)
        if m and m.group(1) in counts:
            new = re.sub(r'`★ \d+`', f'`★ {counts[m.group(1)]}`', line)
            changed |= new != line
            line = new
        out.append(line)
    if changed:
        p.write_text('\n'.join(out) + '\n', encoding='utf-8')
    return changed


def main():
    viewer = fetch_viewer()
    snapshot = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    svgs, total, best, best_streak, active = panel_svg(viewer, snapshot)
    for theme, svg in svgs.items():
        (ROOT / 'assets' / f'activity-{theme}.svg').write_text(svg, encoding='utf-8')
    readme_changed = update_readme_chips(
        [r for r in viewer['repositories']['nodes'] if not r['isPrivate']]
    )
    print(f'snapshot {snapshot}: {total} contributions, best {best["c"]}, streak {best_streak}d, '
          f'active {active}; readme chips updated: {readme_changed}')


if __name__ == '__main__':
    main()
