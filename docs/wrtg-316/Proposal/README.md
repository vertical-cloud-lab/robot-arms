# WRTG 316 proposal (LaTeX)

The research paper proposal, *When Is a Low-Cost Robot Arm Good Enough for a Self-Driving
Lab?* It was drafted in [WRTG-Proposal-2](https://github.com/vertical-cloud-lab/robot-arms/issues/65)
from [`user context/proposal questions.md`](user%20context/proposal%20questions.md) and the
source list in [`../edison/Final_Selection.md`](../edison/Final_Selection.md).

## Files

| File | What it holds |
| --- | --- |
| `main.tex` | Preamble, title block, and the order of the sections. |
| `sections/1-introduction.tex` | Introduction: the research issue, questions and thesis, justification. |
| `sections/2-qualifications.tex` | Capability, library research skills, Review of Literature, Annotated Bibliography. |
| `sections/3-research-plan.tex` | Methods, proposed outline of the paper, timeline. |
| `sections/4-conclusion.tex` | Conclusion. |
| `sections/5-works-cited.tex` | Works Cited. The `\bibitem` order sets the reference numbers. |
| `sections/appendix-ieee-style.tex` | The IEEE citation rules, as the last pages. |
| `sources.tex` | Every reference, typed once in IEEE style and used by both the Annotated Bibliography and the Works Cited. |
| `refs.ris` | The same references, with every author, for importing into EndNote. |
| `check_citations.py` | Checks that the references are numbered in order of first citation. |

## Building

```bash
latexmk -pdf main.tex      # or: pdflatex main.tex, twice
```

There is no BibTeX step. IEEE's current guide (V 3.28.2025) puts an article number after the
date and never writes citation ranges like `[1]–[4]`; `IEEEtran.bst` does neither, so the
references are typed out in `sources.tex` instead.

IEEE numbers references in the order they are first cited. After adding or moving a `\cite`,
run `python3 check_citations.py`: it prints the order `sections/5-works-cited.tex` should use
if the current one is wrong.

## IEEE's guide pages (the last pages)

The appendix summarizes the IEEE rules the proposal uses. To attach IEEE's own pages after it,
open the [IEEE Reference Guide](https://journals.ieeeauthorcenter.ieee.org/wp-content/uploads/sites/7/IEEE_Reference_Guide.pdf)
(it opens as a Google Doc), choose **File → Download → PDF document**, and save it here as
`IEEE_Reference_Guide.pdf`. The next build appends pages 4, 7, 8, 15 and 16 (citing in the
text, conference papers, journal articles). The file is gitignored, because it is IEEE's
document. If IEEE updates the guide, check the page list at the top of
`sections/appendix-ieee-style.tex`.

## EndNote

In EndNote, choose **File → Import → File**, pick `refs.ris`, set **Import Option** to
*Reference Manager (RIS)* and **Text Translation** to *Unicode (UTF-8)*. EndNote's IEEE output
style should then produce the same Works Cited. Article numbers are in the *Article Number*
field.

## Before submitting

Search the `.tex` files for `% CHECK:`. Each marks something to confirm: the prices of our
arms, the instructor's and librarian's names as they should read, two figures taken from a
preprint or an article summary rather than the published full text, one claim that so far
comes only from Edison's summary of Tom et al., and the AI-use sentence, which should say how
you revised the draft.
