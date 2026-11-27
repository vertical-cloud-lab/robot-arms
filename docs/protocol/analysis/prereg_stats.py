"""Estimators, tests and decision rules registered in docs/protocol/PROTOCOL.md (§2, §14).

Every confirmatory number and every supported / refuted / inconclusive label in the reliability
campaign comes from a function in this file (the `h*_decision` functions at the end).
`simulate_and_check.py` runs them on synthetic data with known answers, and `power.py` uses
them to compute the power analysis. Nothing here talks to the arm.

Conventions
-----------
* Success probabilities are per *loading transfer*.
* All one-sided bounds are at 95 % (alpha = 0.05) unless an argument says otherwise.
* Offsets are in mm (x, y) or degrees (yaw); the capture model uses the magnitude |d|.

Only numpy and scipy are needed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import stats
from scipy.special import expit, logit

Z95_ONE_SIDED = stats.norm.ppf(0.95)  # 1.6449
Z95_TWO_SIDED = stats.norm.ppf(0.975)  # 1.9600


# ---------------------------------------------------------------------------------------
# §14.1 Single proportions
# ---------------------------------------------------------------------------------------

def wilson(k: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials (two-sided, `conf`)."""
    if n <= 0:
        raise ValueError("n must be positive")
    z = stats.norm.ppf(0.5 + conf / 2)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def cp_lower(k: int, n: int, alpha: float = 0.05) -> float:
    """Exact (Clopper-Pearson) one-sided lower bound on the success probability.

    For k == n this is alpha ** (1 / n), e.g. 0.05 ** (1 / 300) = 0.99006.
    """
    if k <= 0:
        return 0.0
    return float(stats.beta.ppf(alpha, k, n - k + 1))


def cp_upper(k: int, n: int, alpha: float = 0.05) -> float:
    """Exact (Clopper-Pearson) one-sided upper bound on the success probability."""
    if k >= n:
        return 1.0
    return float(stats.beta.ppf(1 - alpha, k + 1, n - k))


def max_failures_certifying(n: int, target: float = 0.99, alpha: float = 0.05) -> int:
    """Largest number of failures in n trials whose exact lower bound still reaches `target`.

    Returns -1 when even zero failures cannot certify `target` (n too small).
    """
    f = -1
    while f + 1 <= n and cp_lower(n - (f + 1), n, alpha) >= target:
        f += 1
    return f


def min_failures_refuting(n: int, target: float = 0.99, alpha: float = 0.05) -> int:
    """Smallest number of failures in n trials whose exact upper bound falls below `target`."""
    for f in range(n + 1):
        if cp_upper(n - f, n, alpha) < target:
            return f
    return n + 1


# ---------------------------------------------------------------------------------------
# §14.2 Two proportions
# ---------------------------------------------------------------------------------------

def newcombe_diff(k1: int, n1: int, k2: int, n2: int, conf: float = 0.95) -> tuple[float, float, float]:
    """Difference p1 - p2 with Newcombe's hybrid score interval (method 10, 1998)."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1, conf)
    l2, u2 = wilson(k2, n2, conf)
    d = p1 - p2
    lo = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return d, lo, hi


def boschloo_greater(k_treat: int, n_treat: int, k_ctrl: int, n_ctrl: int) -> float:
    """One-sided Boschloo exact p-value for H1: p_treat > p_ctrl (H3a: AT > OL)."""
    table = [[k_treat, k_ctrl], [n_treat - k_treat, n_ctrl - k_ctrl]]
    return float(stats.boschloo_exact(table, alternative="greater", n=64).pvalue)


def gap_closed(p_ol: float, p_at: float, target: float = 0.99) -> float:
    """Share of the gap to `target` closed by correction: (p_AT - p_OL) / (target - p_OL)."""
    if p_ol >= target:
        return float("nan")
    return (p_at - p_ol) / (target - p_ol)


# ---------------------------------------------------------------------------------------
# §14.3 Capture envelope: Firth logistic regression, ED50 / ED90, Fieller and bootstrap
# ---------------------------------------------------------------------------------------

@dataclass
class FirthFit:
    beta: np.ndarray  # (b0, b1): logit p = b0 + b1 * |d|
    cov: np.ndarray  # inverse Fisher information at the penalised estimate
    converged: bool
    iterations: int


def firth_logistic(x: np.ndarray, y: np.ndarray, max_iter: int = 100, tol: float = 1e-8) -> FirthFit:
    """Firth (1993) bias-reduced logistic regression of y (0/1) on one covariate x.

    Uses the modified score U*_j = sum_i (y_i - p_i + h_i (1/2 - p_i)) x_ij with Newton steps
    and step-halving on the penalised log-likelihood l(b) + 1/2 log|I(b)|, as in R's
    `logistf`. Finite estimates exist even under complete separation.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    X = np.column_stack([np.ones_like(x), x])
    beta = np.zeros(2)

    def pen_loglik(b: np.ndarray) -> float:
        eta = X @ b
        p = expit(eta)
        w = p * (1 - p)
        info = X.T @ (X * w[:, None])
        sign, logdet = np.linalg.slogdet(info)
        if sign <= 0:
            return -np.inf
        ll = np.sum(y * eta - np.logaddexp(0.0, eta))
        return ll + 0.5 * logdet

    current = pen_loglik(beta)
    converged = False
    it = 0
    for it in range(1, max_iter + 1):
        p = expit(X @ beta)
        w = p * (1 - p)
        info = X.T @ (X * w[:, None])
        info_inv = np.linalg.inv(info)
        # Hat-matrix diagonal: h_i = w_i x_i^T I^-1 x_i
        h = w * np.einsum("ij,jk,ik->i", X, info_inv, X)
        score = X.T @ (y - p + h * (0.5 - p))
        step = info_inv @ score
        # Step-halving on the penalised likelihood
        t = 1.0
        while True:
            cand = beta + t * step
            val = pen_loglik(cand)
            if val >= current - 1e-12 or t < 1e-6:
                break
            t /= 2
        beta = cand
        current = val
        if np.max(np.abs(t * step)) < tol:
            converged = True
            break
    p = expit(X @ beta)
    w = p * (1 - p)
    cov = np.linalg.inv(X.T @ (X * w[:, None]))
    return FirthFit(beta=beta, cov=cov, converged=converged, iterations=it)


def ed(beta: np.ndarray, q: float) -> float:
    """Offset magnitude at which predicted success equals q: (logit q - b0) / b1."""
    b0, b1 = beta
    if b1 == 0:
        return float("inf")
    return float((logit(q) - b0) / b1)


def fieller_interval(beta: np.ndarray, cov: np.ndarray, q: float, z: float) -> tuple[float, float]:
    """Fieller interval for ED_q = (c - b0) / b1 with c = logit q.

    `z` sets the coverage: z = 1.645 gives a two-sided 90 % interval whose lower end is the
    registered one-sided 95 % lower bound. Returns (-inf, inf) when the slope is not
    distinguishable from zero at that level (g >= 1): the interval is then unbounded.
    """
    c = logit(q)
    a = c - beta[0]  # numerator
    b = beta[1]  # denominator
    var_a = cov[0, 0]
    var_b = cov[1, 1]
    cov_ab = -cov[0, 1]
    g = z * z * var_b / (b * b)
    if g >= 1:
        return -math.inf, math.inf
    # (b^2 - z^2 var_b) t^2 - 2 (a b - z^2 cov_ab) t + (a^2 - z^2 var_a) = 0
    A = b * b - z * z * var_b
    B = -2 * (a * b - z * z * cov_ab)
    C = a * a - z * z * var_a
    disc = B * B - 4 * A * C
    if disc < 0:
        return -math.inf, math.inf
    r1 = (-B - math.sqrt(disc)) / (2 * A)
    r2 = (-B + math.sqrt(disc)) / (2 * A)
    return min(r1, r2), max(r1, r2)


@dataclass
class CaptureResult:
    ed50: float
    ed90: float
    ed90_lower95: float  # Fieller one-sided 95 % lower bound
    ed90_fieller90: tuple[float, float]  # two-sided 90 %: (one-sided 95 % lower, upper)
    ed90_fieller95: tuple[float, float]  # two-sided 95 %, for reporting
    ed90_upper99: float  # Fieller one-sided 99 % upper bound, used to refute H2
    ed50_fieller95: tuple[float, float]
    slope: float  # b1, per mm (or degree)
    slope_upper95: float  # one-sided 95 % upper bound of b1 (Wald)
    censored: bool  # the curve has not fallen to 90 % by the largest offset: report "> max"
    not_reached: bool  # fitted success is below 90 % already at zero offset: report "not reached"
    fitted_at_max: float  # fitted success at the largest |d|
    lower_bound_at_max: float  # exact one-sided 95 % lower bound of success at the largest |d|
    pooled_lower_ge2: float  # exact one-sided 95 % lower bound of success pooled over |d| >= 2 mm
    max_offset: float
    fit: FirthFit

    @property
    def slope_negative(self) -> bool:
        """Success falls with offset: the one-sided 95 % upper bound of the slope is below 0."""
        return self.slope_upper95 < 0

    @property
    def radius90(self) -> float:
        """The capture radius used in differences (H3b): ED90 floored at 0, and 0 when not reached."""
        return 0.0 if self.not_reached else max(0.0, self.ed90)


def capture_curve(abs_offset: np.ndarray, success: np.ndarray) -> CaptureResult:
    """Fit the registered capture model to one task x condition x axis.

    `abs_offset` holds |d| for every trial on that axis, including the zero level.

    Right-censoring (PROTOCOL.md §14.3): the curve is censored when there are no failures at
    the largest offset, or when the fitted success there is still >= 0.90. Its ED90 is then
    reported as "> max offset" and never extrapolated.
    """
    d = np.asarray(abs_offset, dtype=float)
    s = np.asarray(success, dtype=int)
    fit = firth_logistic(d, s)
    dmax = float(d.max())
    at_max = d == dmax
    k_max, n_max = int(s[at_max].sum()), int(at_max.sum())
    fitted_max = float(expit(fit.beta[0] + fit.beta[1] * dmax))
    fitted_zero = float(expit(fit.beta[0]))
    censored = (k_max == n_max) or fitted_max >= 0.9
    ge2 = d >= 2.0
    pooled = cp_lower(int(s[ge2].sum()), int(ge2.sum())) if ge2.any() else 0.0
    f90 = fieller_interval(fit.beta, fit.cov, 0.9, Z95_ONE_SIDED)
    return CaptureResult(
        ed50=ed(fit.beta, 0.5),
        ed90=ed(fit.beta, 0.9),
        ed90_lower95=f90[0],
        ed90_fieller90=f90,
        ed90_fieller95=fieller_interval(fit.beta, fit.cov, 0.9, Z95_TWO_SIDED),
        ed90_upper99=fieller_interval(fit.beta, fit.cov, 0.9, float(stats.norm.ppf(0.99)))[1],
        ed50_fieller95=fieller_interval(fit.beta, fit.cov, 0.5, Z95_TWO_SIDED),
        slope=float(fit.beta[1]),
        slope_upper95=float(fit.beta[1] + Z95_ONE_SIDED * math.sqrt(fit.cov[1, 1])),
        censored=censored,
        not_reached=fitted_zero < 0.9,
        fitted_at_max=fitted_max,
        lower_bound_at_max=cp_lower(k_max, n_max),
        pooled_lower_ge2=pooled,
        max_offset=dmax,
        fit=fit,
    )


def h2_axis_decision(res: CaptureResult, zero_successes: int, zero_trials: int,
                     threshold_mm: float = 1.15) -> str:
    """Registered H2 decision for one translation axis (PROTOCOL.md §2, H2).

    Returns "supported", "refuted" or "inconclusive".

    Support (one-sided 95 %):
      * censored curve: the exact lower bound of success pooled over |d| >= 2 mm is >= 0.90
        (by monotonicity, success at 1.15 mm is at least that average);
      * otherwise: the slope is significantly negative and the Fieller one-sided 95 % lower
        bound of ED90 exceeds the threshold.
    Refutation (one-sided 99 % per axis). H2 is refuted if *either* axis is, a union; Bonferroni
    would give 97.5 % per axis, but Fieller bounds undercover when ED90 lies between the 1 and
    2 mm levels, so 97.5 % refuted a true ED90 of exactly 1.15 mm 5.1-10.4 % of the time on
    synthetic data. At 99 % per axis that rate was 1.0-5.1 % (`power.py --check-rejected`,
    10,000 campaigns for each of three curve shapes):
      * the dock misses 90 % even at zero offset: the exact one-sided 99 % upper bound of success
        over E2's zero-offset trials is below 0.90 (capture radius 0); or
      * the curve is not censored, its slope is significantly negative, and the Fieller
        one-sided 99 % upper bound of ED90 is below the threshold.
    If the data meet both a support and a refutation rule they contradict a monotone capture
    curve, and the axis is "inconclusive".
    """
    supported = False
    if res.censored:
        supported = res.pooled_lower_ge2 >= 0.90
    elif res.slope_negative:
        supported = res.ed90_lower95 > threshold_mm
    refuted = cp_upper(zero_successes, zero_trials, alpha=0.01) < 0.90
    if not refuted and not res.censored and res.slope_negative:
        refuted = res.ed90_upper99 < threshold_mm
    if supported and refuted:
        return "inconclusive"
    if supported:
        return "supported"
    if refuted:
        return "refuted"
    return "inconclusive"


def h2_decision(res_x: CaptureResult, res_y: CaptureResult, zero_successes: int,
                zero_trials: int, threshold_mm: float = 1.15) -> str:
    """H2 over both axes: supported if both are, refuted if either is, else inconclusive."""
    ax = [h2_axis_decision(r, zero_successes, zero_trials, threshold_mm) for r in (res_x, res_y)]
    if "refuted" in ax:
        return "refuted"
    if all(a == "supported" for a in ax):
        return "supported"
    return "inconclusive"


def h2_model_free_check(fail_at_2mm_both_axes: int, n_at_2mm_both_axes: int = 80) -> bool:
    """Secondary (reported, not decisive): >= 90 % caught at +-2 mm on x and y together."""
    return cp_lower(n_at_2mm_both_axes - fail_at_2mm_both_axes, n_at_2mm_both_axes) >= 0.90


def bootstrap_ed90(abs_offset: np.ndarray, success: np.ndarray, n_boot: int = 10_000,
                   seed: int = 0) -> np.ndarray:
    """Percentile-bootstrap replicates of ED90, resampling trials within each offset level."""
    rng = np.random.default_rng(seed)
    d = np.asarray(abs_offset, dtype=float)
    s = np.asarray(success, dtype=int)
    levels = np.unique(d)
    groups = [s[d == L] for L in levels]
    out = np.empty(n_boot)
    for b in range(n_boot):
        ys = np.concatenate([rng.choice(g, size=g.size, replace=True) for g in groups])
        xs = np.concatenate([np.full(g.size, L) for g, L in zip(groups, levels)])
        out[b] = ed(firth_logistic(xs, ys).beta, 0.9)
    return out


# ---------------------------------------------------------------------------------------
# H3c: transfer time, Hodges-Lehmann shift with its Moses (Mann-Whitney) bound
# ---------------------------------------------------------------------------------------

def hodges_lehmann_upper(t_at: np.ndarray, t_ol: np.ndarray, conf: float = 0.95) -> tuple[float, float]:
    """HL shift (AT - OL) and its one-sided `conf` upper bound (Moses, normal approx.)."""
    a = np.asarray(t_at, dtype=float)
    o = np.asarray(t_ol, dtype=float)
    diffs = np.sort((a[:, None] - o[None, :]).ravel())
    n1, n2 = a.size, o.size
    hl = float(np.median(diffs))
    z = stats.norm.ppf(conf)
    c = int(math.floor(n1 * n2 / 2 - z * math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)))
    c = max(c, 1)
    upper = float(diffs[n1 * n2 - c])  # the (n1 n2 - c + 1)-th smallest, 0-indexed
    return hl, upper


# ---------------------------------------------------------------------------------------
# §14.4 MTBI: Kaplan-Meier, restricted mean, Garwood
# ---------------------------------------------------------------------------------------

@dataclass
class KMResult:
    times: np.ndarray  # distinct event times
    surv: np.ndarray  # S(t) just after each event time
    at_risk: np.ndarray
    events: np.ndarray
    max_time: float  # longest observed interval, event or censored


def kaplan_meier(durations: np.ndarray, observed: np.ndarray) -> KMResult:
    """Kaplan-Meier estimate. `durations` in transfers; `observed` = 1 for an intervention."""
    t = np.asarray(durations, dtype=float)
    e = np.asarray(observed, dtype=int)
    times = np.unique(t[e == 1])
    at_risk = np.array([(t >= u).sum() for u in times])
    events = np.array([((t == u) & (e == 1)).sum() for u in times])
    surv = np.cumprod(1 - events / at_risk)
    return KMResult(times=times, surv=surv, at_risk=at_risk, events=events,
                    max_time=float(t.max()) if t.size else 0.0)


def km_survival_at(km: KMResult, t: float) -> float:
    """S(t): probability of reaching t transfers without an intervention."""
    idx = np.searchsorted(km.times, t, side="right") - 1
    return 1.0 if idx < 0 else float(km.surv[idx])


def rmst_tau(km: KMResult, tau: float) -> float:
    """The horizon actually used: tau, or the cell's longest observed interval if shorter.

    Past the longest interval the Kaplan-Meier curve isn't observed, so it isn't extended
    (PROTOCOL.md §14.4).
    """
    return min(float(tau), km.max_time)


def rmst(km: KMResult, tau: float, conf: float = 0.95) -> tuple[float, float, float]:
    """Restricted mean (MTBI up to tau) with a Greenwood-type interval.

    Var = sum over event times t_i <= tau of A_i^2 d_i / (n_i (n_i - d_i)), where A_i is the
    area under S from t_i to tau (Klein and Moeschberger, section 4.5). `tau` is capped at the
    longest observed interval (`rmst_tau`); report the cap with the estimate.
    """
    tau = rmst_tau(km, tau)
    grid = np.concatenate([[0.0], km.times[km.times < tau], [tau]])
    s_vals = np.concatenate([[1.0], km.surv[km.times < tau]])
    widths = np.diff(grid)
    area = float(np.sum(s_vals * widths))
    var = 0.0
    keep = km.times < tau
    for i in np.nonzero(keep)[0]:
        ti = km.times[i]
        # area from ti to tau
        mask = grid[:-1] >= ti
        a_i = float(np.sum(s_vals[mask] * widths[mask]))
        n_i, d_i = km.at_risk[i], km.events[i]
        if n_i > d_i:
            var += a_i * a_i * d_i / (n_i * (n_i - d_i))
    z = stats.norm.ppf(0.5 + conf / 2)
    se = math.sqrt(var)
    return area, area - z * se, area + z * se


def garwood_rate_interval(events: int, exposure: float, conf: float = 0.95) -> tuple[float, float]:
    """Exact Poisson (Garwood 1936) interval for the event rate per unit exposure."""
    a = 1 - conf
    lo = 0.0 if events == 0 else stats.chi2.ppf(a / 2, 2 * events) / 2 / exposure
    hi = stats.chi2.ppf(1 - a / 2, 2 * events + 2) / 2 / exposure
    return float(lo), float(hi)


def mtbi_crude(transfers: int, interventions: int, conf: float = 0.95) -> tuple[float, float, float]:
    """Total transfers / interventions, with the interval inverted from Garwood's."""
    lo_rate, hi_rate = garwood_rate_interval(interventions, transfers, conf)
    est = math.inf if interventions == 0 else transfers / interventions
    return est, (1 / hi_rate), (math.inf if lo_rate == 0 else 1 / lo_rate)


# ---------------------------------------------------------------------------------------
# §14.5 ISO 9283 pose repeatability
# ---------------------------------------------------------------------------------------

def iso9283_rp(points: np.ndarray) -> float:
    """RP = l_bar + 3 S_l for an (n, 3) array of attained positions (ISO 9283:1998, 7.2.2)."""
    pts = np.asarray(points, dtype=float)
    centre = pts.mean(axis=0)
    lj = np.linalg.norm(pts - centre, axis=1)
    return float(lj.mean() + 3 * lj.std(ddof=1))


def bootstrap_rp(points: np.ndarray, n_boot: int = 10_000, seed: int = 0) -> np.ndarray:
    """Bootstrap replicates of RP, resampling the cycles."""
    rng = np.random.default_rng(seed)
    pts = np.asarray(points, dtype=float)
    n = pts.shape[0]
    idx = rng.integers(0, n, size=(n_boot, n))
    sample = pts[idx]  # (B, n, 3)
    centre = sample.mean(axis=1, keepdims=True)
    lj = np.linalg.norm(sample - centre, axis=2)
    return lj.mean(axis=1) + 3 * lj.std(axis=1, ddof=1)


def _rp_batch(x: np.ndarray) -> np.ndarray:
    """ISO 9283 RP over the last two axes of an (..., n, 3) array."""
    c = x.mean(axis=-2, keepdims=True)
    lj = np.linalg.norm(x - c, axis=-1)
    return lj.mean(axis=-1) + 3 * lj.std(axis=-1, ddof=1)


def _jackknife_se_rp(x: np.ndarray) -> np.ndarray:
    """Jackknife standard error of RP for each (n, 3) sample in a (B, n, 3) array."""
    n = x.shape[-2]
    idx = np.array([np.delete(np.arange(n), i) for i in range(n)])
    theta = _rp_batch(x[:, idx, :])  # (B, n)
    return np.sqrt((n - 1) / n * np.sum((theta - theta.mean(axis=1, keepdims=True)) ** 2, axis=1))


def _bootstrap_t_draws(points: np.ndarray, n_boot: int, seed: int) -> tuple[float, float, np.ndarray]:
    """RP, its jackknife SE, and the studentized bootstrap draws (RP* - RP) / SE*."""
    rng = np.random.default_rng(seed)
    pts = np.asarray(points, dtype=float)
    n = pts.shape[0]
    rp = float(_rp_batch(pts))
    se = float(_jackknife_se_rp(pts[None])[0])
    draws = []
    for start in range(0, n_boot, 1000):  # chunks keep memory small
        b = min(1000, n_boot - start)
        xb = pts[rng.integers(0, n, size=(b, n))]
        draws.append((_rp_batch(xb) - rp) / _jackknife_se_rp(xb))
    return rp, se, np.concatenate(draws)


def bootstrap_t_rp(points: np.ndarray, n_boot: int = 10_000, seed: int = 0,
                   conf: float = 0.95) -> tuple[float, float, float]:
    """RP with studentized-bootstrap (bootstrap-t) one-sided `conf` lower and upper bounds.

    The registered interval for H4a (PROTOCOL.md §14.5). Each resample is studentized by its own
    jackknife standard error. On 30 Gaussian points the percentile bootstrap's upper bound
    covered only 72-76 % in simulation; this one covers 91-93 % (85 % for heavy-tailed t5
    errors, against 61 %), see simulate_and_check.py.
    """
    rp, se, t_all = _bootstrap_t_draws(points, n_boot, seed)
    q_hi, q_lo = np.quantile(t_all, [conf, 1 - conf])
    return rp, rp - q_hi * se, rp - q_lo * se


# ---------------------------------------------------------------------------------------
# Agreement between scorers (§7, §13.3)
# ---------------------------------------------------------------------------------------

def cohen_kappa(a: np.ndarray, b: np.ndarray) -> float:
    """Cohen's kappa for two raters' labels."""
    a = np.asarray(a)
    b = np.asarray(b)
    labels = np.unique(np.concatenate([a, b]))
    po = float(np.mean(a == b))
    pe = float(sum(np.mean(a == L) * np.mean(b == L) for L in labels))
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


# ---------------------------------------------------------------------------------------
# Registered decisions (PROTOCOL.md §2): one function per hypothesis
# ---------------------------------------------------------------------------------------

N_BOOT = 10_000  # registered number of bootstrap resamples
SEED = 20261127  # registered seed for every bootstrap below


def h1a_decision(k: int, n: int, target: float = 0.99) -> str:
    """H1a, p >= target: supported if the exact lower bound reaches it, refuted if the exact
    upper bound falls below it, else inconclusive (both one-sided 95 %)."""
    if cp_lower(k, n) >= target:
        return "supported"
    if cp_upper(k, n) < target:
        return "refuted"
    return "inconclusive"


def h1b_decision(k: int, n: int, target: float = 0.99) -> str:
    """H1b, p < target: the mirror image of H1a."""
    if cp_upper(k, n) < target:
        return "supported"
    if cp_lower(k, n) >= target:
        return "refuted"
    return "inconclusive"


def h3a_decision(k_at: int, n_at: int, k_ol: int, n_ol: int, alpha: float = 0.05) -> str:
    """H3a, p_AT > p_OL by one-sided Boschloo: supported, contrary (the reverse is
    significant) or not supported."""
    if boschloo_greater(k_at, n_at, k_ol, n_ol) < alpha:
        return "supported"
    if boschloo_greater(k_ol, n_ol, k_at, n_at) < alpha:
        return "contrary"
    return "not supported"


def gap_closed_interval(k_ol: int, n_ol: int, k_at: int, n_at: int, target: float = 0.99,
                        n_boot: int = N_BOOT, seed: int = SEED) -> tuple[float, float, float]:
    """G = (p_AT - p_OL) / (target - p_OL) with a 95 % percentile-bootstrap interval.

    Resamples the loads of each condition (equivalently, binomial draws at the observed rates);
    resamples whose open-loop rate reaches the target are dropped, as G is undefined there.
    Returns (nan, nan, nan) when the observed open-loop rate reaches the target.
    """
    p_ol, p_at = k_ol / n_ol, k_at / n_at
    if p_ol >= target:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    bo = rng.binomial(n_ol, p_ol, n_boot) / n_ol
    ba = rng.binomial(n_at, p_at, n_boot) / n_at
    keep = bo < target
    g = (ba[keep] - bo[keep]) / (target - bo[keep])
    lo, hi = np.quantile(g, [0.025, 0.975])
    return gap_closed(p_ol, p_at, target), float(lo), float(hi)


def delta_se_ed90(res: CaptureResult) -> float:
    """Delta-method standard error of ED90 from the Firth fit's covariance."""
    b0, b1 = res.fit.beta
    c = logit(0.9)
    g = np.array([-1.0 / b1, -(c - b0) / b1 ** 2])
    return float(math.sqrt(max(g @ res.fit.cov @ g, 0.0)))


def h3b_axis_supported(res_at: CaptureResult, res_ol: CaptureResult) -> bool:
    """Registered H3b decision for one axis (PROTOCOL.md §2, H3b).

    * Corrected curve censored: holds if the Fieller one-sided 95 % upper bound of ED90_OL is
      below the largest offset tested.
    * Otherwise: the one-sided 95 % delta-method lower bound of radius90_AT - radius90_OL
      exceeds 0 (a radius of 0 contributes no variance).

    A percentile bootstrap of the same difference was rejected: on synthetic data with equal
    ED90s but different slopes it gave false support 11 % of the time on both axes; this rule
    gave at most 2.8 % (simulate_and_check.py, power.py).
    """
    if res_at.censored:
        return res_ol.ed90_fieller90[1] < res_at.max_offset
    ra, ro = res_at.radius90, res_ol.radius90
    se = math.hypot(delta_se_ed90(res_at) if ra > 0 else 0.0,
                    delta_se_ed90(res_ol) if ro > 0 else 0.0)
    return (ra - ro) - Z95_ONE_SIDED * se > 0


def h3b_decision(at_x: CaptureResult, ol_x: CaptureResult, at_y: CaptureResult,
                 ol_y: CaptureResult) -> str:
    """H3b over both axes: supported if both pass, else not supported."""
    ok = h3b_axis_supported(at_x, ol_x) and h3b_axis_supported(at_y, ol_y)
    return "supported" if ok else "not supported"


def h3c_decision(t_at: np.ndarray, t_ol: np.ndarray, cap_s: float) -> str:
    """H3c: the one-sided 95 % upper bound of the HL shift (AT - OL) is at most the cap."""
    _hl, upper = hodges_lehmann_upper(t_at, t_ol)
    return "supported" if upper <= cap_s else "not supported"


RP_PER_SIGMA = 2 * math.sqrt(2 / math.pi) + 3 * math.sqrt(3 - 8 / math.pi)  # RP / sigma, Gaussian


def rp_refutation_threshold(spec_mm: float, u_axis_mm: float) -> float:
    """The measured RP an arm exactly at `spec_mm` would show through an instrument with
    per-axis standard uncertainty `u_axis_mm` (isotropic Gaussian approximation). The
    instrument only adds scatter, so refuting the spec needs the measured RP above this."""
    sigma = spec_mm / RP_PER_SIGMA
    return RP_PER_SIGMA * math.hypot(sigma, u_axis_mm)


def h4a_decision(poses_unloaded: list[np.ndarray], u_axis_mm: float, expanded_u_mm: float,
                 spec_mm: float = 0.10, n_boot: int = N_BOOT, seed: int = SEED) -> tuple[str, bool]:
    """H4a over the five unloaded poses. Returns (label, certified).

    Precedence: inconclusive if the instrument's expanded uncertainty exceeds 25 % of the spec
    (ISO 9283 §6.5); refuted if at any pose the bootstrap-t one-sided 99 % lower bound
    (Bonferroni over 5 poses) exceeds `rp_refutation_threshold`; supported if every point
    estimate is <= spec (the instrument can only inflate it); otherwise inconclusive.
    `certified` adds that every bootstrap-t one-sided 95 % upper bound is <= spec.
    """
    if expanded_u_mm > 0.25 * spec_mm:
        return "inconclusive", False
    thr = rp_refutation_threshold(spec_mm, u_axis_mm)
    alpha_pose = 0.05 / len(poses_unloaded)
    rps, uppers, refuted = [], [], False
    for i, pts in enumerate(poses_unloaded):
        rp, se, t_all = _bootstrap_t_draws(pts, n_boot, seed + i)
        q_refute, q_cert = np.quantile(t_all, [1 - alpha_pose, 0.05])
        rps.append(rp)
        uppers.append(rp - q_cert * se)  # one-sided 95 % upper bound
        refuted |= (rp - q_refute * se) > thr  # one-sided (1 - alpha_pose) lower bound
    if refuted:
        return "refuted", False
    if all(r <= spec_mm for r in rps):
        return "supported", all(u <= spec_mm for u in uppers)
    return "inconclusive", False


def h4bc_decisions(points: dict, reach_mm: list[float], n_boot: int = N_BOOT,
                   seed: int = SEED) -> dict:
    """H4b (RP grows with payload) and H4c (RP grows with reach).

    `points[(pose_index, payload)]` is the (30, 3) array of attained positions, payload 0 or 1.
    Cycles are resampled within each pose x payload; H4b needs the one-sided 95 % lower bound
    of the mean over poses of RP(loaded) - RP(unloaded) above 0, and H4c the one-sided 95 %
    lower bound of the reach slope (per 100 mm, payload as a covariate) above 0.
    """
    n_pose = len(reach_mm)
    boots = {key: bootstrap_rp(v, n_boot, seed + 10 * key[0] + key[1]) for key, v in points.items()}
    diff = np.mean([boots[(k, 1)] - boots[(k, 0)] for k in range(n_pose)], axis=0)
    X = np.column_stack([np.ones(2 * n_pose), np.tile(np.asarray(reach_mm) / 100.0, 2),
                         np.repeat([0.0, 1.0], n_pose)])
    Y = np.stack([boots[(k, load)] for load in (0, 1) for k in range(n_pose)])
    slope = np.linalg.lstsq(X, Y, rcond=None)[0][1]
    lb_b, lb_c = float(np.quantile(diff, 0.05)), float(np.quantile(slope, 0.05))
    return {"h4b": "supported" if lb_b > 0 else "not supported", "h4b_lower": lb_b,
            "h4c": "supported" if lb_c > 0 else "not supported", "h4c_lower": lb_c}

