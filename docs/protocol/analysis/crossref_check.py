"""Check every DOI in docs/protocol/references.md against Crossref (DataCite for arXiv).

For each reference it fetches the registered metadata and compares the title, first author's
family name, year, journal, volume and first page with what references.md says. Writes
out/crossref.md. Run:  python crossref_check.py

The requests carry a generic User-Agent and no contact details.
"""

from __future__ import annotations

import re
import sys
import time
import unicodedata
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
UA = {"User-Agent": "prereg-reference-check/1.0 (+https://github.com/vertical-cloud-lab/robot-arms)"}

# key, DOI, expected title (start), first author family name, year, container, volume, first page
REFS = [
    ("Wang2026", "10.48550/arXiv.2607.23704", "LabRobFail", "Wang", 2026, "arXiv", None, None),
    ("Kuric2018", "10.1051/matecconf/201824401015", "Measurement of industrial robot pose repeatability", "Kuric", 2018, "MATEC Web of Conferences", "244", "01015"),
    ("Wilson1927", "10.1080/01621459.1927.10502953", "Probable Inference, the Law of Succession, and Statistical Inference", "Wilson", 1927, "Journal of the American Statistical Association", "22", "209"),
    ("Clopper1934", "10.1093/biomet/26.4.404", "The use of confidence or fiducial limits illustrated in the case of the binomial", "Clopper", 1934, "Biometrika", "26", "404"),
    ("Newcombe1998", "10.1002/(SICI)1097-0258(19980430)17:8<873::AID-SIM779>3.0.CO;2-I", "Interval estimation for the difference between independent proportions", "Newcombe", 1998, "Statistics in Medicine", "17", "873"),
    ("Boschloo1970", "10.1111/j.1467-9574.1970.tb00104.x", "Raised conditional level of significance for the 2 × 2-table when testing the equality of two probabilities", "Boschloo", 1970, "Statistica Neerlandica", "24", "1"),
    ("Firth1993", "10.1093/biomet/80.1.27", "Bias reduction of maximum likelihood estimates", "Firth", 1993, "Biometrika", "80", "27"),
    ("Heinze2002", "10.1002/sim.1047", "A solution to the problem of separation in logistic regression", "Heinze", 2002, "Statistics in Medicine", "21", "2409"),
    ("Fieller1954", "10.1111/j.2517-6161.1954.tb00159.x", "Some Problems in Interval Estimation", "Fieller", 1954, "Journal of the Royal Statistical Society", "16", "175"),
    ("Hodges1963", "10.1214/aoms/1177704172", "Estimates of Location Based on Rank Tests", "Hodges", 1963, "The Annals of Mathematical Statistics", "34", "598"),
    ("Bauer1972", "10.1080/01621459.1972.10481279", "Constructing Confidence Sets Using Rank Statistics", "Bauer", 1972, "Journal of the American Statistical Association", "67", "687"),
    ("KaplanMeier1958", "10.1080/01621459.1958.10501452", "Nonparametric Estimation from Incomplete Observations", "Kaplan", 1958, "Journal of the American Statistical Association", "53", "457"),
    ("Royston2013", "10.1186/1471-2288-13-152", "Restricted mean survival time: an alternative to the hazard ratio", "Royston", 2013, "BMC Medical Research Methodology", "13", None),
    ("Klein2003", "10.1007/b97377", "Survival Analysis", "Klein", 2003, None, None, None),
    ("Garwood1936", "10.1093/biomet/28.3-4.437", "Fiducial limits for the Poisson distribution", "Garwood", 1936, "Biometrika", "28", "437"),
    ("Efron1987", "10.1080/01621459.1987.10478410", "Better Bootstrap Confidence Intervals", "Efron", 1987, "Journal of the American Statistical Association", "82", "171"),
    ("Efron1993", "10.1201/9780429246593", "An Introduction to the Bootstrap", "Efron", 1994, None, None, None),
    ("Cohen1960", "10.1177/001316446002000104", "A Coefficient of Agreement for Nominal Scales", "Cohen", 1960, "Educational and Psychological Measurement", "20", "37"),
    ("Olson2011", "10.1109/ICRA.2011.5979561", "AprilTag: A robust and flexible visual fiducial system", "Olson", 2011, "2011 IEEE International Conference on Robotics and Automation", None, "3400"),
    ("Wang2016", "10.1109/IROS.2016.7759617", "AprilTag 2: Efficient and robust fiducial detection", "Wang", 2016, "2016 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)", None, "4193"),
    ("Tsai1989", "10.1109/70.34770", "A new technique for fully autonomous and efficient 3D robotics hand/eye calibration", "Tsai", 1989, "IEEE Transactions on Robotics and Automation", "5", "345"),
    ("Nosek2018", "10.1073/pnas.1708274114", "The preregistration revolution", "Nosek", 2018, "Proceedings of the National Academy of Sciences", "115", "2600"),
    ("MacLeod2020", "10.1126/sciadv.aaz8867", "Self-driving laboratory for accelerated discovery of thin-film materials", "MacLeod", 2020, "Science Advances", "6", None),
]


def norm(s: str | None) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("×", "x")
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def fetch_crossref(doi: str) -> dict | None:
    r = requests.get(f"https://api.crossref.org/works/{requests.utils.quote(doi, safe='')}", headers=UA, timeout=30)
    if r.status_code != 200:
        return None
    m = r.json()["message"]
    year = None
    for k in ("published-print", "published-online", "issued", "published"):
        if m.get(k, {}).get("date-parts"):
            year = m[k]["date-parts"][0][0]
            break
    return {
        "title": (m.get("title") or [""])[0],
        "family": (m.get("author") or [{}])[0].get("family", ""),
        "year": year,
        "container": (m.get("container-title") or [""])[0],
        "volume": m.get("volume"),
        "page": (m.get("page") or m.get("article-number") or "").split("-")[0] or None,
        "registry": "Crossref",
    }


def fetch_datacite(doi: str) -> dict | None:
    r = requests.get(f"https://api.datacite.org/dois/{doi}", headers=UA, timeout=30)
    if r.status_code != 200:
        return None
    a = r.json()["data"]["attributes"]
    return {
        "title": a["titles"][0]["title"],
        "family": (a.get("creators") or [{}])[0].get("familyName", ""),
        "year": a.get("publicationYear"),
        "container": a.get("publisher", ""),
        "volume": None,
        "page": None,
        "registry": "DataCite",
    }


def main():
    OUT.mkdir(exist_ok=True)
    rows = []
    problems = 0
    for key, doi, title, family, year, container, volume, page in REFS:
        meta = fetch_datacite(doi) if doi.startswith("10.48550/") else fetch_crossref(doi)
        time.sleep(0.3)
        if meta is None:
            rows.append(f"| {key} | `{doi}` | — | **not found** | |")
            problems += 1
            continue
        checks = []
        checks.append(("title", norm(meta["title"]).startswith(norm(title)[:40]) or norm(title)[:40] in norm(meta["title"])))
        checks.append(("author", norm(family) == norm(meta["family"])))
        checks.append(("year", year is None or meta["year"] is None or int(meta["year"]) == year))
        if container:
            checks.append(("journal", norm(container)[:25] in norm(meta["container"]) or norm(meta["container"])[:25] in norm(container)))
        if volume:
            checks.append(("volume", str(meta["volume"]) == volume))
        if page:
            checks.append(("page", meta["page"] is not None and str(meta["page"]).lstrip("0") == page.lstrip("0")))
        bad = [n for n, ok in checks if not ok]
        problems += bool(bad)
        status = "matches" if not bad else "**mismatch: " + ", ".join(bad) + "**"
        shown = f"{meta['family']} ({meta['year']}). {meta['title']}. {meta['container']}"
        if meta["volume"]:
            shown += f" {meta['volume']}"
        if meta["page"]:
            shown += f", {meta['page']}"
        rows.append(f"| {key} | `{doi}` | {meta['registry']} | {status} | {shown} |")
        print(key, status, flush=True)
    text = ["# Reference check against Crossref", "",
            f"Generated by `crossref_check.py` on {time.strftime('%Y-%m-%d', time.gmtime())}. Each DOI in "
            "[`references.md`](../../references.md) was looked up in Crossref (DataCite for the arXiv DOI), "
            "and the registered title, first author, year, journal, volume and first page were compared "
            "with the reference as written. ISO 9283:1998 has no DOI and is not checked here.", "",
            f"**{len(REFS) - problems} of {len(REFS)} match.**", "",
            "| Key | DOI | Registry | Result | What the registry holds |", "|---|---|---|---|---|"] + rows
    (OUT / "crossref.md").write_text("\n".join(text) + "\n")
    print(f"{len(REFS) - problems}/{len(REFS)} match")
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
