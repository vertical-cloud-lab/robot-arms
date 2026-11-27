"""Estimators and tests registered in docs/protocol/PROTOCOL.md (section 12).

Every confirmatory number in the reliability campaign comes from a function in this file.
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
# 12.1 Single proportions
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
# 12.2 Two proportions
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
# 12.3 Capture envelope: Firth logistic regression, ED50 / ED90, Fieller and bootstrap
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
    ed90_lower95: float  # registered one-sided 95 % lower bound (Fieller)
    ed90_fieller90: tuple[float, float]  # two-sided 90 %: (one-sided 95 % lower, upper)
    ed50_fieller95: tuple[float, float]
    censored: bool  # the curve has not fallen to 90 % by the largest offset: report "> max"
    not_reached: bool  # fitted success is below 90 % already at zero offset: report "< 0"
    fitted_at_max: float  # fitted success at the largest |d|
    pooled_lower_ge2: float  # exact lower bound of success pooled over |d| >= 2 mm
    max_offset: float
    fit: FirthFit

    @property
    def radius90(self) -> float:
        """ED90 floored at zero, the capture radius used in differences (H3b)."""
        return max(0.0, self.ed90)


def capture_curve(abs_offset: np.ndarray, success: np.ndarray) -> CaptureResult:
    """Fit the registered capture model to one task x condition x axis.

    `abs_offset` holds |d| for every trial on that axis, including the zero level.

    Right-censoring (PROTOCOL.md 12.3): the curve is censored when there are no failures at
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
        ed50_fieller95=fieller_interval(fit.beta, fit.cov, 0.5, Z95_TWO_SIDED),
        censored=censored,
        not_reached=fitted_zero < 0.9,
        fitted_at_max=fitted_max,
        pooled_lower_ge2=pooled,
        max_offset=dmax,
        fit=fit,
    )


def h2_axis_supported(res: CaptureResult, threshold_mm: float = 1.15) -> bool:
    """Registered H2 decision for one translation axis (PROTOCOL.md 2, H2).

    * Not censored: supported when the Fieller one-sided 95 % lower bound of ED90 exceeds
      the threshold.
    * Censored (the curve has not fallen to 90 % by 4 mm): the logistic fit cannot place
      ED90, so use monotonicity instead. Success at 1.15 mm is at least the average success
      over every level at or beyond 2 mm, so H2 is supported when the exact one-sided 95 %
      lower bound of the pooled success over |d| >= 2 mm is at least 0.90.
    """
    if res.censored:
        return res.pooled_lower_ge2 >= 0.90
    return res.ed90_lower95 > threshold_mm


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
# 12.4 MTBI: Kaplan-Meier, restricted mean, Garwood
# ---------------------------------------------------------------------------------------

@dataclass
class KMResult:
    times: np.ndarray  # distinct event times
    surv: np.ndarray  # S(t) just after each event time
    at_risk: np.ndarray
    events: np.ndarray


def kaplan_meier(durations: np.ndarray, observed: np.ndarray) -> KMResult:
    """Kaplan-Meier estimate. `durations` in transfers; `observed` = 1 for an intervention."""
    t = np.asarray(durations, dtype=float)
    e = np.asarray(observed, dtype=int)
    times = np.unique(t[e == 1])
    at_risk = np.array([(t >= u).sum() for u in times])
    events = np.array([((t == u) & (e == 1)).sum() for u in times])
    surv = np.cumprod(1 - events / at_risk)
    return KMResult(times=times, surv=surv, at_risk=at_risk, events=events)


def km_survival_at(km: KMResult, t: float) -> float:
    """S(t): probability of reaching t transfers without an intervention."""
    idx = np.searchsorted(km.times, t, side="right") - 1
    return 1.0 if idx < 0 else float(km.surv[idx])


def rmst(km: KMResult, tau: float, conf: float = 0.95) -> tuple[float, float, float]:
    """Restricted mean (MTBI up to tau) with a Greenwood-type interval.

    Var = sum over event times t_i <= tau of A_i^2 d_i / (n_i (n_i - d_i)), where A_i is the
    area under S from t_i to tau (Klein and Moeschberger, section 4.5).
    """
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
# 12.5 ISO 9283 pose repeatability
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


# ---------------------------------------------------------------------------------------
# Agreement between scorers (section 6)
# ---------------------------------------------------------------------------------------

def cohen_kappa(a: np.ndarray, b: np.ndarray) -> float:
    """Cohen's kappa for two raters' labels."""
    a = np.asarray(a)
    b = np.asarray(b)
    labels = np.unique(np.concatenate([a, b]))
    po = float(np.mean(a == b))
    pe = float(sum(np.mean(a == L) * np.mean(b == L) for L in labels))
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)
