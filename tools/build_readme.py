#!/usr/bin/env python3
"""Set README.md and the chapter plates from one body of copy.

    python tools/build_readme.py

Section openers are SVG plates, because GitHub strips CSS and these are set in
the page's own serif; the running text stays Markdown so it can be selected,
searched and read aloud. Star counts come from the live API and are woven into
the entries, so the README is never half-stale.
"""
from gh_api import USER, repositories
from plates import ROOT, T, flat, hairline, link, plate, themed, wrap

PROFILE = f"https://github.com/{USER}"
REPO = f"{PROFILE}/"

STATEMENT = ("Independent developer in Hangzhou. I build tooling for mathematical modeling "
             "contests and local-first desktop apps, and write about AI-assisted writing and "
             "code verification.")
TOOLBOX = "**Toolbox** — `Python` `TypeScript` `Electron` `Vue` `LaTeX`"

SECTIONS = [("I", "Selected Work", f"{PROFILE}?tab=repositories"),
            ("II", "Also Building", f"{PROFILE}?tab=repositories"),
            ("III", "Writing", "https://escaping.top")]

WORKS = [
    ("math-modeling-skill", "End-to-end AI skill for mathematical modeling contests: problem "
                            "analysis, algorithm selection, implementation, paper polishing. "
                            "PDF + Word delivery."),
    ("VisualLaTeX", "Visual LaTeX editor with multi-file projects and click-to-edit formulas; "
                    "editing is fully offline, with PDF preview and export via a local "
                    "Tectonic/XeLaTeX + Ghostscript service."),
    ("altiora-agent", "Log-first coding agent harness with a CLI and Windows desktop app: "
                      "streaming turns, tool calls, permission enforcement and resumable "
                      "sessions over OpenAI-compatible models."),
]

ALSO = [
    ("mathmodel-studio", "Local-first desktop agent for modeling contests: human-in-the-loop "
                         "model selection, explanations, quality gates and scoring, plus "
                         "figures, LaTeX/Word papers and de-AI checks. Electron + Python, "
                         "bring your own model."),
    ("Escaping-Notes", "Personal blog and journal: articles, collections, updates, gallery, "
                       "projects."),
    ("kaggle-store-sales-timesfm", "Kaggle Store Sales forecasting: TimesFM-3 zero-shot + "
                                   "recursive LightGBM, log-space blend (public LB 0.38980)."),
    ("deai-writing", "General-purpose de-AI writing skill: vocabulary-, structural-, and "
                     "character-level gates with bilingual rules and regression checks."),
    ("yijing-atlas", "Zhouyi divination and hexagram atlas: the 49-stalk yarrow ritual step by "
                     "step, hexagram texts with vernacular, Wang Bi commentary and modern "
                     "readings, and a 365¼-day star chart of lunar mansions, solar terms and "
                     "hexagram qi. Pure static, offline."),
]

WRITING = "[Escaping Notes](https://escaping.top) — essays and notes, a long exposure of star trails."

COLOPHON = ("Set in Cormorant Garamond; the plates are drawn by tools/plates.py, the contribution "
            "figures refreshed every six hours, and the whole printed for the author.")
COLOPHON_MARK = f"{USER.upper()} · MMXXVI"

BANNER_ALT = "Escap1ng — Altiora petamus — Independent developer in Hangzhou"
ACTIVITY_ALT = ("GitHub activity over six months: an isometric carpet, a contribution-type "
                "radar, the language ring, and the figures (auto-refreshed)")

INK = {
    "light": dict(ink="#191b1b", text="#4e5248", mute="#7d8075",
                  accent="#2f7a58", hair=("#191b1b", 0.14)),
    "dark": dict(ink="#f2f0e8", text="#c3c5ba", mute="#8d9086",
                 accent="#4fbf8f", hair=("#f2f0e8", 0.16)),
}


SECTION_SIZES = {
    "w": dict(num=25, caps=11.5, y_num=42, y_caps=74, h=96),
    "m": dict(num=23, caps=11, y_num=40, y_caps=71, h=92),
    "n": dict(num=21, caps=10, y_num=37, y_caps=66, h=86),
    "s": dict(num=19, caps=9.5, y_num=35, y_caps=63, h=82),
}

COLOPHON_SIZES = {
    "w": dict(size=13, lead=19.5, measure=560),
    "m": dict(size=12.5, lead=19, measure=400),
    "n": dict(size=12, lead=18, measure=250),
    "s": dict(size=11.5, lead=17, measure=204),
}


def section_svg(num, label, t):
    settings = {}
    for key, z in SECTION_SIZES.items():
        body = (hairline(0, t["hair"])
                + T(0, z["y_num"], num, "italic", z["num"], t["accent"], "start")
                + T(0, z["y_caps"], label.upper(), "book", z["caps"], t["ink"], "start", track=0.3))
        settings[key] = (body, z["h"])
    return plate(f"{num} · {label}", settings, valign="top")


def colophon_svg(t):
    settings = {}
    for key, z in COLOPHON_SIZES.items():
        lines = wrap("italic", z["size"], COLOPHON, z["measure"])
        y = 34.0
        body = [hairline(0, t["hair"])]
        for ln in lines:
            body.append(T("50%", y, ln, "italic", z["size"], t["text"]))
            y += z["lead"]
        y += 16
        body.append(T("50%", y, COLOPHON_MARK, "book", 9.5, t["ink"], track=0.3))
        settings[key] = ("".join(body), y + 26)
    return plate(flat(f"{COLOPHON} {COLOPHON_MARK}"), settings, valign="top")


def write_plates():
    out = {}
    for theme, t in INK.items():
        for i, (num, label, _) in enumerate(SECTIONS, start=1):
            name = f"sec-{i}-{theme}.svg"
            (ROOT / "assets" / name).write_text(section_svg(num, label, t), encoding="utf-8")
            out[f"sec-{i}"] = name
        name = f"colophon-{theme}.svg"
        (ROOT / "assets" / name).write_text(colophon_svg(t), encoding="utf-8")
        out["colophon"] = name
    return out


def build(counts):
    def chip(repo):
        return f"`★ {counts.get(repo, 0)}`"

    blocks = [
        "<!-- set by tools/build_readme.py — edit that, not this -->",
        themed("assets/banner-animated-{theme}.svg?v=800", BANNER_ALT),
        link(PROFILE, themed("assets/activity-{theme}.svg?v=800", ACTIVITY_ALT)),
        STATEMENT,
        TOOLBOX,
        link(SECTIONS[0][2], themed("assets/sec-1-{theme}.svg", "I · Selected Work")),
    ]
    for name, text in WORKS:
        blocks.append(f"**[{name}]({REPO}{name})** {chip(name)}\n\n{text}")
    blocks.append(link(SECTIONS[1][2], themed("assets/sec-2-{theme}.svg", "II · Also Building")))
    blocks.append("\n".join(f"- **[{name}]({REPO}{name})** — {text} {chip(name)}"
                            for name, text in ALSO))
    blocks.append(link(SECTIONS[2][2], themed("assets/sec-3-{theme}.svg", "III · Writing")))
    blocks.append(WRITING)
    blocks.append(themed("assets/colophon-{theme}.svg", flat(f"{COLOPHON} {COLOPHON_MARK}")))
    return "\n\n".join(blocks) + "\n"


def main():
    write_plates()
    counts = {r["name"]: r["stargazers_count"] for r in repositories() if not r["fork"]}
    text = build(counts)
    (ROOT / "README.md").write_text(text, encoding="utf-8")
    print(f"README.md: {len(text)} chars; stars: " + ", ".join(f"{k} {v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
