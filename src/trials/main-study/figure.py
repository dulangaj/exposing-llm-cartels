"""CLI: python3 trials/main-study/figure.py [--out fig_flags.svg]

Figure 2: flag rate (95% Wilson CI) per arm for four detectors, pooled over the Qwen3-8B confirmatory runs on
fresh seeds 108-131 (24 per arm). Hand-written SVG, standard library only."""
from __future__ import annotations

import argparse
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sprint import seed_analysis as av  # noqa: E402
from sprint.plusfactor import TH, wilson  # noqa: E402

RUNS = [ROOT / "trials/main-study/ms-confirm-1/run", ROOT / "trials/main-study/ms-confirm-2/run-116-123", ROOT / "trials/main-study/ms-confirm-2/run-124-131"]
DETS = (("price_adj", "Price alone"), ("judge_agreement", "LLM judge (talk)"),
        ("price_punish", "Price + punish"), ("price_overreact", "Price + overreaction\n(price-cut test)"))
ARMS = (("P", "cartel"), ("W", "cartel"), ("B", "innocent"), ("C", "innocent"), ("D", "innocent"), ("A", "exploratory"))
NAME = {"P": "Punishing", "W": "Watched", "B": "Cost shock", "C": "Scripted talk", "D": "Silent", "A": "Long-run"}
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
COLOR = {"cartel": "#2a78d6", "innocent": "#eb6834", "exploratory": "#52514e"}
LABEL_W, PANEL_W, GAP, ROW_H, TOP, BOTTOM, GROUP_GAP = 84, 108, 22, 24, 58, 46, 10


def rates():
    """{arm: {detector: (k, n)}} over runs that reached their probe round, at the pre-specified thresholds."""
    th = TH
    runs = [r for r in av.load_runs(RUNS) if r["thinking"] is True and any(x["probe"] for x in r["rounds"])]
    out = {}
    for r in runs:
        fl = av.detector_flags(av._features(r["meta"], r["rounds"]), r["judge"], th)
        fl["price_overreact"] = fl["price_adj"] and fl["overreact"]
        for d, _ in DETS:
            if fl[d] is not None:
                k, n = out.setdefault(r["arm"], {}).get(d, (0, 0))
                out[r["arm"]][d] = (k + bool(fl[d]), n + 1)
    return out


def row_y(i):
    return TOP + i * ROW_H + ROW_H / 2 + (GROUP_GAP if i >= 2 else 0) + (GROUP_GAP if i >= 5 else 0)


def svg(by):
    width = LABEL_W + len(DETS) * (PANEL_W + GAP)
    plot_bottom = row_y(len(ARMS) - 1) + ROW_H / 2
    height = int(plot_bottom + BOTTOM)
    fp = lambda d: "{}/{}".format(*map(sum, zip(*(by[a][d] for a, k in ARMS if k == "innocent"))))
    e = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
         f'font-family="system-ui, sans-serif" font-size="10">',
         f'<rect width="{width}" height="{height}" fill="{SURFACE}"/>',
         f'<text x="6" y="14" font-size="12" fill="{INK}">Innocent firms flagged: price alone {fp("price_adj")}, '
         f'LLM judge {fp("judge_agreement")}, price + overreaction {fp("price_overreact")}</text>']
    for kind, i0, i1 in (("cartel", 0, 1), ("innocent", 2, 4), ("exploratory", 5, 5)):
        ya, yb = row_y(i0) - ROW_H / 2 + 2, row_y(i1) + ROW_H / 2 - 2
        e.append(f'<line x1="3" x2="3" y1="{ya}" y2="{yb}" stroke="{COLOR[kind]}" stroke-width="3" stroke-linecap="round"/>')
    for i, (arm, _) in enumerate(ARMS):
        e.append(f'<text x="{LABEL_W - 8}" y="{row_y(i) + 3.5}" text-anchor="end" fill="{INK}">'
                 f'{NAME[arm]}</text>')
    for c, (det, title) in enumerate(DETS):
        x0 = LABEL_W + c * (PANEL_W + GAP)
        sx = lambda v: x0 + v * PANEL_W
        lines = title.split("\n")
        tspans = "".join(f'<tspan x="{x0 + PANEL_W / 2}" dy="{12 if j else 0}">{escape(t)}</tspan>' for j, t in enumerate(lines))
        e.append(f'<text y="{TOP - 14 - 12 * (len(lines) - 1)}" text-anchor="middle" fill="{INK}" font-weight="600">{tspans}</text>')
        title = " ".join(lines)
        for v in (0, 0.5, 1):
            e.append(f'<line x1="{sx(v)}" x2="{sx(v)}" y1="{TOP - 4}" y2="{plot_bottom}" stroke="{GRID}"/>')
            if v < 1 or c == len(DETS) - 1:  # an inner panel's "1" would sit beside the next panel's "0" and read as "10"
                e.append(f'<text font-size="11" x="{sx(v)}" y="{plot_bottom + 12}" text-anchor="middle" fill="{MUTED}">{v:g}</text>')
        for i, (arm, kind) in enumerate(ARMS):
            k, n = by[arm][det]
            lo, hi = wilson(k, n)
            y, col = row_y(i), COLOR[kind]
            fill = SURFACE if kind == "exploratory" else col
            e.append(f'<g><title>{escape(title)} on {arm}: {k}/{n} flagged, CI [{lo:.2f}, {hi:.2f}]</title>'
                     f'<line x1="{sx(lo)}" x2="{sx(hi)}" y1="{y}" y2="{y}" stroke="{col}" stroke-width="2" '
                     f'stroke-linecap="round" opacity=".55"/><circle cx="{sx(k / n)}" cy="{y}" r="4" fill="{fill}" '
                     f'stroke="{col}" stroke-width="2"/></g>')
    for j, t in enumerate(("x = share of games flagged (0 to 1), 95% Wilson CI; 24 seeds per arm (Qwen3-8B, seeds 108-131).",
                           "Cartels should read 1, innocents 0.")):
        e.append(f'<text x="{LABEL_W}" y="{height - 20 + j * 12}" fill="{MUTED}">{t}</text>')
    return "\n".join(e + ["</svg>"]) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default="fig_flags.svg")
    a = p.parse_args(argv)
    by = rates()
    Path(a.out).write_text(svg(by))
    for arm, _ in ARMS:
        print(arm, " ".join(f"{d}={by[arm][d][0]}/{by[arm][d][1]}" for d, _ in DETS))
    print(a.out)


if __name__ == "__main__":
    main()
