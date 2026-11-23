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

QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}"""

GH_USER = 'Escap1ng'


def gh_request(url, token, data=None):
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {token}',
        'User-Agent': 'profile-assets-refresh',
        'Accept': 'application/vnd.github+json',
    }, data=data.encode() if isinstance(data, str) else data)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def fetch_viewer():
    token = os.environ['GITHUB_TOKEN']
    cal = gh_request(
        'https://api.github.com/graphql',
        token,
        data=json.dumps({'query': QUERY, 'variables': {'login': GH_USER}}),
    )
    if cal.get('errors'):
        raise RuntimeError(cal['errors'])
    user = gh_request(f'https://api.github.com/users/{GH_USER}', token)
    repos = gh_request(f'https://api.github.com/users/{GH_USER}/repos?per_page=100', token)
    return {
        'followers': {'totalCount': user['followers']},
        'repositories': {'nodes': [
            {'name': r['name'], 'stargazerCount': r['stargazers_count'],
             'forkCount': r['forks_count'], 'isPrivate': r['private']}
            for r in repos
        ]},
        'contributionsCollection': {
            'contributionCalendar': cal['data']['user']['contributionsCollection']['contributionCalendar'],
        },
    }


W, H = 760, 216
X0, Y0, PITCH, CELL = 40, 82, 13, 11
MONO = 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

THEMES = {
    'light': dict(bg0='#f7faf8', bg1='#e9f0eb', border='#d2dcd5', L0='#dfe8e2', L1='#c9dfd6',
                  L2='#7fbfa1', L3='#16a36a', L4='#0b563b', label='#7d8b82', ink='#10131a',
                  sweep='#16a36a'),
    'dark': dict(bg0='#030604', bg1='#0a120e', border='#233229', L0='#121a16', L1='#143a29',
                 L2='#1c6349', L3='#16a36a', L4='#6fd3a6', label='#8a9992', ink='#e9f1ec',
                 sweep='#3fbf8a'),
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
        squeezed = []
        for x, name in labels:
            if squeezed and x - squeezed[-1][0] < 26:
                squeezed[-1] = (x, name)
            else:
                squeezed.append((x, name))
        months = ''.join(
            f'  <text x="{x}" y="{Y0 - 8}" font-family="{MONO}" font-size="10" letter-spacing="0.4" fill="{t["label"]}">{name}</text>'
            for x, name in squeezed
        )
        legend_y = 194
        legend = (
            f'  <text x="{X0}" y="{legend_y}" font-family="{MONO}" font-size="9.5" letter-spacing="0.6" fill="{t["label"]}">less</text>\n'
            f'  <rect x="{X0 + 30}" y="{legend_y - 9.5}" width="{CELL}" height="{CELL}" rx="3" fill="{t["L0"]}"/>\n'
            f'  <rect x="{X0 + 44}" y="{legend_y - 9.5}" width="{CELL}" height="{CELL}" rx="3" fill="{t["L1"]}"/>\n'
            f'  <rect x="{X0 + 58}" y="{legend_y - 9.5}" width="{CELL}" height="{CELL}" rx="3" fill="{t["L2"]}"/>\n'
            f'  <rect x="{X0 + 72}" y="{legend_y - 9.5}" width="{CELL}" height="{CELL}" rx="3" fill="{t["L3"]}"/>\n'
            f'  <rect x="{X0 + 86}" y="{legend_y - 9.5}" width="{CELL}" height="{CELL}" rx="3" fill="{t["L4"]}"/>\n'
            f'  <text x="{X0 + 101}" y="{legend_y}" font-family="{MONO}" font-size="9.5" letter-spacing="0.6" fill="{t["label"]}">more</text>'
        )
        stat_rows = [
            (100, f'best day · {best_fmt}', best['c']),
            (134, 'longest streak', f'{best_streak}d'),
            (168, 'active days', active),
        ]
        stats = '\n'.join(
            f'  <text x="456" y="{y}" font-family="{MONO}" font-size="9.5" letter-spacing="1.4" fill="{t["label"]}">{label.upper()}</text>\n'
            f'  <text x="720" y="{y + 0.5}" text-anchor="end" font-family="{MONO}" font-size="15" font-weight="600" fill="{t["ink"]}">{value}</text>'
            for y, label, value in stat_rows
        )
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub activity: {total} contributions in the last six months, snapshot {snapshot}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{t['bg0']}"/>
      <stop offset="1" stop-color="{t['bg1']}"/>
    </linearGradient>
    <linearGradient id="hdr" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t['label']}" stop-opacity="0.45"/>
      <stop offset="1" stop-color="{t['label']}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="sweepg">
      <stop stop-color="{t['sweep']}" stop-opacity="0"/>
      <stop offset=".5" stop-color="{t['sweep']}" stop-opacity=".16"/>
      <stop offset="1" stop-color="{t['sweep']}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="gclip"><rect x="{X0 - 4}" y="{Y0 - 6}" width="{(len(days) // 7 - 1) * PITCH + CELL + 100}" height="{7 * PITCH + 12}"/></clipPath>
  </defs>
  <style>@media (prefers-reduced-motion: reduce){{.sweep{{display:none}}}}</style>

  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="url(#bg)" stroke="{t['border']}"/>
  <text x="{X0}" y="46" font-family="{MONO}" font-size="16" fill="{t['ink']}" font-weight="600">{total_stars}<tspan font-weight="400" font-size="11" fill="{t['label']}"> stars · </tspan>{total_forks}<tspan font-weight="400" font-size="11" fill="{t['label']}"> forks · </tspan>{followers}<tspan font-weight="400" font-size="11" fill="{t['label']}"> followers · </tspan>{n_repos}<tspan font-weight="400" font-size="11" fill="{t['label']}"> projects</tspan></text>
  <text x="{W - 40}" y="46" text-anchor="end" font-family="{MONO}" font-size="9.5" letter-spacing="1.6" fill="{t['label']}">SNAPSHOT {snapshot}</text>
  <rect x="{X0}" y="59" width="{W - 80}" height="1" fill="url(#hdr)"/>
{months}{chr(10).join(rects)}
  <g clip-path="url(#gclip)"><rect class="sweep" x="{X0}" y="{Y0 - 6}" width="90" height="{7 * PITCH + 12}" fill="url(#sweepg)"><animateTransform attributeName="transform" type="translate" from="-110 0" to="{(len(days) // 7 - 1) * PITCH + CELL + 110} 0" dur="13s" repeatCount="indefinite"/></rect></g>
{legend}
  <line x1="436" y1="{Y0}" x2="436" y2="{Y0 + 7 * PITCH + 2}" stroke="{t['label']}" stroke-opacity="0.25"/>
{stats}
</svg>
'''

    return {theme: build(theme) for theme in THEMES}, total, best, best_streak, active


def update_readme_chips(repos):
    counts = {r['name']: r['stargazerCount'] for r in repos}
    p = ROOT / 'README.md'
    out, changed = [], False
    link_re = re.compile(r'^\s*(?:[-*]\s+)?\*\*\[([\w-]+)\]\(https://github\.com/Escap1ng/[\w-]+\)\*\*')
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
