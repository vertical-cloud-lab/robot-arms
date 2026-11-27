"""Power analysis for the CubXL reliability pre-registration.

Run:  python power.py --check-rejected   (about 35 minutes on one core; writes out/power.md,
                                          out/power.json and out/fig_*.png)
      python power.py                    (the registered rules only)
      python power.py --quick            (fewer simulations, for a smoke test)

Every decision rule here is the registered one, from prereg_stats.py; bootstrap rules use fewer
resamples than the registered 10,000 to keep the run short. `--check-rejected` (alias
`--check-bootstrap`) also simulates, on the same draws, the rules that were registered and then
replaced: H3b's percentile bootstrap, H2 refuted at 95 % and 97.5 % per axis, and H4a's
pre-review refutation rules. Its copies of the registered rules are checked against
prereg_stats.py as it runs. Seeds are fixed, so the numbers in PROTOCOL.md can be reproduced
exactly.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.special import expit, logit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import prereg_stats as ps  # noqa: E402

OUT = HERE / "out"
TARGET = 0.99

# Reference palette (dataviz skill, light mode); validated: adjacent CVD dE >= 11.8.
# Slots 2-4 are below 3:1 on white, so every line is also direct-labelled and every
# figure has a table in out/power.md.
C = ["#257de0", "#f47230", "#00b894", "#f2a600"]
MARKERS = ["o", "s", "^", "D"]
TEXT = "#191919"
TEXT2 = "#666666"
GRID = "#e6e6e6"


# ---------------------------------------------------------------------------------------
# H1: certify >= 99 % (H1a) and show < 99 % (H1b)
# ---------------------------------------------------------------------------------------

def power_certify(n: int, p: float, target: float = TARGET) -> float:
    f = ps.max_failures_certifying(n, target)
    return 0.0 if f < 0 else float(stats.binom.cdf(f, n, 1 - p))


def power_refute(n: int, p: float, target: float = TARGET) -> float:
    f = ps.min_failures_refuting(n, target)
    return float(stats.binom.sf(f - 1, n, 1 - p))


def n_for_power(fn, p: float, power: float, n_min: int = 50, n_max: int = 6000) -> int | None:
    """Smallest n at which `fn(n, p)` reaches `power` (power is a saw-tooth in n)."""
    for n in range(n_min, n_max + 1):
        if fn(n, p) >= power:
            return n
    return None


# ---------------------------------------------------------------------------------------
# H3a: one-sided Boschloo exact test, exact power from its critical region
# ---------------------------------------------------------------------------------------

def boschloo_critical_region(n1: int, n2: int, alpha: float = 0.05) -> np.ndarray:
    """Boolean (n1+1, n2+1) array: tables (x1 successes of n1 treated, x2 of n2 controls)
    that the one-sided Boschloo test rejects at `alpha` for H1: p1 > p2.

    Boschloo orders tables by Fisher's one-sided p-value and takes the supremum over the
    common success probability pi; the critical region is {Fisher p <= c*}, with c* the
    largest cut-off whose size, maximised over pi, stays within alpha.
    """
    x1 = np.arange(n1 + 1)
    x2 = np.arange(n2 + 1)
    s = x1[:, None] + x2[None, :]
    fisher_p = stats.hypergeom.sf(x1[:, None] - 1, n1 + n2, s, n1)  # P(X1 >= x1 | s)
    pis = np.unique(np.concatenate([np.linspace(0, 1, 2001), np.linspace(0.85, 1, 3001)]))
    b1 = stats.binom.pmf(x1[:, None], n1, pis[None, :])  # (n1+1, G)
    b2 = stats.binom.pmf(x2[:, None], n2, pis[None, :])  # (n2+1, G)
    cand = np.unique(fisher_p)

    def size(c: float) -> float:
        r = (fisher_p <= c).astype(float)
        return float(np.max(np.sum((b1.T @ r) * b2.T, axis=1)))

    lo, hi = 0, len(cand) - 1
    if size(cand[0]) > alpha:
        return np.zeros_like(fisher_p, dtype=bool)
    while lo < hi:  # largest index with size <= alpha
        mid = (lo + hi + 1) // 2
        if size(cand[mid]) <= alpha:
            lo = mid
        else:
            hi = mid - 1
    return fisher_p <= cand[lo]


def fisher_critical_region(n1: int, n2: int, alpha: float = 0.05) -> np.ndarray:
    x1 = np.arange(n1 + 1)
    x2 = np.arange(n2 + 1)
    s = x1[:, None] + x2[None, :]
    return stats.hypergeom.sf(x1[:, None] - 1, n1 + n2, s, n1) <= alpha


def region_power(region: np.ndarray, n1: int, p1: float, n2: int, p2: float) -> float:
    b1 = stats.binom.pmf(np.arange(n1 + 1), n1, p1)
    b2 = stats.binom.pmf(np.arange(n2 + 1), n2, p2)
    return float(b1 @ region.astype(float) @ b2)


# ---------------------------------------------------------------------------------------
# H2 and H3b: capture envelope (simulation)
# ---------------------------------------------------------------------------------------

LEVELS_ABS = np.array([1.0, 2.0, 3.0, 4.0])
TRIALS_PER_LEVEL = 20  # per signed level, so 40 per |d| on one axis
ZERO_TRIALS = 20


def logistic_curve(ed90: float, width: float):
    """p(|d|) with ED90 = ed90 and ED50 = ed90 + width (width > 0)."""
    b1 = (logit(0.5) - logit(0.9)) / width
    b0 = logit(0.9) - b1 * ed90
    return lambda d: expit(b0 + b1 * np.asarray(d, dtype=float))


def step_curve(edge: float, p_in: float = 0.995, p_out: float = 0.05):
    """A lead-in that catches everything inside `edge` and almost nothing outside."""
    return lambda d: np.where(np.asarray(d, dtype=float) <= edge, p_in, p_out)


def simulate_axis(curve, rng, zero_success: np.ndarray):
    """One axis of E2: the shared zero level plus +-1..4 mm, 20 trials per signed level."""
    d = np.concatenate([np.zeros(ZERO_TRIALS), np.repeat(LEVELS_ABS, 2 * TRIALS_PER_LEVEL)])
    p = curve(np.repeat(LEVELS_ABS, 2 * TRIALS_PER_LEVEL))
    s = np.concatenate([zero_success, (rng.random(p.size) < p).astype(int)])
    return d, s


def h2_power(curve, n_sims: int, seed: int) -> dict:
    """Rates of each registered H2 outcome (prereg_stats.h2_decision), plus the secondary
    model-free check and what v1's combined rule would have given."""
    rng = np.random.default_rng(seed)
    sup = ref = free = v1 = 0
    p0 = float(curve(0.0))
    for _ in range(n_sims):
        zero = (rng.random(ZERO_TRIALS) < p0).astype(int)
        res = []
        fails_at_2 = 0
        for _axis in ("x", "y"):
            d, s = simulate_axis(curve, rng, zero)
            res.append(ps.capture_curve(d, s))
            fails_at_2 += int(np.sum(1 - s[d == 2.0]))
        dec = ps.h2_decision(res[0], res[1], int(zero.sum()), ZERO_TRIALS)
        f = ps.h2_model_free_check(fails_at_2)
        sup += dec == "supported"
        ref += dec == "refuted"
        free += f
        v1 += (dec == "supported") and f
    return {"supported": sup / n_sims, "refuted": ref / n_sims, "model_free": free / n_sims,
            "v1_combined": v1 / n_sims}


def _resample(d, s, rng):
    out_d, out_s = [], []
    for L in np.unique(d):
        g = s[d == L]
        out_s.append(rng.choice(g, size=g.size, replace=True))
        out_d.append(np.full(g.size, L))
    return np.concatenate(out_d), np.concatenate(out_s)


def _h3b_bootstrap_axis(r_at, r_ol, d_at, s_at, d_ol, s_ol, rng, n_boot: int) -> bool:
    """The percentile-bootstrap rule v2 first registered and then rejected (kept for the check)."""
    if r_at.censored:
        return r_ol.ed90_fieller90[1] < r_at.max_offset
    reps = []
    for _ in range(n_boot):
        da, sa = _resample(d_at, s_at, rng)
        do, so = _resample(d_ol, s_ol, rng)
        ra, ro = ps.capture_curve(da, sa).radius90, ps.capture_curve(do, so).radius90
        reps.append(ra - ro)
    return float(np.quantile(reps, 0.05)) > 0


def h3b_power(curve_ol, curve_at, n_sims: int, seed: int, method: str = "registered",
              n_boot: int = 300) -> float:
    """Chance H3b is supported on both axes: `registered` (prereg_stats.h3b_axis_supported,
    the delta-method rule) or `bootstrap` (the rejected percentile-bootstrap rule)."""
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n_sims):
        z_ol = (rng.random(ZERO_TRIALS) < float(curve_ol(0.0))).astype(int)
        z_at = (rng.random(ZERO_TRIALS) < float(curve_at(0.0))).astype(int)
        ok = True
        for _axis in ("x", "y"):
            d_ol, s_ol = simulate_axis(curve_ol, rng, z_ol)
            d_at, s_at = simulate_axis(curve_at, rng, z_at)
            r_ol, r_at = ps.capture_curve(d_ol, s_ol), ps.capture_curve(d_at, s_at)
            if method == "registered":
                ok &= ps.h3b_axis_supported(r_at, r_ol)
            else:
                ok &= _h3b_bootstrap_axis(r_at, r_ol, d_at, s_at, d_ol, s_ol, rng, n_boot)
        hits += ok
    return hits / n_sims


# ---------------------------------------------------------------------------------------
# H3c: time cost (Hodges-Lehmann upper bound)
# ---------------------------------------------------------------------------------------

def h3c_power(delta_s: float, cap_s: float, sd_s: float, n: int, n_sims: int, seed: int) -> float:
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n_sims):
        t_ol = 30 + rng.gamma(4.0, sd_s / 2.0, n)  # right-skewed transfer times
        t_at = 30 + delta_s + rng.gamma(4.0, sd_s / 2.0, n)
        _hl, upper = ps.hodges_lehmann_upper(t_at, t_ol)
        hits += upper <= cap_s
    return hits / n_sims


# ---------------------------------------------------------------------------------------
# H4: ISO 9283 RP (simulation)
# ---------------------------------------------------------------------------------------

RP_PER_SIGMA = ps.RP_PER_SIGMA  # 3.615


def sigma_for_rp(rp: float) -> float:
    return rp / RP_PER_SIGMA


def h4a_power(rp_true: float, u_inst: float, n_cycles: int, n_sims: int, seed: int,
              n_boot: int = 1000) -> dict:
    """Rates of each registered H4a outcome (prereg_stats.h4a_decision) for an arm whose true RP
    is `rp_true` at all five poses, seen through an instrument with expanded uncertainty
    `u_inst` (k = 2), i.e. u = U / 2 per axis."""
    rng = np.random.default_rng(seed)
    u_axis = u_inst / 2
    s_tot = math.hypot(sigma_for_rp(rp_true), u_axis)
    sup = cert = ref = 0
    for _ in range(n_sims):
        poses = [rng.normal(0, s_tot, (n_cycles, 3)) for _pose in range(5)]
        label, certified = ps.h4a_decision(poses, u_axis, u_inst, n_boot=n_boot,
                                           seed=int(rng.integers(1 << 30)))
        sup += label == "supported"
        cert += certified
        ref += label == "refuted"
    return {"meets": sup / n_sims, "certified": cert / n_sims, "refuted": ref / n_sims}


def h4bc_power(rp_unloaded: float, d_payload: float, slope_per_100mm: float, reach_mm: np.ndarray,
               u_inst: float, n_cycles: int, n_sims: int, seed: int, n_boot: int = 500) -> dict:
    """Chance H4b and H4c are supported (prereg_stats.h4bc_decisions)."""
    rng = np.random.default_rng(seed)
    centre = float(np.mean(reach_mm))
    hits_b = hits_c = 0
    for _ in range(n_sims):
        cells = {}
        for k, r in enumerate(reach_mm):
            for load in (0, 1):
                rp = rp_unloaded + load * d_payload + slope_per_100mm * (r - centre) / 100
                s_tot = math.hypot(sigma_for_rp(max(rp, 1e-6)), u_inst / 2)
                cells[(k, load)] = rng.normal(0, s_tot, (n_cycles, 3))
        out = ps.h4bc_decisions(cells, list(reach_mm), n_boot=n_boot, seed=int(rng.integers(1 << 30)))
        hits_b += out["h4b"] == "supported"
        hits_c += out["h4c"] == "supported"
    return {"h4b": hits_b / n_sims, "h4c": hits_c / n_sims}


def compute_h2(res: dict, sims: int) -> None:
    res["h2_by_width"] = {}
    for w in (0.25, 0.5, 1.0):
        rows = []
        for e in (0.5, 0.8, 1.0, 1.15, 1.5, 2.0, 2.5, 3.0):
            r = h2_power(logistic_curve(e, w), sims, seed=int(1000 * e + 10 * w))
            rows.append({"ed90": e, **r})
        res["h2_by_width"][str(w)] = rows
    res["h2_step"] = []
    for edge in (1.5, 2.5, 3.0, 3.5):
        r = h2_power(step_curve(edge), sims, seed=int(100 * edge))
        res["h2_step"].append({"edge_mm": edge, **r})


def compute_h4(res: dict, quick: bool) -> None:
    h4sims = 100 if quick else 500
    res["h4_sims"] = h4sims
    res["h4a"] = []
    for rp in (0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13):
        res["h4a"].append({"rp_true": rp, **h4a_power(rp, 0.025, 30, h4sims, seed=int(1000 * rp),
                                                       n_boot=1000)})
    reach = np.array([350.0, 270.0, 430.0, 270.0, 430.0])
    res["h4bc"] = []
    for d_pay, slope in ((0.005, 0.005), (0.01, 0.01), (0.02, 0.02)):
        r = h4bc_power(0.06, d_pay, slope, reach, 0.025, 30, min(h4sims, 300), seed=int(1e4 * d_pay))
        res["h4bc"].append({"rp_unloaded": 0.06, "payload_increase": d_pay,
                            "slope_per_100mm": slope, "reach_mm": reach.tolist(), **r})


# ---------------------------------------------------------------------------------------
# Rules registered earlier and then rejected, simulated on the same draws (--check-rejected)
# ---------------------------------------------------------------------------------------

H2_LEVELS = (0.95, 0.975, 0.99)


def _h2_axis_label_at(res, zero_k: int, zero_n: int, level: float, threshold: float = 1.15) -> str:
    """ps.h2_axis_decision with both refutation bounds at one-sided `level` instead of 99 %.
    At level = 0.99 it is the registered rule, and h2_refutation_by_level checks that."""
    supported = False
    if res.censored:
        supported = res.pooled_lower_ge2 >= 0.90
    elif res.slope_negative:
        supported = res.ed90_lower95 > threshold
    refuted = ps.cp_upper(zero_k, zero_n, alpha=1 - level) < 0.90
    if not refuted and not res.censored and res.slope_negative:
        z = float(stats.norm.ppf(level))
        refuted = ps.fieller_interval(res.fit.beta, res.fit.cov, 0.9, z)[1] < threshold
    if supported and refuted:
        return "inconclusive"
    return "supported" if supported else ("refuted" if refuted else "inconclusive")


def h2_refutation_by_level(curve, n_sims: int, seed: int) -> dict:
    """How often H2 is refuted (either axis) with the per-axis refutation bound at 95 %, 97.5 %
    and 99 %. Same seed and draw order as h2_power, so the 99 % column equals its 'refuted'."""
    rng = np.random.default_rng(seed)
    hits = {lv: 0 for lv in H2_LEVELS}
    p0 = float(curve(0.0))
    for _ in range(n_sims):
        zero = (rng.random(ZERO_TRIALS) < p0).astype(int)
        res = []
        for _axis in ("x", "y"):
            d, s = simulate_axis(curve, rng, zero)
            res.append(ps.capture_curve(d, s))
        k0 = int(zero.sum())
        for lv in H2_LEVELS:
            hits[lv] += "refuted" in [_h2_axis_label_at(r, k0, ZERO_TRIALS, lv) for r in res]
        registered = ps.h2_decision(res[0], res[1], k0, ZERO_TRIALS) == "refuted"
        if registered != ("refuted" in [_h2_axis_label_at(r, k0, ZERO_TRIALS, 0.99) for r in res]):
            raise AssertionError("the 99 % copy of the H2 rule disagrees with prereg_stats")
    return {str(lv): hits[lv] / n_sims for lv in H2_LEVELS}


def compute_h2_levels(res: dict, sims: int) -> None:
    """Five times the main table's campaigns, with the same seeds, so the first `sims` of them are
    the main table's and the boundary rate is known to about +-0.3 percentage points."""
    n = 5 * sims
    rows = []
    for w in (0.25, 0.5, 1.0):
        for e in (0.8, 1.0, 1.15):
            rows.append({"width": w, "ed90": e, "n_sims": n,
                         **h2_refutation_by_level(logistic_curve(e, w), n, seed=int(1000 * e + 10 * w))})
    res["h2_refutation_levels"] = rows


def h4a_rejected_rules(rp_true: float, u_inst: float, n_cycles: int, n_sims: int, seed: int,
                       n_boot: int = 1000) -> dict:
    """How often H4a is refuted under four refutation rules, on the same draws as h4a_power:
    the pre-review rule (one-sided 95 % lower bound above 0.10 mm at any pose), Bonferroni alone
    (99 % per pose, against 0.10 mm), the instrument adjustment alone (95 %, against
    rp_refutation_threshold) and the registered rule (99 %, against that threshold)."""
    rng = np.random.default_rng(seed)
    u_axis = u_inst / 2
    s_tot = math.hypot(sigma_for_rp(rp_true), u_axis)
    thr = ps.rp_refutation_threshold(0.10, u_axis)
    rules = {"pre_review_95_vs_spec": (0.95, 0.10), "bonferroni_99_vs_spec": (0.99, 0.10),
             "adjusted_95_vs_threshold": (0.95, thr), "registered_99_vs_threshold": (0.99, thr)}
    hits = dict.fromkeys(rules, 0)
    for sim in range(n_sims):
        poses = [rng.normal(0, s_tot, (n_cycles, 3)) for _pose in range(5)]
        seed_s = int(rng.integers(1 << 30))
        refuted = dict.fromkeys(rules, False)
        for i, pts in enumerate(poses):
            rp, se, t_all = ps._bootstrap_t_draws(pts, n_boot, seed_s + i)
            for name, (level, bar) in rules.items():
                refuted[name] |= bool((rp - float(np.quantile(t_all, level)) * se) > bar)
        if sim < 25:  # spot-check the copy against the registered function (it costs a second bootstrap)
            label, _cert = ps.h4a_decision(poses, u_axis, u_inst, n_boot=n_boot, seed=seed_s)
            if (label == "refuted") != refuted["registered_99_vs_threshold"]:
                raise AssertionError("the copy of the H4a refutation rule disagrees with prereg_stats")
        for name in rules:
            hits[name] += refuted[name]
    return {"rp_true": rp_true, **{k: v / n_sims for k, v in hits.items()}}


def compute_h4a_rejected(res: dict, quick: bool) -> None:
    n = 100 if quick else 500
    res["h4a_rejected"] = [h4a_rejected_rules(rp, 0.025, 30, n, seed=int(1000 * rp))
                           for rp in (0.09, 0.10, 0.11, 0.12)]


# ---------------------------------------------------------------------------------------
# D11: how often the run-of-failures stop fires (PROTOCOL.md §10, rule 3)
# ---------------------------------------------------------------------------------------

def d11_e1_cell(q: float, n_loads: int = 300, run: int = 3) -> dict:
    """E1 clause, exact: a cell's loads fail independently with probability q, and `run` failed
    loads in a row stop the block. The count restarts after a stop. Runs are counted across
    block boundaries, so these are upper bounds for counting within blocks."""
    p_all = np.zeros(run)  # P(current run length = j)
    p_all[0] = 1.0
    p_clean = p_all.copy()  # the same, on paths with no stop yet
    expected = 0.0
    for _ in range(n_loads):
        stop = q * p_all[-1]
        expected += stop
        p_all = np.concatenate([[(1 - q) * p_all.sum() + stop], q * p_all[:-1]])
        p_clean = np.concatenate([[(1 - q) * p_clean.sum()], q * p_clean[:-1]])
    mean_wait = sum(q ** -j for j in range(1, run + 1))  # expected loads to the first run
    return {"q": q, "expected_stops": float(expected), "p_any_stop": 1 - float(p_clean.sum()),
            "mean_loads_to_first_stop": float(mean_wait)}


def d11_e1_window(q: float, n_sims: int, seed: int, n_loads: int = 300, k: int = 5,
                  window: int = 20) -> dict:
    """An optional extra E1 clause, simulated: `k` failed loads among a cell's last `window`
    loads stop the block (v1 had it, and v2 until the review). The window empties after a stop."""
    rng = np.random.default_rng(seed)
    stops = any_stop = 0
    first = []
    for _ in range(n_sims):
        fails = rng.random(n_loads) < q
        recent: list[bool] = []
        n_stops = 0
        for i, f in enumerate(fails):
            recent.append(bool(f))
            if len(recent) > window:
                recent.pop(0)
            if sum(recent) >= k:
                n_stops += 1
                if n_stops == 1:
                    first.append(i + 1)
                recent = []
        stops += n_stops
        any_stop += n_stops > 0
    return {"q": q, "n_sims": n_sims, "expected_stops": stops / n_sims, "p_any_stop": any_stop / n_sims,
            "median_loads_to_first_stop": float(np.median(first)) if first else None}


def d11_e2_task(q_ol: float, q_at: float, pairs_per_block: int, n_sims: int, seed: int,
                passes: int = 20, levels: int = 21) -> dict:
    """E2 clause, simulated on the registered schedule (§9): for one task, `passes` passes over
    the 21 levels in random order, each level a pair of loads (OL and AT); blocks of
    `pairs_per_block` pairs; 2 failed zero-offset loads in one block stop it, and the rest of the
    schedule goes on in the next block."""
    rng = np.random.default_rng(seed)
    stops = 0
    first_stop_pairs = []
    for _ in range(n_sims):
        seq = np.concatenate([rng.permutation(levels) for _p in range(passes)])  # level 0 = zero
        fails_in_block = in_block = 0
        n_stops = 0
        for i, lv in enumerate(seq):
            if lv == 0:
                fails_in_block += int(rng.random() < q_ol) + int(rng.random() < q_at)
            in_block += 1
            if fails_in_block >= 2:
                n_stops += 1
                if n_stops == 1:
                    first_stop_pairs.append(i + 1)
                fails_in_block = in_block = 0
            elif in_block == pairs_per_block:
                fails_in_block = in_block = 0
        stops += n_stops
    caught = len(first_stop_pairs) / n_sims
    return {"q_ol": q_ol, "q_at": q_at, "pairs_per_block": pairs_per_block, "n_sims": n_sims,
            "expected_stops": stops / n_sims, "p_any_stop": caught,
            "median_pairs_to_first_stop": float(np.median(first_stop_pairs)) if first_stop_pairs else None}


def compute_d11(res: dict, quick: bool) -> None:
    qs = (0.002, 0.01, 0.025, 0.07, 0.15, 0.30, 0.50)
    n = 2000 if quick else 20000
    res["d11_e1"] = [d11_e1_cell(q) for q in qs]
    res["d11_e1_window"] = [d11_e1_window(q, n // 4, seed=12000 + i) for i, q in enumerate(qs)]
    rows = []
    # Planning scenario (e2_expected_failures): carriers 0 % OL and 1 % AT at zero offset; single
    # vials 2.5 % OL and 2 % AT. Then a cell gone wrong: zero-offset success 90 %, 80 %, 50 %.
    for k, (q_ol, q_at) in enumerate([(0.0, 0.01), (0.025, 0.02), (0.10, 0.10), (0.20, 0.20), (0.50, 0.50)]):
        rows.append(d11_e2_task(q_ol, q_at, 15, n, seed=11000 + k))
    res["d11_e2"] = rows


# ---------------------------------------------------------------------------------------
# Expected failures (so, human resets) in E2 under one plausible scenario
# ---------------------------------------------------------------------------------------

def e2_expected_failures() -> dict:
    """Expected failed loads per E2 cell, which is roughly the number of human resets.

    Scenario (assumptions, not data): carrier OL capture ED90 2.8 mm with ED50 3.2 mm in x
    and y, and 2 and 4 degrees of yaw past the lead-in (byu-vcl PR 272: the lead-in covers
    about +-1.4 degrees), so 97 % and 100 % fail there. Single-vial OL pocket: 97.5 % at zero
    offset, ED90 0.2 mm, ED50 0.5 mm, and every yaw level fails. AT cells: 1 % (carrier)
    and 2 % (vial) at every level.
    """
    xy = np.repeat([1.0, 2.0, 3.0, 4.0], 2 * TRIALS_PER_LEVEL)
    c_ol = logistic_curve(2.8, 0.4)
    v_ol = logistic_curve(0.2, 0.3)
    out = {
        "carrier_OL": float(ZERO_TRIALS * (1 - c_ol(0.0)) + 2 * np.sum(1 - c_ol(xy))
                            + 2 * TRIALS_PER_LEVEL * (0.97 + 1.0)),
        "carrier_AT": 0.01 * 420,
        "vial_OL": float(ZERO_TRIALS * (1 - v_ol(0.0)) + 2 * np.sum(1 - v_ol(xy))
                         + 2 * TRIALS_PER_LEVEL * 2),
        "vial_AT": 0.02 * 420,
    }
    out["total"] = sum(out.values())
    trimmed = float(ZERO_TRIALS * (1 - v_ol(0.0)) + 2 * np.sum(1 - v_ol(xy[xy <= 2.0]))
                    + 2 * TRIALS_PER_LEVEL * 1)
    out["vial_OL_if_trimmed_to_2mm_and_2deg"] = trimmed
    return out


# ---------------------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------------------

def _style(ax, title: str, xlabel: str, ylabel: str):
    ax.set_title(title, loc="left", fontsize=11, color=TEXT)
    ax.set_xlabel(xlabel, color=TEXT2)
    ax.set_ylabel(ylabel, color=TEXT2)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#bdbdbd")
    ax.tick_params(colors=TEXT2)


def fig_h1(res: dict, path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), dpi=150)
    ns = res["n_values"]
    for i, n in enumerate(ns):
        ps_ = np.array(res["h1a_grid"])
        pw = np.array(res["h1a_power"][str(n)])
        axes[0].plot(ps_ * 100, pw, color=C[i], lw=2, marker=MARKERS[i], markevery=12, ms=6,
                     label=f"n = {n}")
        j = int(np.argmin(np.abs(ps_ - 0.9975)))
        axes[0].annotate(f"n = {n}", (ps_[j] * 100, pw[j]), textcoords="offset points",
                         xytext=(4, -10 + 3 * i), fontsize=8, color=TEXT)
    axes[0].axhline(0.8, color="#9c9c9c", lw=1, ls="--")
    _style(axes[0], "H1a: chance of certifying ≥ 99 %", "true success rate per load (%)",
           "power (exact lower bound ≥ 99 %)")
    axes[0].set_ylim(0, 1)
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    for i, n in enumerate(ns):
        ps_ = np.array(res["h1b_grid"])
        pw = np.array(res["h1b_power"][str(n)])
        axes[1].plot(ps_ * 100, pw, color=C[i], lw=2, marker=MARKERS[i], markevery=12, ms=6,
                     label=f"n = {n}")
    axes[1].axhline(0.8, color="#9c9c9c", lw=1, ls="--")
    _style(axes[1], "H1b: chance of showing < 99 %", "true success rate per load (%)",
           "power (exact upper bound < 99 %)")
    axes[1].set_ylim(0, 1)
    axes[1].legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_h2(res: dict, path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=150)
    for i, (w, rows) in enumerate(res["h2_by_width"].items()):
        e = [r["ed90"] for r in rows]
        pw = [r["supported"] for r in rows]
        # No end labels: all three curves end at 1.0 and the labels would collide. The legend,
        # the marker shapes and the table in power.md identify the series.
        ax.plot(e, pw, color=C[i], lw=2, marker=MARKERS[i], ms=7, label=f"ED50 − ED90 = {w} mm")
    ax.axvline(1.15, color="#9c9c9c", lw=1, ls=":")
    ax.annotate("threshold 1.15 mm", (1.15, 0.72), textcoords="offset points", xytext=(4, 0),
                fontsize=8, color=TEXT2)
    ax.axhline(0.8, color="#9c9c9c", lw=1, ls="--")
    _style(ax, "H2: chance H2 is supported (both axes)", "true ED90 (mm)", "probability")
    ax.set_ylim(0, 1.02)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_h3a(res: dict, path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=150)
    for i, row in enumerate(res["h3a_curves"]):
        # Curves converge near 1.0 at the right, so no end labels; legend, markers and the
        # table in power.md identify them.
        ax.plot(row["n"], row["power"], color=C[i], lw=2, marker=MARKERS[i], ms=6,
                label=row["label"])
    ax.axhline(0.8, color="#9c9c9c", lw=1, ls="--")
    ax.axvline(300, color="#9c9c9c", lw=1, ls=":")
    _style(ax, "H3a: Boschloo one-sided power, AT vs OL single vials", "loads per condition",
           "power")
    ax.set_ylim(0, 1.02)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_design_e2(path: Path):
    """The E2 design over the planning scenario's capture curves (assumptions, not data)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = np.linspace(0, 4.2, 300)
    curves = [
        ("Carrier, open loop (ED90 2.8 mm)", logistic_curve(2.8, 0.4)),
        ("Carrier, corrected (flat 99.5 %)", lambda x: np.full_like(np.asarray(x, float), 0.995)),
        ("Single vial, open loop (ED90 0.2 mm)", logistic_curve(0.2, 0.3)),
        ("Single vial, corrected (ED90 3.0 mm)", logistic_curve(3.0, 0.5)),
    ]
    label_at = [3.05, 1.6, 0.62, 3.55]
    fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=150)
    for i, (name, f) in enumerate(curves):
        ax.plot(d, f(d), color=C[i], lw=2, label=name)
        lv = np.array([0, 1, 2, 3, 4], float)
        ax.plot(lv, f(lv), ls="none", marker=MARKERS[i], ms=7, color=C[i],
                markeredgecolor="white", markeredgewidth=1.5)
        x = label_at[i]
        ax.annotate(name.split(" (")[0], (x, float(f(x))), textcoords="offset points",
                    xytext=(6, 6 if i != 2 else -14), fontsize=8, color=TEXT)
    ax.axhline(0.9, color="#9c9c9c", lw=1, ls="--")
    ax.annotate("90 % (ED90)", (4.2, 0.9), textcoords="offset points", xytext=(-58, 4),
                fontsize=8, color=TEXT2)
    ax.axvline(1.15, color="#9c9c9c", lw=1, ls=":")
    ax.annotate("±1.15 mm worst-case\narm error (#266)", (1.15, 0.45), textcoords="offset points",
                xytext=(5, 0), fontsize=8, color=TEXT2)
    _style(ax, "E2 design: 20 loads at each level, on the planning scenario's curves",
           "injected offset |d| on x or y (mm)", "probability a load succeeds")
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_ylim(-0.02, 1.05)
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2)
    fig.text(0.01, 0.01, "Curves: planning assumptions from power.py, not data. Markers: tested levels "
             "(20 loads at 0; 40 per axis at 1-4 mm).", fontsize=7, color=TEXT2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path)
    plt.close(fig)


def fig_h4(res: dict, path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 5.0), dpi=150)
    rows = res["h4a"]
    x = [r["rp_true"] for r in rows]
    ax.plot(x, [r["meets"] for r in rows], color=C[0], lw=2, marker=MARKERS[0], ms=7,
            label="meets: point estimate ≤ 0.10 mm at all 5 poses")
    ax.plot(x, [r["certified"] for r in rows], color=C[1], lw=2, marker=MARKERS[1], ms=7,
            label="certified: bootstrap-t upper bound ≤ 0.10 mm at all 5")
    ax.plot(x, [r.get("refuted", 0.0) for r in rows], color=C[2], lw=2, marker=MARKERS[2], ms=7,
            label="refuted: bootstrap-t lower bound above the instrument-adjusted threshold")
    ax.axvline(0.10, color="#9c9c9c", lw=1, ls=":")
    ax.annotate("spec 0.10 mm", (0.10, 0.5), textcoords="offset points", xytext=(4, 0),
                fontsize=8, color=TEXT2)
    ax.axhline(0.8, color="#9c9c9c", lw=1, ls="--")
    _style(ax, "H4a outcomes: 30 cycles per pose, instrument U = 0.025 mm (k = 2)",
           "true arm RP (mm)", "probability")
    ax.set_ylim(0, 1.02)
    ax.legend(frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=1)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# ---------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--check-rejected", "--check-bootstrap", dest="check_rejected", action="store_true",
                    help="also simulate the rules that were registered and then rejected, on the same "
                         "draws: H3b's percentile bootstrap, H2 refuted at 95 %% and 97.5 %% per axis, "
                         "and H4a's pre-review refutation rules")
    ap.add_argument("--h2-only", action="store_true",
                    help="recompute only the H2 rows and keep the rest of out/power.json")
    ap.add_argument("--h4-only", action="store_true",
                    help="recompute only the H4 rows and keep the rest of out/power.json")
    ap.add_argument("--extras-only", action="store_true",
                    help="recompute only the D11 stop rates (and, with --check-rejected, the H2 and H4a "
                         "rejected-rule rows) and keep the rest of out/power.json")
    ap.add_argument("--figures-only", action="store_true",
                    help="re-draw figures and power.md from out/power.json without simulating")
    args = ap.parse_args()
    if args.figures_only:
        res = json.loads((OUT / "power.json").read_text())
        fig_h1(res, OUT / "fig_power_h1.png")
        fig_h2(res, OUT / "fig_power_h2.png")
        fig_h3a(res, OUT / "fig_power_h3a.png")
        fig_h4(res, OUT / "fig_power_h4.png")
        fig_design_e2(OUT / "fig_design_e2.png")
        write_markdown(res, OUT / "power.md")
        return
    sims = 300 if args.quick else 2000
    OUT.mkdir(exist_ok=True)
    t0 = time.time()
    if args.h2_only:
        res = json.loads((OUT / "power.json").read_text())
        compute_h2(res, res["sims"])
        (OUT / "power.json").write_text(json.dumps(res, indent=1))
        fig_h2(res, OUT / "fig_power_h2.png")
        write_markdown(res, OUT / "power.md")
        print(f"H2 redone in {time.time() - t0:.0f}s")
        return
    if args.h4_only:
        res = json.loads((OUT / "power.json").read_text())
        compute_h4(res, args.quick)
        res["runtime_s"] = res.get("runtime_s", 0.0)
        (OUT / "power.json").write_text(json.dumps(res, indent=1))
        fig_h4(res, OUT / "fig_power_h4.png")
        write_markdown(res, OUT / "power.md")
        print(f"H4 redone in {time.time() - t0:.0f}s")
        return
    if args.extras_only:
        res = json.loads((OUT / "power.json").read_text())
        compute_d11(res, args.quick)
        if args.check_rejected:
            compute_h2_levels(res, res["sims"])
            compute_h4a_rejected(res, args.quick)
        (OUT / "power.json").write_text(json.dumps(res, indent=1))
        write_markdown(res, OUT / "power.md")
        print(f"extras redone in {time.time() - t0:.0f}s")
        return
    res: dict = {"sims": sims}

    # ---- H1 -------------------------------------------------------------------------
    ns = [300, 473, 628, 1000]
    res["n_values"] = ns
    g_a = np.round(np.linspace(0.985, 1.0, 151), 5)
    g_b = np.round(np.linspace(0.94, 0.995, 111), 5)
    res["h1a_grid"] = g_a.tolist()
    res["h1b_grid"] = g_b.tolist()
    res["h1a_power"] = {str(n): [power_certify(n, p) for p in g_a] for n in ns}
    res["h1b_power"] = {str(n): [power_refute(n, p) for p in g_b] for n in ns}
    res["h1a_table"] = [
        {"p": p, **{str(n): power_certify(n, p) for n in ns}} for p in (0.99, 0.995, 0.997, 0.998, 0.999, 0.9995)
    ]
    res["h1b_table"] = [
        {"p": p, **{str(n): power_refute(n, p) for n in ns}} for p in (0.95, 0.96, 0.97, 0.975, 0.98, 0.985, 0.99)
    ]
    res["h1a_n_needed"] = [
        {"p": p, "n80": n_for_power(power_certify, p, 0.8, 299), "n90": n_for_power(power_certify, p, 0.9, 299)}
        for p in (0.997, 0.998, 0.999, 0.9995)
    ]
    res["h1b_n_needed"] = [
        {"p": p, "n80": n_for_power(power_refute, p, 0.8), "n90": n_for_power(power_refute, p, 0.9)}
        for p in (0.95, 0.97, 0.98, 0.985)
    ]
    res["thresholds"] = {str(n): {"max_fail_certify": ps.max_failures_certifying(n),
                                  "min_fail_refute": ps.min_failures_refuting(n)} for n in ns}
    print(f"H1 done {time.time() - t0:.0f}s", flush=True)

    # ---- H3a --------------------------------------------------------------------------
    scen = [(0.90, 0.99), (0.95, 0.99), (0.97, 0.995), (0.97, 0.99), (0.98, 0.995), (0.99, 0.999)]
    region300 = boschloo_critical_region(300, 300)
    fisher300 = fisher_critical_region(300, 300)
    # check: Boschloo size stays within alpha
    res["h3a_size_check"] = max(region_power(region300, 300, p, 300, p) for p in np.linspace(0.5, 0.9999, 400))
    res["h3a_table"] = []
    for p_ol, p_at in scen:
        row = {"p_ol": p_ol, "p_at": p_at,
               "boschloo_300": region_power(region300, 300, p_at, 300, p_ol),
               "fisher_300": region_power(fisher300, 300, p_at, 300, p_ol)}
        res["h3a_table"].append(row)
    curves = []
    n_grid = [150, 300, 450, 600, 800, 1000]
    regions = {n: boschloo_critical_region(n, n) for n in n_grid}
    for p_ol, p_at in [(0.95, 0.99), (0.97, 0.995), (0.97, 0.99), (0.98, 0.995)]:
        curves.append({"label": f"{p_ol:.0%} → {p_at:.1%}".replace(".0%", "%"), "n": n_grid,
                       "power": [region_power(regions[n], n, p_at, n, p_ol) for n in n_grid]})
    res["h3a_curves"] = curves
    # validate the critical-region approach against scipy on one table
    k_ol, k_at = 285, 296
    pf_obs = stats.hypergeom.sf(k_at - 1, 600, k_at + k_ol, 300)
    res["h3a_validation"] = {"table": [k_at, 300, k_ol, 300],
                             "scipy_boschloo_p": ps.boschloo_greater(k_at, 300, k_ol, 300),
                             "in_region": bool(region300[k_at, k_ol]),
                             "fisher_p": float(pf_obs)}
    print(f"H3a done {time.time() - t0:.0f}s", flush=True)

    # ---- H2 ---------------------------------------------------------------------------
    compute_h2(res, sims)
    if args.check_rejected:
        compute_h2_levels(res, sims)
    print(f"H2 done {time.time() - t0:.0f}s", flush=True)

    # ---- H3b --------------------------------------------------------------------------
    h3b = []
    scen_b = [
        ("OL pocket ED90 0.3 mm, AT ED90 3.0 mm", logistic_curve(0.3, 0.3), logistic_curve(3.0, 0.5)),
        ("OL p(0) = 80 %, AT ED90 3.0 mm", logistic_curve(-0.2, 0.4), logistic_curve(3.0, 0.5)),
        ("OL ED90 0.3 mm, AT catches all to 4 mm", logistic_curve(0.3, 0.3), step_curve(5.0, 0.995, 0.995)),
        ("OL ED90 0.3 mm, AT ED90 1.0 mm", logistic_curve(0.3, 0.3), logistic_curve(1.0, 0.4)),
        ("OL ED90 0.3 mm, AT ED90 0.6 mm", logistic_curve(0.3, 0.3), logistic_curve(0.6, 0.3)),
        ("no effect: both ED90 0.3 mm", logistic_curve(0.3, 0.3), logistic_curve(0.3, 0.3)),
        ("no effect: both ED90 0.3 mm, OL sharper (ED50 − ED90 0.3 vs 1.0 mm)",
         logistic_curve(0.3, 0.3), logistic_curve(0.3, 1.0)),
    ]
    for label, c_ol, c_at in scen_b:
        h3b.append({"scenario": label, "power": h3b_power(c_ol, c_at, sims, seed=len(label))})
    res["h3b"] = h3b
    if args.check_rejected:
        chk = []
        for label, c_ol, c_at in scen_b[3:]:
            chk.append({"scenario": label,
                        "registered": h3b_power(c_ol, c_at, 200, seed=7, method="registered"),
                        "bootstrap": h3b_power(c_ol, c_at, 200, seed=7, method="bootstrap", n_boot=300)})
        res["h3b_bootstrap_check"] = chk
    print(f"H3b done {time.time() - t0:.0f}s", flush=True)

    # ---- H3c --------------------------------------------------------------------------
    res["h3c"] = [{"delta_s": d, "cap_s": 5.0, "sd_s": 3.0,
                   "power": h3c_power(d, 5.0, 3.0, 300, min(sims, 500), seed=int(10 * d))}
                  for d in (2.0, 3.0, 4.0, 4.5, 5.0)]
    print(f"H3c done {time.time() - t0:.0f}s", flush=True)

    # ---- MTBI precision -----------------------------------------------------------------
    rows = []
    for q in (0.001, 0.002, 0.005, 0.01, 0.02):
        n_tr = 600
        k = max(int(round(q * n_tr)), 0)
        est, lo, hi = ps.mtbi_crude(n_tr, k) if k > 0 else (math.inf, ps.mtbi_crude(n_tr, 0)[1], math.inf)
        rows.append({"q": q, "transfers": n_tr, "expected_interventions": q * n_tr,
                     "mtbi_true": 1 / q, "mtbi_ci_at_expected": [lo, hi], "s50_true": (1 - q) ** 50})
    res["mtbi"] = rows

    # ---- H4 ---------------------------------------------------------------------------
    compute_h4(res, args.quick)
    if args.check_rejected:
        compute_h4a_rejected(res, args.quick)
    print(f"H4 done {time.time() - t0:.0f}s", flush=True)

    compute_d11(res, args.quick)
    res["e2_burden"] = e2_expected_failures()
    res["runtime_s"] = time.time() - t0
    (OUT / "power.json").write_text(json.dumps(res, indent=1))
    fig_h1(res, OUT / "fig_power_h1.png")
    fig_h2(res, OUT / "fig_power_h2.png")
    fig_h3a(res, OUT / "fig_power_h3a.png")
    fig_h4(res, OUT / "fig_power_h4.png")
    fig_design_e2(OUT / "fig_design_e2.png")
    write_markdown(res, OUT / "power.md")
    print(f"done in {time.time() - t0:.0f}s")


def pct(x: float, nd: int = 0) -> str:
    return f"{100 * x:.{nd}f} %"


def write_markdown(res: dict, path: Path):
    ns = res["n_values"]
    L = []
    L.append("# Power analysis: results tables\n")
    extra = ""
    if "h2_refutation_levels" in res:
        extra += (f", the H2 refutation-level check with {res['h2_refutation_levels'][0]['n_sims']:,}, "
                  f"the H4a rejected-rule check with {res.get('h4_sims', 500)}")
    if "d11_e2" in res:
        extra += (f", and D11's window clause and E2 clause with {res['d11_e1_window'][0]['n_sims']:,} and "
                  f"{res['d11_e2'][0].get('n_sims', 20000):,}")
    L.append(f"Generated by `power.py`. H1, H3a and D11's E1 clause are exact. Simulated: H2 and H3b "
             f"with {res['sims']:,} campaigns per scenario, H3c with {min(res['sims'], 500)}, H4a with "
             f"{res.get('h4_sims', 500)} sessions per row and H4b/H4c with {min(res.get('h4_sims', 500), 300)}, "
             f"the H3b bootstrap comparison with 200{extra}. Every decision rule is the registered one "
             f"from `prereg_stats.py`, and seeds are fixed.\n")
    L.append("## H1a: certifying ≥ 99 % (exact one-sided 95 % lower bound ≥ 0.99)\n")
    L.append("| True success rate | " + " | ".join(f"n = {n}" for n in ns) + " |")
    L.append("|---|" + "---|" * len(ns))
    for row in res["h1a_table"]:
        L.append(f"| {row['p']:.2%} | " + " | ".join(pct(row[str(n)]) for n in ns) + " |")
    L.append("\nFailures allowed: " + ", ".join(
        f"n = {n}: {res['thresholds'][str(n)]['max_fail_certify']}" for n in ns) + ".\n")
    L.append("| True success rate | n for 80 % power | n for 90 % power |")
    L.append("|---|---|---|")
    for row in res["h1a_n_needed"]:
        L.append(f"| {row['p']:.2%} | {row['n80']} | {row['n90']} |")
    L.append("\n## H1b: showing < 99 % (exact one-sided 95 % upper bound < 0.99)\n")
    L.append("| True success rate | " + " | ".join(f"n = {n}" for n in ns) + " |")
    L.append("|---|" + "---|" * len(ns))
    for row in res["h1b_table"]:
        L.append(f"| {row['p']:.1%} | " + " | ".join(pct(row[str(n)]) for n in ns) + " |")
    L.append("\nFailures needed: " + ", ".join(
        f"n = {n}: {res['thresholds'][str(n)]['min_fail_refute']}" for n in ns) + ".\n")
    L.append("| True success rate | n for 80 % power | n for 90 % power |")
    L.append("|---|---|---|")
    for row in res["h1b_n_needed"]:
        L.append(f"| {row['p']:.1%} | {row['n80']} | {row['n90']} |")
    L.append("\n## H3a: one-sided Boschloo, AT vs OL, single vials\n")
    L.append(f"Exact power from the test's critical region (largest size over the nuisance parameter: "
             f"{res['h3a_size_check']:.4f} ≤ 0.05). One-sided Fisher shown for comparison.\n")
    L.append("| OL → AT | Boschloo, n = 300 each | Fisher, n = 300 each |")
    L.append("|---|---|---|")
    for row in res["h3a_table"]:
        L.append(f"| {row['p_ol']:.1%} → {row['p_at']:.1%} | {pct(row['boschloo_300'])} | {pct(row['fisher_300'])} |")
    L.append("\n| OL → AT | " + " | ".join(f"n = {n}" for n in res["h3a_curves"][0]["n"]) + " |")
    L.append("|---|" + "---|" * len(res["h3a_curves"][0]["n"]))
    for row in res["h3a_curves"]:
        L.append(f"| {row['label']} | " + " | ".join(pct(v) for v in row["power"]) + " |")
    v = res["h3a_validation"]
    L.append(f"\nCheck against `scipy.stats.boschloo_exact` for AT {v['table'][0]}/300 vs OL "
             f"{v['table'][2]}/300: scipy p = {v['scipy_boschloo_p']:.4f}; inside this critical "
             f"region: {v['in_region']}.\n")
    L.append("## H2: capture radius (ED90 on x and y > 1.15 mm)\n")
    L.append("Logistic capture curves with the given ED90 and a given distance from ED90 to ED50 "
             "(smaller = sharper edge). 'Supported' and 'refuted' are the registered decision "
             "(`prereg_stats.h2_decision`): support needs both axes, refutation either axis at "
             "one-sided 99 % each. 'Model-free' is the secondary ±2 mm check (≤ 3 failures in 80); 'v1' is "
             "v1's rule, which required the two together.\n")
    L.append("| ED50 − ED90 | True ED90 | Supported | Refuted | Model-free check | v1 rule |")
    L.append("|---|---|---|---|---|---|")
    for w, rows in res["h2_by_width"].items():
        for r in rows:
            L.append(f"| {w} mm | {r['ed90']} mm | {pct(r['supported'])} | {pct(r['refuted'])} | {pct(r['model_free'])} | {pct(r['v1_combined'])} |")
    L.append("\nStep-shaped capture (99.5 % inside the edge, 5 % outside), which the logistic model does "
             "not describe exactly:\n")
    L.append("| Edge | Supported | Refuted | Model-free check | v1 rule |")
    L.append("|---|---|---|---|---|")
    for r in res["h2_step"]:
        L.append(f"| {r['edge_mm']} mm | {pct(r['supported'])} | {pct(r['refuted'])} | {pct(r['model_free'])} | {pct(r['v1_combined'])} |")
    if "h2_refutation_levels" in res:
        n_lv = res["h2_refutation_levels"][0]["n_sims"]
        L.append(f"\n**Why refutation is at 99 % per axis.** H2 is refuted if either axis is, so the "
                 f"per-axis level sets the false-refutation rate at the boundary (true ED90 exactly "
                 f"1.15 mm, which should be refuted at most 5 % of the time). {n_lv:,} simulated "
                 f"campaigns per row with the seeds above, so the first {res['sims']:,} are the "
                 f"campaigns in the table above; only the level of the two refutation bounds changes. "
                 f"The 99 % column is the registered rule, checked against `prereg_stats.h2_decision` "
                 f"on every campaign. At a 5 % rate the Monte Carlo standard error is "
                 f"{100 * (0.05 * 0.95 / n_lv) ** 0.5:.1f} percentage points.\n")
        L.append("| ED50 − ED90 | True ED90 | 95 % per axis | 97.5 % (Bonferroni) | 99 % (registered) |")
        L.append("|---|---|---|---|---|")
        for r in res["h2_refutation_levels"]:
            L.append(f"| {r['width']} mm | {r['ed90']} mm | {pct(r['0.95'], 1)} | {pct(r['0.975'], 1)} | {pct(r['0.99'], 1)} |")
    L.append("\n## H3b: correction widens single-vial ED90 (x and y)\n")
    L.append("The registered rule (`prereg_stats.h3b_axis_supported`: delta-method bound on the "
             "radius difference, Fieller if the corrected curve is censored), on both axes. The last "
             "two rows have no true difference, so they are false-support rates.\n")
    L.append("| Scenario | Power |")
    L.append("|---|---|")
    for r in res["h3b"]:
        L.append(f"| {r['scenario']} | {pct(r['power'])} |")
    if "h3b_bootstrap_check" in res:
        L.append("\nWhy not a percentile bootstrap: the rule first registered in v2, against the "
                 "registered one (200 simulated campaigns each). The bootstrap detects more in the "
                 "0.6 vs 0.3 mm case, but when the two curves share an ED90 and differ in slope it "
                 "claims a difference far more often than 5 %.\n")
        L.append("\n| Scenario | Registered (delta) | Percentile bootstrap (B = 300) |")
        L.append("|---|---|---|")
        for r in res["h3b_bootstrap_check"]:
            L.append(f"| {r['scenario']} | {pct(r['registered'])} | {pct(r['bootstrap'])} |")
    L.append("\n## H3c: time cost (HL upper bound ≤ cap)\n")
    L.append("n = 300 per condition, right-skewed transfer times with SD 3 s, cap 5 s.\n")
    L.append("| True extra time | Power |")
    L.append("|---|---|")
    for r in res["h3c"]:
        L.append(f"| {r['delta_s']} s | {pct(r['power'])} |")
    L.append("\n## MTBI: precision from 600 E1 transfers per cell\n")
    L.append("| Interventions per transfer | Expected interventions | True MTBI | 95 % interval if the expected count is seen | True S(50) |")
    L.append("|---|---|---|---|---|")
    for r in res["mtbi"]:
        lo, hi = r["mtbi_ci_at_expected"]
        hi_s = "∞" if not math.isfinite(hi) else f"{hi:.0f}"
        L.append(f"| {r['q']} | {r['expected_interventions']:.1f} | {r['mtbi_true']:.0f} | {lo:.0f}–{hi_s} | {pct(r['s50_true'])} |")
    b = res["e2_burden"]
    L.append("\n## E2: expected failed loads (each needs a person to reset the cell)\n")
    L.append("One plausible scenario, not data; see `e2_expected_failures()` for the assumptions.\n")
    L.append("| Cell | Expected failed loads of 420 |")
    L.append("|---|---|")
    for k in ("carrier_OL", "carrier_AT", "vial_OL", "vial_AT", "total"):
        L.append(f"| {k.replace('_', ' ')} | {b[k]:.0f} |")
    L.append(f"\nIf single-vial OL ran only 0, ±1, ±2 mm and ±2°: {b['vial_OL_if_trimmed_to_2mm_and_2deg']:.0f} "
             f"failed loads instead of {b['vial_OL']:.0f}.\n")
    if "d11_e1" in res:
        L.append("\n## D11: how often the run-of-failures stop fires\n")
        L.append("The stop exists for upkeep: it should rarely fire on a healthy cell and soon on one "
                 "that has gone wrong. **E1 clause** (3 failed loads in a row in one cell), exact, for "
                 "one cell's 300 loads failing independently at a given rate. Runs are counted across "
                 "block boundaries, so these are upper bounds if the count restarts with each block.\n")
        L.append("| Failure rate per load | Expected stops in 300 loads | Chance of at least one stop | Mean loads to the first stop |")
        L.append("|---|---|---|---|")
        for r in res["d11_e1"]:
            wait = r["mean_loads_to_first_stop"]
            wait_s = "> 100,000" if wait > 1e5 else f"{wait:,.0f}"
            L.append(f"| {pct(r['q'], 1)} | {r['expected_stops']:.3f} | {pct(r['p_any_stop'], 1)} | {wait_s} |")
        if "d11_e1_window" in res:
            L.append(f"\nAn optional extra E1 clause, not registered: 5 failed loads among the cell's last 20 "
                     f"(v1 had it, and v2 until the review), simulated ({res['d11_e1_window'][0]['n_sims']:,} "
                     f"cells per row). It warns much sooner when a cell degrades, and stops a healthy 93 % "
                     f"cell more often.\n")
            L.append("| Failure rate per load | Expected stops in 300 loads | Chance of at least one stop | Median loads to the first stop (when ≥ 10 % of cells stop) |")
            L.append("|---|---|---|---|")
            for r in res["d11_e1_window"]:
                med = ("—" if r["median_loads_to_first_stop"] is None or r["p_any_stop"] < 0.1
                       else f"{r['median_loads_to_first_stop']:.0f}")
                L.append(f"| {pct(r['q'], 1)} | {r['expected_stops']:.3f} | {pct(r['p_any_stop'], 1)} | {med} |")
        e2rows = res["d11_e2"]
        L.append(f"\n**E2 clause** (2 failed zero-offset loads in one block), simulated on the registered "
                 f"schedule for one task: 20 passes over the 21 levels in random order, each level a pair "
                 f"of loads (OL and AT), {e2rows[0]['pairs_per_block']} pairs per block, so a block holds "
                 f"one zero-offset pair or none most of the time. The first two rows are the planning "
                 f"scenario; the rest are a cell gone wrong.\n")
        L.append("| Zero-offset failure rate, OL / AT | Expected stops over the task's 420 pairs | Chance of at least one stop | Median pairs to the first stop (when ≥ 10 % of tasks stop) |")
        L.append("|---|---|---|---|")
        for r in e2rows:
            med = ("—" if r["median_pairs_to_first_stop"] is None or r["p_any_stop"] < 0.1
                   else f"{r['median_pairs_to_first_stop']:.0f}")
            L.append(f"| {pct(r['q_ol'], 1)} / {pct(r['q_at'], 1)} | {r['expected_stops']:.3f} | {pct(r['p_any_stop'], 1)} | {med} |")
    L.append(f"\n## H4: ISO 9283 RP, 30 cycles per pose ({res.get('h4_sims', 1000)} simulated sessions per row)\n")
    L.append("Instrument expanded uncertainty U = 0.025 mm (k = 2), treated as u = 0.0125 mm per axis "
             "and added in quadrature, so the measured RP is biased upward. Outcomes from "
             "`prereg_stats.h4a_decision`: refuted needs a bootstrap-t one-sided 99 % lower bound "
             "(Bonferroni over 5 poses) above the RP an arm exactly at 0.10 mm would show through "
             f"this instrument ({ps.rp_refutation_threshold(0.10, 0.0125):.3f} mm).\n")
    L.append("| True arm RP | Supported (meets: point ≤ 0.10 at all 5) | Certified (upper bound ≤ 0.10 at all 5) | Refuted |")
    L.append("|---|---|---|---|")
    for r in res["h4a"]:
        L.append(f"| {r['rp_true']:.2f} mm | {pct(r['meets'])} | {pct(r['certified'])} | {pct(r.get('refuted', float('nan')))} |")
    if "h4a_rejected" in res:
        thr = ps.rp_refutation_threshold(0.10, 0.0125)
        L.append("\n**Why H4a's refutation rule has both fixes.** How often H4a is refuted under the "
                 "rule registered before the independent review and under each fix alone, on the same "
                 "simulated sessions. An arm exactly at 0.10 mm should be refuted at most 5 % of the "
                 "time. The last column is the registered rule and equals 'Refuted' above.\n")
        L.append(f"| True arm RP | Pre-review: 95 % per pose, against 0.10 mm | Bonferroni only: 99 %, against 0.10 mm | "
                 f"Instrument only: 95 %, against {thr:.3f} mm | Registered: 99 %, against {thr:.3f} mm |")
        L.append("|---|---|---|---|---|")
        for r in res["h4a_rejected"]:
            L.append(f"| {r['rp_true']:.2f} mm | {pct(r['pre_review_95_vs_spec'], 1)} | {pct(r['bonferroni_99_vs_spec'], 1)} | "
                     f"{pct(r['adjusted_95_vs_threshold'], 1)} | {pct(r['registered_99_vs_threshold'], 1)} |")
    L.append("\n| RP unloaded | Payload adds | Slope per 100 mm | H4b power | H4c power |")
    L.append("|---|---|---|---|---|")
    for r in res["h4bc"]:
        L.append(f"| {r['rp_unloaded']} mm | {r['payload_increase']} mm | {r['slope_per_100mm']} mm | {pct(r['h4b'])} | {pct(r['h4c'])} |")
    L.append(f"\nReach of the five poses assumed: {res['h4bc'][0]['reach_mm']} mm.\n")
    path.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
