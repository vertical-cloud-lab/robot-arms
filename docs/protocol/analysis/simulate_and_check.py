"""Run the registered analysis on a synthetic campaign whose true values are known.

PROTOCOL.md section 14 says the analysis code must be shown to recover known values before the
first counted trial. This script:

1. builds a synthetic E1 + E2 + E3 campaign with the schedule rules of PROTOCOL.md section 9
   (seeded sub-blocks, blocks, interventions after failures), and writes it in the registered
   per-transfer format (`out/synthetic_transfers.csv`, `out/synthetic_rp.csv`);
2. runs every confirmatory rule in `prereg_stats.py` on it and reports the H1-H4 decisions next
   to the decisions the true values imply;
3. repeats the key interval procedures on many synthetic data sets and reports their coverage.

Run:  python simulate_and_check.py            (about 3 minutes)
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
    h1a = "supported" if ps.cp_lower(k_c, n_c) >= 0.99 else ("refuted" if ps.cp_upper(k_c, n_c) < 0.99 else "inconclusive")
    k2, n2 = est[("V", "OL")]
    h1b = "supported" if ps.cp_upper(k2, n2) < 0.99 else ("refuted" if ps.cp_lower(k2, n2) >= 0.99 else "inconclusive")
    # H3a
    ka, na = est[("V", "AT")]
    p3a = ps.boschloo_greater(ka, na, k2, n2)
    d, dlo, dhi = ps.newcombe_diff(ka, na, k2, n2)
    true_d = P_LOAD[("V", "AT")] - P_LOAD[("V", "OL")]
    L.append(f"| p(V, AT) − p(V, OL) | {true_d:.3f} | {d:.3f} | Newcombe {dlo:.3f}–{dhi:.3f} | {'yes' if dlo <= true_d <= dhi else 'no'} |")
    g = ps.gap_closed(k2 / n2, ka / na)
    g_true = ps.gap_closed(P_LOAD[("V", "OL")], P_LOAD[("V", "AT")])
    boot = []
    for _ in range(2000):
        po = rng.binomial(n2, k2 / n2) / n2
        pa = rng.binomial(na, ka / na) / na
        if po < 0.99:
            boot.append(ps.gap_closed(po, pa))
    glo, ghi = np.quantile(boot, [0.025, 0.975])
    L.append(f"| Gap closed G(V) | {g_true:.2f} | {g:.2f} | bootstrap {glo:.2f}–{ghi:.2f} | {'yes' if glo <= g_true <= ghi else 'no'} |")
    # H3c
    t_at = np.array([r["transfer_time_s"] for r in loads[("V", "AT")] if r["success"]], dtype=float)
    t_ol = np.array([r["transfer_time_s"] for r in loads[("V", "OL")] if r["success"]], dtype=float)
    hl, hl_up = ps.hodges_lehmann_upper(t_at, t_ol)
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
    h2 = all(ps.h2_axis_supported(decisions[("C", "OL", ax)]) for ax in ("x", "y"))
    h3b_axes = []
    for ax in ("x", "y"):
        r_at, r_ol = decisions[("V", "AT", ax)], decisions[("V", "OL", ax)]
        if r_at.censored:
            h3b_axes.append(r_ol.ed90_fieller90[1] < r_at.max_offset)
        else:
            rs_at = [r for r in e2 if (r["task"], r["condition"]) == ("V", "AT") and r["offset_axis"] in ("0", ax)]
            rs_ol = [r for r in e2 if (r["task"], r["condition"]) == ("V", "OL") and r["offset_axis"] in ("0", ax)]
            ba = ps.bootstrap_ed90(np.array([abs(r["offset_value"]) for r in rs_at]),
                                   np.array([r["success"] for r in rs_at]), 2000, seed=11)
            bo = ps.bootstrap_ed90(np.array([abs(r["offset_value"]) for r in rs_ol]),
                                   np.array([r["success"] for r in rs_ol]), 2000, seed=12)
            diff = np.maximum(ba, 0) - np.maximum(bo, 0)
            h3b_axes.append(float(np.quantile(diff, 0.05)) > 0)
    # MTBI
    dur, ev = mtbi_intervals(e1, "V", "OL")
    km = ps.kaplan_meier(dur, ev)
    m, mlo, mhi = ps.rmst(km, 300)
    transfers = sum(1 for r in e1 if (r["task"], r["condition"]) == ("V", "OL"))
    q_true = 1 - (P_LOAD[("V", "OL")] + P_UNLOAD[("V", "OL")]) / 2
    rmst_true = (1 - (1 - q_true) ** 300) / q_true  # geometric renewal, restricted at 300
    L.append(f"| MTBI V-OL, RMST to 300 transfers | {rmst_true:.1f} | {m:.1f} | Greenwood {mlo:.1f}–{mhi:.1f} | {'yes' if mlo <= rmst_true <= mhi else 'no'} |")
    crude, clo, chi = ps.mtbi_crude(transfers, int(ev.sum()))
    L.append(f"| MTBI V-OL, crude | {1 / q_true:.1f} | {crude:.1f} | Garwood {clo:.1f}–{chi:.1f} | {'yes' if clo <= 1 / q_true <= chi else 'no'} |")
    s50 = ps.km_survival_at(km, 50)
    L.append(f"| S(50), V-OL | {(1 - q_true) ** 50:.3f} | {s50:.3f} | — | — |")
    # E3
    h4a_meets, h4a_cert, h4a_ref = True, True, False
    boots = {}
    for load in (0, 1):
        for k in range(5):
            pts = np.array([[r["x_mm"], r["y_mm"], r["z_mm"]] for r in e3 if r["payload"] == load and r["pose"] == f"P{k + 1}"])
            rp, lo, hi = ps.bootstrap_t_rp(pts, 4000, seed=100 * load + k, conf=0.975)
            b = ps.bootstrap_rp(pts, 4000, seed=100 * load + k)
            boots[(load, k)] = b
            rp_obs_true = math.hypot(RP_TRUE[load][k], U_INST / 2 * (2 * math.sqrt(2 / math.pi) + 3 * math.sqrt(3 - 8 / math.pi)))
            if load == 0:
                _r, lo1, hi1 = ps.bootstrap_t_rp(pts, 4000, seed=100 * load + k, conf=0.95)
                h4a_meets &= rp <= 0.10
                h4a_cert &= hi1 <= 0.10
                h4a_ref |= lo1 > 0.10
            L.append(f"| RP P{k + 1}, {'loaded' if load else 'unloaded'} (mm) | {RP_TRUE[load][k]:.3f} (arm) / {rp_obs_true:.3f} (with instrument) | {rp:.3f} | bootstrap-t 95 % {lo:.3f}–{hi:.3f} | {'yes' if lo <= rp_obs_true <= hi else 'no'} |")
    diff = np.mean([boots[(1, k)] - boots[(0, k)] for k in range(5)], axis=0)
    h4b = float(np.quantile(diff, 0.05)) > 0
    X = np.column_stack([np.ones(10), np.tile(np.array(REACH) / 100, 2), np.repeat([0.0, 1.0], 5)])
    Y = np.stack([boots[(load, k)] for load in (0, 1) for k in range(5)])
    slope = np.linalg.lstsq(X, Y, rcond=None)[0][1]
    h4c = float(np.quantile(slope, 0.05)) > 0

    L.append("\n## 2. Decisions on the synthetic campaign\n")
    L.append("What the registered rules decide, next to what the true values imply. A test can "
             "miss a true effect (low power) without being wrong; section 3 checks the "
             "procedures themselves.\n")
    L.append("| Hypothesis | Truth | Decision | Detail |")
    L.append("|---|---|---|---|")
    L.append(f"| H1a | true rate 99.8 %, so ≥ 99 % is true | {h1a} | {k_c}/{n_c} carrier OL loads; exact lower bound {ps.cp_lower(k_c, n_c):.4f} (power is 55 % at this rate) |")
    L.append(f"| H1b | true rate 93 %, so < 99 % is true | {h1b} | {k2}/{n2}; exact upper bound {ps.cp_upper(k2, n2):.4f} |")
    L.append(f"| H2 | true ED90 2.8 mm > 1.15 mm | {'supported' if h2 else 'not supported'} | Fieller lower bounds x {decisions[('C', 'OL', 'x')].ed90_lower95:.2f}, y {decisions[('C', 'OL', 'y')].ed90_lower95:.2f} mm |")
    L.append(f"| H3a | 93 % → 98.5 %, a real gain | {'supported' if p3a < 0.05 else 'not supported'} | Boschloo one-sided p = {p3a:.2g} |")
    L.append(f"| H3b | ED90 0.2 → 3.0 mm, a real gain | {'supported' if all(h3b_axes) else 'not supported'} | x {'passes' if h3b_axes[0] else 'fails'}, y {'passes' if h3b_axes[1] else 'fails'} |")
    L.append(f"| H3c (cap 5 s) | 3.0 s ≤ 5 s | {'supported' if hl_up <= 5.0 else 'not supported'} | HL upper bound {hl_up:.2f} s |")
    h4a = "supported" if h4a_meets else ("refuted" if h4a_ref else "inconclusive")
    L.append(f"| H4a | unloaded RP 0.050–0.065 mm ≤ 0.10 | {h4a}{', certified' if h4a_cert and h4a_meets else ''} | all five poses |")
    L.append(f"| H4b | payload adds 0.010–0.013 mm | {'supported' if h4b else 'not supported'} | bootstrap lower bound of the mean difference {np.quantile(diff, 0.05):.4f} mm |")
    L.append(f"| H4c | RP grows 0.0075–0.0081 mm per 100 mm | {'supported' if h4c else 'not supported'} | slope lower bound {np.quantile(slope, 0.05):.4f} mm per 100 mm |")
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
        true_rmst = (1 - (1 - q) ** tau) / q
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
            _m, lo, hi = ps.rmst(km, tau)
            hit += lo <= true_rmst <= hi
        L.append(f"| RMST 95 % (Greenwood) | {q:.0%} interventions per transfer, 600 transfers, τ = {tau} | 95 % | {hit / reps:.1%} |")
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
    L.append("\nFrom a separate run (400 data sets each, `bootstrap_t_rp`): the bootstrap-t upper "
             "bound covered 93.8 % (isotropic), 92.5 % and 91.0 % (anisotropic, variance ratios "
             "3:1:1 and 5:2:1) and 81.8 % (heavy-tailed t5); the percentile upper bound covered "
             "71–76 % in the same Gaussian settings. With no payload effect, H4b's percentile rule "
             "gave false positives 4.3 % of the time (300 data sets).\n")
    return L


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
             "that adds 0.005–0.010 mm at these sizes. This is why H4a needs *U* ≤ 0.025 mm.")
    L.append("- **Why the MTBI clock runs across sessions.** v1 censored every interval at the end "
             "of its block. With about 10 units of a cell per block, no interval could be longer "
             "than about 20 transfers, so neither S(50) nor a restricted mean to τ = 300 could be "
             "estimated. v2 lets a cell's clock run on across sessions within a configuration "
             "(PROTOCOL.md §14.4), which this script follows.")
    (OUT / "recovery.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
