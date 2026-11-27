"""Run the registered analysis on a synthetic campaign whose true values are known.

PROTOCOL.md section 14 says the analysis code must be shown to recover known values before the
first counted trial. This script:

1. builds a synthetic E1 + E2 + E3 campaign with the schedule rules of PROTOCOL.md section 9
   (seeded sub-blocks, blocks, interventions after failures), and writes it in the registered
   per-transfer format (`out/synthetic_transfers.csv`, `out/synthetic_rp.csv`);
2. runs every confirmatory rule in `prereg_stats.py` on it and reports the H1-H4 decisions next
   to the decisions the true values imply;
3. repeats the key interval procedures on many synthetic data sets and reports their coverage.

Run:  python simulate_and_check.py            (about 4 minutes on one core)
Writes out/recovery.md. Seeds are fixed. Nothing here talks to the arm.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import numpy as np
from scipy.special import expit, logit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import prereg_stats as ps  # noqa: E402

OUT = HERE / "out"

# ---------------------------------------------------------------------------------------
# Truth for the synthetic campaign
# ---------------------------------------------------------------------------------------

P_LOAD = {("C", "OL"): 0.998, ("C", "AT"): 0.999, ("V", "OL"): 0.93, ("V", "AT"): 0.985}
P_UNLOAD = {("C", "OL"): 0.999, ("C", "AT"): 0.999, ("V", "OL"): 0.99, ("V", "AT"): 0.995}
TIME_BASE = 32.0  # s per transfer, plus gamma noise
TIME_AT_EXTRA = 3.0  # s, the true cost of correction
N_E1 = 300
UNITS_PER_BLOCK_E1 = 40  # 10 sub-blocks of 4


def curve(ed90: float, width: float):
    b1 = (logit(0.5) - logit(0.9)) / width
    b0 = logit(0.9) - b1 * ed90
    return (b0, b1), (lambda d: expit(b0 + b1 * np.asarray(d, dtype=float)))


TRUE_CURVES = {
    ("C", "OL"): curve(2.8, 0.4),
    ("C", "AT"): ((None, None), lambda d: np.full_like(np.asarray(d, dtype=float), 0.995)),
    ("V", "OL"): curve(0.2, 0.3),
    ("V", "AT"): curve(3.0, 0.5),
}
YAW_P = {("C", "OL"): {2.0: 0.03, 4.0: 0.0}, ("C", "AT"): {2.0: 0.995, 4.0: 0.99},
         ("V", "OL"): {2.0: 0.0, 4.0: 0.0}, ("V", "AT"): {2.0: 0.99, 4.0: 0.98}}
LEVELS = [("0", 0.0)] + [(ax, s * m) for ax in ("x", "y") for m in (1, 2, 3, 4) for s in (1, -1)] \
    + [("yaw", s * m) for m in (2, 4) for s in (1, -1)]
RP_TRUE = {0: [0.050, 0.055, 0.060, 0.055, 0.065], 1: [0.060, 0.066, 0.072, 0.066, 0.078]}
REACH = [350.0, 270.0, 430.0, 270.0, 430.0]
U_INST = 0.025


def true_p_e2(task: str, cond: str, axis: str, value: float) -> float:
    if axis == "yaw":
        return YAW_P[(task, cond)][abs(value)]
    return float(TRUE_CURVES[(task, cond)][1](abs(value)))


# ---------------------------------------------------------------------------------------
# Synthetic campaign
# ---------------------------------------------------------------------------------------

def build_e1(rng: np.random.Generator) -> list[dict]:
    rows = []
    cells = [("C", "OL"), ("C", "AT"), ("V", "OL"), ("V", "AT")]
    schedule = []
    for _ in range(N_E1):
        schedule.extend([cells[i] for i in rng.permutation(4)])
    n_blocks = math.ceil(len(schedule) / UNITS_PER_BLOCK_E1)
    unit = 0
    for b in range(n_blocks):
        block_units = schedule[b * UNITS_PER_BLOCK_E1:(b + 1) * UNITS_PER_BLOCK_E1]
        for task, cond in block_units:
            unit += 1
            legs = ("unload", "load") if task == "C" else ("load", "unload")
            for leg in legs:
                p = P_LOAD[(task, cond)] if leg == "load" else P_UNLOAD[(task, cond)]
                ok = int(rng.random() < p)
                t = TIME_BASE + rng.gamma(4.0, 0.75) + (TIME_AT_EXTRA if cond == "AT" else 0.0)
                rows.append(dict(experiment="E1", block_id=f"E1-{b + 1:03d}", cfg_id="cfg-1",
                                 unit_id=unit, task=task, condition=cond, leg=leg,
                                 offset_axis="0", offset_value=0.0, transfer_time_s=round(t, 2),
                                 success=ok, intervention=1 - ok, excluded=0))
    return rows


def build_e2(rng: np.random.Generator) -> list[dict]:
    rows = []
    unit = 100000
    for task in ("C", "V"):
        for rep in range(20):  # one replicate = every level once, OL and AT paired
            order = rng.permutation(len(LEVELS))
            for li in order:
                axis, value = LEVELS[li]
                for cond in (("OL", "AT") if rng.random() < 0.5 else ("AT", "OL")):
                    unit += 1
                    ok = int(rng.random() < true_p_e2(task, cond, axis, value))
                    rows.append(dict(experiment="E2", block_id=f"E2-{task}-{rep + 1:03d}", cfg_id="cfg-1",
                                     unit_id=unit, task=task, condition=cond, leg="load",
                                     offset_axis=axis, offset_value=value, transfer_time_s="",
                                     success=ok, intervention=1 - ok, excluded=0))
    return rows


def build_e3(rng: np.random.Generator) -> list[dict]:
    rows = []
    for load in (0, 1):
        for k in range(5):
            sigma = math.hypot(RP_TRUE[load][k] / (2 * math.sqrt(2 / math.pi) + 3 * math.sqrt(3 - 8 / math.pi)),
                               U_INST / 2)
            pts = rng.normal(0.0, sigma, (30, 3))
            for c in range(30):
                rows.append(dict(payload=load, pose=f"P{k + 1}", reach_mm=REACH[k], cycle=c + 1,
                                 x_mm=pts[c, 0], y_mm=pts[c, 1], z_mm=pts[c, 2]))
    return rows


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------------------------------
# Registered analysis on the synthetic campaign
# ---------------------------------------------------------------------------------------

def mtbi_intervals(rows: list[dict], task: str, cond: str) -> tuple[np.ndarray, np.ndarray]:
    """Transfers between interventions for one cell, per PROTOCOL.md 14.4 (E1 only).

    The cell's clock counts only its own transfers. It runs on across sessions within a
    configuration (a session end is a pause, not an intervention), restarts after each of the
    cell's interventions, and is censored when the configuration (here, the data) ends.
    """
    durations, events = [], []
    by_cfg: dict[str, list[dict]] = {}
    for r in rows:
        by_cfg.setdefault(r["cfg_id"], []).append(r)
    for _cfg, rs in by_cfg.items():
        count = 0
        for r in rs:
            if (r["task"], r["condition"]) != (task, cond):
                continue
            count += 1
            if r["intervention"]:
                durations.append(count)
                events.append(1)
                count = 0
        if count > 0:
            durations.append(count)
            events.append(0)
    return np.array(durations, dtype=float), np.array(events, dtype=int)


def analyse(e1: list[dict], e2: list[dict], e3: list[dict], rng: np.random.Generator) -> list[str]:
    L = []
    L.append("## 1. The registered analysis on one synthetic campaign\n")
    L.append("Intervals are 95 % except the ED90 rows, which show the 90 % Fieller interval whose "
             "ends are the registered one-sided 95 % bounds; about one in ten of those should miss.\n")
    L.append("| Quantity | True | Estimate | Interval | Inside? |")
    L.append("|---|---|---|---|---|")
    loads = {c: [r for r in e1 if (r["task"], r["condition"]) == c and r["leg"] == "load"] for c in P_LOAD}
    est = {}
    for c, rs in loads.items():
        k = sum(r["success"] for r in rs)
        n = len(rs)
        lo, hi = ps.wilson(k, n)
        est[c] = (k, n)
        inside = lo <= P_LOAD[c] <= hi
        L.append(f"| p({c[0]}, {c[1]}) loads | {P_LOAD[c]:.3f} | {k}/{n} = {k / n:.3f} | Wilson {lo:.3f}–{hi:.3f} | {'yes' if inside else 'no'} |")
    # H1
    k_c, n_c = est[("C", "OL")]
    h1a = ps.h1a_decision(k_c, n_c)
    k2, n2 = est[("V", "OL")]
    h1b = ps.h1b_decision(k2, n2)
    # H3a
    ka, na = est[("V", "AT")]
    p3a = ps.boschloo_greater(ka, na, k2, n2)
    h3a = ps.h3a_decision(ka, na, k2, n2)
    d, dlo, dhi = ps.newcombe_diff(ka, na, k2, n2)
    true_d = P_LOAD[("V", "AT")] - P_LOAD[("V", "OL")]
    L.append(f"| p(V, AT) − p(V, OL) | {true_d:.3f} | {d:.3f} | Newcombe {dlo:.3f}–{dhi:.3f} | {'yes' if dlo <= true_d <= dhi else 'no'} |")
    g, glo, ghi = ps.gap_closed_interval(k2, n2, ka, na)
    g_true = ps.gap_closed(P_LOAD[("V", "OL")], P_LOAD[("V", "AT")])
    L.append(f"| Gap closed G(V) | {g_true:.2f} | {g:.2f} | bootstrap {glo:.2f}–{ghi:.2f} | {'yes' if glo <= g_true <= ghi else 'no'} |")
    # H3c
    t_at = np.array([r["transfer_time_s"] for r in loads[("V", "AT")] if r["success"]], dtype=float)
    t_ol = np.array([r["transfer_time_s"] for r in loads[("V", "OL")] if r["success"]], dtype=float)
    hl, hl_up = ps.hodges_lehmann_upper(t_at, t_ol)
    h3c = ps.h3c_decision(t_at, t_ol, 5.0)
    L.append(f"| HL time shift, V (s) | {TIME_AT_EXTRA:.1f} | {hl:.2f} | upper 95 % {hl_up:.2f} | {'yes' if TIME_AT_EXTRA <= hl_up else 'no'} |")
    # E2 curves
    decisions = {}
    for (task, cond) in TRUE_CURVES:
        for axis in ("x", "y"):
            rs = [r for r in e2 if (r["task"], r["condition"]) == (task, cond) and r["offset_axis"] in ("0", axis)]
            dd = np.array([abs(r["offset_value"]) for r in rs])
            ss = np.array([r["success"] for r in rs])
            res = ps.capture_curve(dd, ss)
            decisions[(task, cond, axis)] = res
            (b0, b1), _f = TRUE_CURVES[(task, cond)]
            if b0 is None:
                true_ed90 = "> 4 (flat)"
            else:
                true_ed90 = f"{(logit(0.9) - b0) / b1:.2f}"
            lo90, hi90 = res.ed90_fieller90
            if res.censored:
                shown = "censored: > 4 mm"
                interval = f"pooled ≥ 2 mm lower bound {res.pooled_lower_ge2:.3f}"
                inside = "yes" if b0 is None else "—"
            else:
                shown = f"{res.ed90:.2f}"
                interval = f"Fieller 90 % {lo90:.2f}–{hi90:.2f}"
                inside = "yes" if (b0 is not None and lo90 <= (logit(0.9) - b0) / b1 <= hi90) else "no"
            L.append(f"| ED90 {task}-{cond} {axis} (mm) | {true_ed90} | {shown} | {interval} | {inside} |")
    zero_c = [r for r in e2 if (r["task"], r["condition"]) == ("C", "OL") and r["offset_axis"] == "0"]
    h2 = ps.h2_decision(decisions[("C", "OL", "x")], decisions[("C", "OL", "y")],
                        sum(r["success"] for r in zero_c), len(zero_c))
    h3b_axes = [ps.h3b_axis_supported(decisions[("V", "AT", ax)], decisions[("V", "OL", ax)])
                for ax in ("x", "y")]
    h3b = ps.h3b_decision(decisions[("V", "AT", "x")], decisions[("V", "OL", "x")],
                          decisions[("V", "AT", "y")], decisions[("V", "OL", "y")])
    # MTBI
    dur, ev = mtbi_intervals(e1, "V", "OL")
    km = ps.kaplan_meier(dur, ev)
    m, mlo, mhi = ps.rmst(km, 300)
    tau_used = ps.rmst_tau(km, 300)
    transfers = sum(1 for r in e1 if (r["task"], r["condition"]) == ("V", "OL"))
    q_true = 1 - (P_LOAD[("V", "OL")] + P_UNLOAD[("V", "OL")]) / 2
    rmst_true = (1 - (1 - q_true) ** tau_used) / q_true  # geometric renewal, restricted at tau
    L.append(f"| MTBI V-OL, RMST to {tau_used:.0f} transfers | {rmst_true:.1f} | {m:.1f} | Greenwood {mlo:.1f}–{mhi:.1f} | {'yes' if mlo <= rmst_true <= mhi else 'no'} |")
    crude, clo, chi = ps.mtbi_crude(transfers, int(ev.sum()))
    L.append(f"| MTBI V-OL, crude | {1 / q_true:.1f} | {crude:.1f} | Garwood {clo:.1f}–{chi:.1f} | {'yes' if clo <= 1 / q_true <= chi else 'no'} |")
    s50 = ps.km_survival_at(km, 50)
    L.append(f"| S(50), V-OL | {(1 - q_true) ** 50:.3f} | {s50:.3f} | — | — |")
    # E3
    pose_pts = {}
    for load in (0, 1):
        for k in range(5):
            pts = np.array([[r["x_mm"], r["y_mm"], r["z_mm"]] for r in e3 if r["payload"] == load and r["pose"] == f"P{k + 1}"])
            pose_pts[(k, load)] = pts
            rp, lo, hi = ps.bootstrap_t_rp(pts, 4000, seed=100 * load + k, conf=0.975)
            rp_obs_true = math.hypot(RP_TRUE[load][k], U_INST / 2 * ps.RP_PER_SIGMA)
            L.append(f"| RP P{k + 1}, {'loaded' if load else 'unloaded'} (mm) | {RP_TRUE[load][k]:.3f} (arm) / {rp_obs_true:.3f} (with instrument) | {rp:.3f} | bootstrap-t 95 % {lo:.3f}–{hi:.3f} | {'yes' if lo <= rp_obs_true <= hi else 'no'} |")
    h4a, h4a_cert = ps.h4a_decision([pose_pts[(k, 0)] for k in range(5)], U_INST / 2, U_INST)
    h4bc = ps.h4bc_decisions(pose_pts, REACH)

    L.append("\n## 2. Decisions on the synthetic campaign\n")
    L.append("What the registered rules decide, next to what the true values imply. A test can "
             "miss a true effect (low power) without being wrong; section 3 checks the "
             "procedures themselves.\n")
    L.append("| Hypothesis | Truth | Decision | Detail |")
    L.append("|---|---|---|---|")
    L.append(f"| H1a | true rate 99.8 %, so ≥ 99 % is true | {h1a} | {k_c}/{n_c} carrier OL loads; exact lower bound {ps.cp_lower(k_c, n_c):.4f} (power is 55 % at this rate) |")
    L.append(f"| H1b | true rate 93 %, so < 99 % is true | {h1b} | {k2}/{n2}; exact upper bound {ps.cp_upper(k2, n2):.4f} |")
    L.append(f"| H2 | true ED90 2.8 mm > 1.15 mm | {h2} | Fieller lower bounds x {decisions[('C', 'OL', 'x')].ed90_lower95:.2f}, y {decisions[('C', 'OL', 'y')].ed90_lower95:.2f} mm |")
    L.append(f"| H3a | 93 % → 98.5 %, a real gain | {h3a} | Boschloo one-sided p = {p3a:.2g} |")
    L.append(f"| H3b | ED90 0.2 → 3.0 mm, a real gain | {h3b} | x {'passes' if h3b_axes[0] else 'fails'}, y {'passes' if h3b_axes[1] else 'fails'} |")
    L.append(f"| H3c (cap 5 s) | 3.0 s ≤ 5 s | {h3c} | HL upper bound {hl_up:.2f} s |")
    rp0, rp1 = np.array(RP_TRUE[0]), np.array(RP_TRUE[1])
    gain = rp1 - rp0
    reach100 = np.array(REACH) / 100.0
    slopes = [float(np.polyfit(reach100, np.array(RP_TRUE[load]), 1)[0]) for load in (0, 1)]
    L.append(f"| H4a | unloaded RP {rp0.min():.3f}–{rp0.max():.3f} mm ≤ 0.10 | {h4a}{', certified' if h4a_cert else ''} | all five poses; instrument U = {U_INST} mm |")
    L.append(f"| H4b | payload adds {gain.min():.3f}–{gain.max():.3f} mm | {h4bc['h4b']} | bootstrap lower bound of the mean difference {h4bc['h4b_lower']:.4f} mm |")
    L.append(f"| H4c | RP grows {min(slopes):.4f}–{max(slopes):.4f} mm per 100 mm (arm alone; less through the instrument) | {h4bc['h4c']} | slope lower bound {h4bc['h4c_lower']:.4f} mm per 100 mm |")
    return L


# ---------------------------------------------------------------------------------------
# Coverage of the interval procedures over repeated synthetic data
# ---------------------------------------------------------------------------------------

def coverage(rng: np.random.Generator, reps: int) -> list[str]:
    L = ["\n## 3. Coverage over repeated synthetic data\n",
         f"Each row repeats one procedure on {reps} fresh synthetic data sets and counts how often "
         "its interval contains the true value. A 95 % interval should cover about 95 % of the "
         "time; a one-sided 95 % bound, about 95 % or more.\n",
         "| Procedure | Setting | Nominal | Coverage |", "|---|---|---|---|"]
    from scipy import stats
    # Wilson, exact one-sided lower bound: exact coverage by enumeration
    for p in (0.93, 0.985, 0.998):
        ks = np.arange(301)
        pmf = stats.binom.pmf(ks, 300, p)
        cov_w = sum(pmf[k] for k in ks if ps.wilson(int(k), 300)[0] <= p <= ps.wilson(int(k), 300)[1])
        cov_l = sum(pmf[k] for k in ks if ps.cp_lower(int(k), 300) <= p)
        L.append(f"| Wilson 95 % | p = {p}, n = 300 (exact) | 95 % | {cov_w:.1%} |")
        L.append(f"| Exact one-sided lower bound | p = {p}, n = 300 (exact) | ≥ 95 % | {cov_l:.1%} |")
    # Fieller for ED90 (C-OL-like curve)
    (b0, b1), f = curve(2.8, 0.4)
    true = (logit(0.9) - b0) / b1
    d = np.concatenate([np.zeros(20), np.repeat([1.0, 2.0, 3.0, 4.0], 40)])
    hit = lower_ok = n_ok = 0
    for _ in range(reps):
        s = (rng.random(d.size) < f(d)).astype(int)
        r = ps.capture_curve(d, s)
        if r.censored:
            continue
        n_ok += 1
        lo, hi = ps.fieller_interval(r.fit.beta, r.fit.cov, 0.9, ps.Z95_TWO_SIDED)
        hit += lo <= true <= hi
        lower_ok += r.ed90_lower95 <= true
    L.append(f"| Fieller 95 % for ED90 | ED90 2.8 mm, ED50 3.2 mm, 180 trials | 95 % | {hit / n_ok:.1%} |")
    L.append(f"| Fieller one-sided 95 % lower bound | same | ≥ 95 % | {lower_ok / n_ok:.1%} |")
    (b0, b1), f = curve(1.8, 1.0)
    true = (logit(0.9) - b0) / b1
    hit = n_ok = 0
    for _ in range(reps):
        s = (rng.random(d.size) < f(d)).astype(int)
        r = ps.capture_curve(d, s)
        if r.censored:
            continue
        n_ok += 1
        lo, hi = ps.fieller_interval(r.fit.beta, r.fit.cov, 0.9, ps.Z95_TWO_SIDED)
        hit += lo <= true <= hi
    L.append(f"| Fieller 95 % for ED90 | ED90 1.8 mm, ED50 2.8 mm (gentle) | 95 % | {hit / n_ok:.1%} |")
    # RMST with Greenwood: renewal process with geometric gaps over one configuration
    for q, tau in ((0.04, 300), (0.01, 300), (0.04, 50)):
        hit = 0
        for _ in range(reps):
            durs, evs = [], []
            left = 600  # 300 units x 2 transfers of one cell
            while left > 0:
                g = int(rng.geometric(q))
                if g <= left:
                    durs.append(g)
                    evs.append(1)
                    left -= g
                else:
                    durs.append(left)
                    evs.append(0)
                    left = 0
            km = ps.kaplan_meier(np.array(durs, float), np.array(evs))
            if km.times.size == 0:
                hit += 1  # no interventions: RMST = tau, and the truth is within [lower, tau]
                continue
            tau_used = ps.rmst_tau(km, tau)  # capped at the longest observed interval
            true_rmst = (1 - (1 - q) ** tau_used) / q
            _m, lo, hi = ps.rmst(km, tau)
            hit += lo <= true_rmst <= hi
        L.append(f"| RMST 95 % (Greenwood) | {q:.0%} interventions per transfer, 600 transfers, τ = {tau} (capped at the longest interval) | 95 % | {hit / reps:.1%} |")
    # RP: percentile bootstrap (v1's rule) against bootstrap-t (v2's registered rule)
    rp_true = 0.06
    sigma = rp_true / (2 * math.sqrt(2 / math.pi) + 3 * math.sqrt(3 - 8 / math.pi))
    up_pct = up_t = lo_t = 0
    n_rp = min(reps, 400)
    for i in range(n_rp):
        pts = rng.normal(0, sigma, (30, 3))
        b = ps.bootstrap_rp(pts, 2000, seed=i)
        up_pct += np.quantile(b, 0.95) >= rp_true
        _r, lo, hi = ps.bootstrap_t_rp(pts, 1000, seed=i)
        up_t += hi >= rp_true
        lo_t += lo <= rp_true
    L.append(f"| RP percentile bootstrap, one-sided 95 % upper bound (v1) | true RP 0.06 mm, 30 cycles, isotropic ({n_rp} data sets) | ≥ 95 % | {up_pct / n_rp:.1%} |")
    L.append(f"| RP bootstrap-t, one-sided 95 % upper bound (v2, registered) | same | ≥ 95 % | {up_t / n_rp:.1%} |")
    L.append(f"| RP bootstrap-t, one-sided 95 % lower bound (v2, registered) | same | ≥ 95 % | {lo_t / n_rp:.1%} |")
    L += rp_shape_coverage(np.random.default_rng(20261128), n_rp)
    L += h4b_null_rate(np.random.default_rng(20261129), reps)
    return L


def _true_rp(draw, n: int = 2_000_000) -> float:
    """Population RP (mean + 3 SD of the distance from the true centre) by Monte Carlo."""
    lj = np.linalg.norm(draw(np.random.default_rng(1), n), axis=1)
    return float(lj.mean() + 3 * lj.std())


def rp_shape_coverage(rng: np.random.Generator, reps: int) -> list[str]:
    """Upper-bound coverage of the registered bootstrap-t and of the rejected percentile bootstrap
    when the 30 attained positions are not isotropic Gaussian. Each shape is scaled so that its
    population RP is 0.06 mm."""
    shapes = {
        "isotropic Gaussian": lambda g, n: g.normal(0, 1, (n, 3)),
        "anisotropic Gaussian, variances 3:1:1": lambda g, n: g.normal(0, 1, (n, 3)) * np.sqrt([3, 1, 1]),
        "anisotropic Gaussian, variances 5:2:1": lambda g, n: g.normal(0, 1, (n, 3)) * np.sqrt([5, 2, 1]),
        "heavy-tailed, Student t with 5 df": lambda g, n: g.standard_t(5, (n, 3)),
    }
    L = [f"\nRP upper bounds when the scatter is not isotropic Gaussian ({reps} data sets of 30 cycles "
         f"per shape, true RP 0.06 mm):\n",
         "| Shape | Bootstrap-t upper bound (registered) | Percentile upper bound (v1, rejected) |",
         "|---|---|---|"]
    for name, draw in shapes.items():
        scale = 0.06 / _true_rp(draw)
        up_t = up_pct = 0
        for i in range(reps):
            pts = draw(rng, 30) * scale
            up_pct += np.quantile(ps.bootstrap_rp(pts, 2000, seed=i), 0.95) >= 0.06
            up_t += ps.bootstrap_t_rp(pts, 1000, seed=i)[2] >= 0.06
        L.append(f"| {name} | {up_t / reps:.1%} | {up_pct / reps:.1%} |")
    return L


def h4b_null_rate(rng: np.random.Generator, reps: int) -> list[str]:
    """How often H4b and H4c are supported when payload and reach change nothing (RP 0.06 mm at
    every pose and payload, instrument U = 0.025 mm): their false-positive rates."""
    sigma = math.hypot(0.06 / ps.RP_PER_SIGMA, U_INST / 2)
    fp_b = fp_c = 0
    for i in range(reps):
        cells = {(k, load): rng.normal(0, sigma, (30, 3)) for k in range(5) for load in (0, 1)}
        out = ps.h4bc_decisions(cells, REACH, n_boot=2000, seed=i)
        fp_b += out["h4b"] == "supported"
        fp_c += out["h4c"] == "supported"
    return [f"\nWith no payload or reach effect ({reps} data sets, 2,000 resamples each), H4b was "
            f"supported {fp_b / reps:.1%} of the time and H4c {fp_c / reps:.1%}; both should be "
            f"about 5 % or less.\n"]


def main():
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(20261127)
    e1 = build_e1(rng)
    e2 = build_e2(rng)
    e3 = build_e3(rng)
    write_csv(OUT / "synthetic_transfers.csv", e1 + e2)
    write_csv(OUT / "synthetic_rp.csv", e3)
    L = ["# Synthetic-data check of the registered analysis\n",
         "Generated by `simulate_and_check.py` (seed 20261127). The campaign below is invented, "
         "with known true values, and written in the registered per-transfer format "
         "(`synthetic_transfers.csv`, `synthetic_rp.csv`). Every number comes from the same "
         "functions in `prereg_stats.py` that will analyse the real campaign.\n"]
    L += analyse(e1, e2, e3, rng)
    L += coverage(np.random.default_rng(7), reps=1000)
    L.append("\n## Notes\n")
    L.append("- **RP and the instrument.** Measured RP includes the instrument's noise, so the "
             "intervals cover the RP of arm plus instrument, not the arm alone. With *U* = 0.025 mm "
             "that adds 0.012–0.017 mm at these sizes. This is why H4a needs *U* ≤ 0.025 mm.")
    L.append("- **Why the MTBI clock runs across sessions.** v1 censored every interval at the end "
             "of its block. With about 10 units of a cell per block, no interval could be longer "
             "than about 20 transfers, so neither S(50) nor a restricted mean to τ = 300 could be "
             "estimated. v2 lets a cell's clock run on across sessions within a configuration "
             "(PROTOCOL.md §14.4), which this script follows.")
    L.append("- **E1 and E2 are set apart on purpose.** The synthetic E1 rates are chosen to exercise "
             "H1b and H3a (single vials 93 % open loop, 98.5 % corrected), while the E2 curves are the "
             "planning scenario that `power.py` uses for the reset estimate (97.5 % and about 100 % at "
             "zero offset). So this campaign's single-vial E1 and E2 zero-offset rates disagree, which "
             "a real campaign's E1-against-E2 check (PROTOCOL.md §14.6) would flag. It is a test of "
             "the code, not a prediction.")
    (OUT / "recovery.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
