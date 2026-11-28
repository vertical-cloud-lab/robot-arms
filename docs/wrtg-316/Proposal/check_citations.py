"""Check that the Works Cited is numbered in IEEE order (order of first citation).

Run from this folder: python3 check_citations.py
It follows main.tex's \\input order, lists each \\cite key in the order it first appears,
and compares that with the \\bibitem order in sections/5-works-cited.tex. Standard library
only.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMENT = re.compile(r"(?<!\\)%.*")


def read(name):
    path = HERE / (name if name.endswith(".tex") else name + ".tex")
    return COMMENT.sub("", path.read_text(encoding="utf-8"))


def expand(name):
    """Return the text of a file with its \\input files spliced in, in order."""
    return re.sub(r"\\input\{([^}]+)\}", lambda m: expand(m.group(1)), read(name))


body = expand("main.tex").split(r"\begin{document}", 1)[1]
body = body.split(r"\begin{thebibliography}", 1)[0]
cited = []
for keys in re.findall(r"\\cite\{([^}]+)\}", body):
    for key in (k.strip() for k in keys.split(",")):
        if key not in cited:
            cited.append(key)
bib = re.findall(r"\\bibitem\{([^}]+)\}", read("sections/5-works-cited"))

ok = True
if cited != bib:
    ok = False
    print("The \\bibitem order does not follow the order of first citation.")
    print("Order of first citation (use this in sections/5-works-cited.tex):")
    for n, key in enumerate(cited, 1):
        print(f"  [{n}] {key}")
missing = [k for k in cited if k not in bib]
unused = [k for k in bib if k not in cited]
if missing:
    ok = False
    print("Cited but not in the Works Cited:", ", ".join(missing))
if unused:
    ok = False
    print("In the Works Cited but never cited:", ", ".join(unused))
if ok:
    print(f"OK: {len(bib)} references, numbered in order of first citation.")
sys.exit(0 if ok else 1)
