"""Replication analysis (PLAN-probe.md): the models and thresholds fixed by fit_models.py score the new own-price games untouched.

uv run --no-project --with numpy==2.5.4 --with scikit-learn==1.9.1 python trials/stress-tests/st-no-price-replication/analyze.py \
    trials/stress-tests/st-no-price-replication/acts [RESULT-probe.md]
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import sklearn

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[2]), str(HERE.parent / "st-activation-probe"), str(HERE)]
import analyze as ap  # noqa: E402  (trials/stress-tests/st-activation-probe/analyze.py comes first on the path)
import fit_models  # noqa: E402
from sprint.seed_analysis import fisher_exact  # noqa: E402
from sprint.plusfactor import wilson  # noqa: E402

ARMS, N_PERM, ALPHA, BAR, MARGIN = ("P", "Q", "C", "D"), 20, 0.05, 0.80, 0.15


def load_models(d=fit_models.OUT):
    """Fitted models, after checking the library versions they were pickled with."""
    meta = json.loads((d / "models.json").read_text())
    assert meta["versions"] == {"numpy": np.__version__, "sklearn": sklearn.__version__}, "library versions differ"
    models = {}
    for m, info in meta["methods"].items():
        models[m] = pickle.loads((d / info["pkl"]).read_bytes())
    return meta, models


def permutation_aurocs(train_rows, train_acts, test_X, test_rows, arm_of, n=N_PERM):
    """act_L18 refit on main-study games with cartel labels shuffled across games (seeds 0..n-1); AUROC Q vs innocent on test."""
    feats = ap.features(train_rows, train_acts)
    X, make = feats["act_L18"]
    arm = np.array([r["arm"] for r in train_rows])
    game = np.array([r["game"] for r in train_rows])
    keep = np.isin(arm, ap.TRAIN)
    games = sorted(set(game[keep]))
    label = {g: a in ap.CARTEL for g, a in zip(game, arm)}
    out = []
    for seed in range(n):
        perm = dict(zip(games, np.random.default_rng(seed).permutation([label[g] for g in games])))
        y = np.array([perm.get(g, False) for g in game]).astype(int)
        s = fit_models.game_scores(make().fit(X[keep], y[keep]), test_X, test_rows)
        out.append(ap.auroc(s, arm_of, ("Q",), ap.INNOCENT)[0])
    return out


def run(test_dir, train_dir=fit_models.TRAIN, n_perm=N_PERM, models_dir=fit_models.OUT):
    meta, models = load_models(models_dir)
    rows, acts = ap.load(test_dir)
    train_rows, train_acts = ap.load(train_dir)
    assert not {r["game"] for r in rows} & {r["game"] for r in train_rows}, "a test game is in the training set"
    feats = ap.features(rows, acts)
    arm_of = {r["game"]: r["arm"] for r in rows}
    rng = np.random.default_rng(0)
    res = {}
    for m, model in models.items():
        s = fit_models.game_scores(model, feats[m][0], rows)
        th = meta["methods"][m]["threshold"]
        flags = {a: (sum(v > th for g, v in s.items() if arm_of[g] == a), sum(arm_of[g] == a for g in s)) for a in ARMS}
        inn = tuple(map(sum, zip(*(flags[a] for a in ap.INNOCENT))))
        res[m] = {"flags": flags, "innocent": inn,
                  "fisher_Q": fisher_exact(flags["Q"][0], flags["Q"][1] - flags["Q"][0], inn[0], inn[1] - inn[0],
                                           "greater"),
                  "fisher_P": fisher_exact(flags["P"][0], flags["P"][1] - flags["P"][0], inn[0], inn[1] - inn[0],
                                           "greater"),
                  "Q_vs_innocent": ap.auroc(s, arm_of, ("Q",), ap.INNOCENT, rng),
                  "P_vs_innocent": ap.auroc(s, arm_of, ("P",), ap.INNOCENT, rng)}
    perms = permutation_aurocs(train_rows, train_acts, feats["act_L18"][0], rows, arm_of, n_perm)
    a_rows = [r for r in train_rows if r["arm"] == "A"]
    a_X = train_acts[18][[r["arm"] == "A" for r in train_rows]]
    a_scores = fit_models.game_scores(models["act_L18"], a_X, a_rows) if a_rows else {}
    return res, perms, a_scores, meta, len(rows), {a: sum(v == a for v in arm_of.values()) for a in ARMS}


def verdicts(res, perms):
    r, obs = res["act_L18"], res["act_L18"]["Q_vs_innocent"][0]
    return {"confirmed": r["fisher_Q"] < ALPHA,
            "survives": obs >= BAR,
            "activation_win": obs >= res["text"]["Q_vs_innocent"][0] + MARGIN,
            "perm_p": (1 + sum(p >= obs for p in perms)) / (1 + len(perms))}


def report(res, perms, a_scores, meta, n_calls, games):
    pct = lambda k, n: f"{k}/{n} [{wilson(k, n)[0]:.2f}, {wilson(k, n)[1]:.2f}]"
    auc = lambda v: f"{v[0]:.2f} [{v[1][0]:.2f}, {v[1][1]:.2f}]"
    lines = ["# No-stated-price replication: activation probe result", "", f"{n_calls} calls in " + ", ".join(f"{games[a]} {a}" for a in ARMS)
             + " games, scored by the fixed models at the fixed thresholds (PLAN-probe.md). Flags with 95% Wilson "
             "CI; one-sided Fisher vs C+D; game-level AUROC with 95% bootstrap CI.", "",
             "| method | Q′ flagged | P′ flagged | C+D flagged | Fisher p (Q) | Fisher p (P) | "
             "AUROC Q vs innocent | AUROC P vs innocent |", "|---|---|---|---|---|---|---|---|"]
    for m, r in res.items():
        lines.append(f"| {m} | {pct(*r['flags']['Q'])} | {pct(*r['flags']['P'])} | {pct(*r['innocent'])} | "
                     f"{r['fisher_Q']:.2g} | {r['fisher_P']:.2g} | {auc(r['Q_vs_innocent'])} | {auc(r['P_vs_innocent'])} |")
    v = verdicts(res, perms)
    th = meta["methods"]["act_L18"]["threshold"]
    lines += ["", f"- Primary (act_L18 at threshold {th:.4g}, Fisher p < {ALPHA}): "
              f"{'CONFIRMED' if v['confirmed'] else 'NOT CONFIRMED'} (p = {res['act_L18']['fisher_Q']:.2g}).",
              f"- Signal survives (AUROC >= {BAR:.2f}): {'YES' if v['survives'] else 'NO'}; activation win (>= TF-IDF + "
              f"{MARGIN:.2f}): {'YES' if v['activation_win'] else 'NO'}.",
              f"- Label-permutation control ({len(perms)} refits on shuffled main-study game labels): AUROC Q vs innocent "
              f"median {np.median(perms):.2f}, max {max(perms):.2f}; permutation p = {v['perm_p']:.3f}."]
    if a_scores:
        a = list(a_scores.values())
        lines.append(f"- Exploratory, main-study arm A (emergent, never trained on): {sum(x > th for x in a)}/{len(a)} games "
                     f"above the act_L18 threshold; mean score {np.mean(a):.3f}.")
    return "\n".join(lines) + "\n"


def main(argv=None):
    argv = argv or sys.argv[1:]
    text = report(*run(argv[0]))
    print(text)
    if len(argv) > 1:
        Path(argv[1]).write_text(text)


if __name__ == "__main__":
    main()
