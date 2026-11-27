# Pre-registration: PiPER reliability at loading a CubXL-geometry dock (#21)

This folder is the pre-registration for the PiPER reliability campaign: how reliably the arm loads
a CubXL-style dock with 8 + 1 vial carriers and with single vials, and how much of the gap to 99 %
per transfer a lead-in dock and wrist-camera AprilTag correction each close. Nothing here moves the
arm.

## Where it stands (2026-11-27)

| Piece | State |
|---|---|
| Protocol text ([`PROTOCOL.md`](PROTOCOL.md)) | **Complete draft, v2.** Every section the registry asks for is written. It is not locked: the PI's decisions in [§0](PROTOCOL.md#0-decisions-before-locking) are still blank |
| Registry form answers ([`osf/`](osf/)) | Written for both registrations, question by question, ready to paste |
| Power analysis ([`analysis/power.py`](analysis/power.py), [`analysis/out/power.md`](analysis/out/power.md)) | **Rerun on the corrected rules** (after the independent review), with fixed seeds: exact where possible, simulated otherwise. It also simulates, on the same draws, the rules the review replaced, so every "before the fix" rate in PROTOCOL.md can be reproduced, and how often the run-of-failures stop (D11) fires. Every number in PROTOCOL.md and the `osf/` answers comes from `power.md` (including its closed-form section) or `recovery.md`, apart from inputs taken from the hardware threads (masses, clearances, tag sizes) and stated assumptions (time per transfer, per reset and per pose visit) |
| Analysis code ([`analysis/prereg_stats.py`](analysis/prereg_stats.py)) | Written, with one `h*_decision` function per hypothesis, so every supported/refuted/inconclusive label is code. [`simulate_and_check.py`](analysis/simulate_and_check.py) runs it on a synthetic campaign with known answers and checks interval coverage ([`out/recovery.md`](analysis/out/recovery.md)). That dry run caught two flaws in v1, and an independent review of the package caught several more (listed in [PROTOCOL.md §16](PROTOCOL.md#16-amendments)). All are fixed |
| Check against the bench and PR 23 ([`hardware-and-safety-check.md`](hardware-and-safety-check.md)) | Done. **Most of the campaign's hardware does not exist yet** (the dock, carriers, finger inserts, shelf, trial harness, correction code and metrology fixture) |
| Bench readiness ([`bench-readiness.md`](bench-readiness.md)) | Gates listed with suggested owners and realistic dates. None is met yet |
| Design summary ([`study-design-table.md`](study-design-table.md)) | One row per hypothesis, in PCI RR's column layout |
| References ([`references.md`](references.md)) | 30 sources. All 23 DOIs match Crossref or DataCite ([`analysis/out/crossref.md`](analysis/out/crossref.md)). One claim is still unchecked: the Ada 97.5 % figure in §1 |
| Registered | **No.** Nothing has been submitted anywhere |

## Registry and format: OSF Preregistration, two registrations

**Choice.** Register on [OSF Registries](https://osf.io/registries) with the **OSF Preregistration**
template (version 4, the current one on 2026-11-27, read from OSF's API). Use two registrations:

- **A. Transfer reliability and capture envelope** (E1 and E2, H1–H3): [`osf/A-transfer-reliability.md`](osf/A-transfer-reliability.md).
- **B. Pose repeatability** (E3, H4): [`osf/B-pose-repeatability.md`](osf/B-pose-repeatability.md).

**Why OSF and not a Registered Report Stage 1:**

1. **I found no robotics or lab-automation journal that offers Registered Reports.** A Stage 1 would
   have to go to a general-science venue, such as PCI Registered Reports and then a "PCI RR-friendly"
   journal like Royal Society Open Science, or to PLOS ONE. That would decide the paper's journal now.
2. **The hardware is not built.** The dock, carriers, finger inserts and offset plates exist only as
   CAD ([byu-vcl PR 272](https://github.com/vertical-cloud-lab/byu-vcl/pull/272)), and there is no
   trial harness. A Stage 1 is judged on a design that's ready to run, and in-principle acceptance
   (IPA) locks it. Here the design will keep shifting until the parts are printed and piloted.
3. **Timing.** OSF registration is free and immediate, mints a DOI, and can stay embargoed for up to
   four years. A Stage 1 review takes months, and no counted trial may run before IPA.
4. **The door stays open.** [`study-design-table.md`](study-design-table.md) is already in the
   format PCI RR asks for. If you want IPA instead, a Stage 1 needs only an introduction, this
   methods text, that table and pilot data.

**Why two registrations.** The template asks for one registration per study. E3 needs a metrology
fixture that doesn't exist yet, and it shares no trials with E1 and E2. Splitting means E1 and E2
can be registered and started without waiting for it.

**OSF is changing.** Since 2026-11-16 nobody can create new OSF *projects*, and every project
becomes read-only after 2027-02-19. COS says registrations continue unchanged
([cos.io/osf-changes](https://www.cos.io/osf-changes)). So create each registration directly from
OSF Registries (**Add New**, with no project), and attach the files to the template's upload fields.
An update to a registration can't add or remove files, so attach everything at submission.

## How to register (once the "before registration" gates are met)

1. Fill in every decision in [PROTOCOL.md §0](PROTOCOL.md#0-decisions-before-locking) and commit.
2. Tag that commit `prereg-v1`, so the text and the code can be cited by hash.
3. Build the attachments:
   `pandoc docs/protocol/PROTOCOL.md -o PROTOCOL.pdf` (or open PROTOCOL.md on GitHub at the tag
   and print it to PDF), and `git archive prereg-v1 docs/protocol/analysis -o analysis.zip`.
4. On OSF Registries: **Add New** → *OSF Preregistration*. Paste each answer from
   `osf/A-transfer-reliability.md`. Attach `PROTOCOL.pdf` to *Study design* and `analysis.zip` to
   *Statistical models*. Add the contributors. Choose public or an embargo (I'd make it public, so
   the timestamp can be checked before the paper is reviewed).
5. Submit. OSF e-mails each admin contributor to approve it before it becomes final.
6. Write the DOI into PROTOCOL.md's header and into #21.
7. Register B the same way when its gates are met.

The registration is the first irreversible step: once approved, it can be withdrawn but never deleted.

## Realistic dates

From [`bench-readiness.md`](bench-readiness.md#realistic-dates), assuming work starts the week of
2026-11-30 and little happens over the winter break:

| Milestone | Realistic | Earliest |
|---|---|---|
| Register A | **2027-01-29** | 2026-12-04, if you register on the CAD design and accept amending later |
| Register B | **2027-02-19** | 2027-01-29 |
| First counted block | **2027-03-05** | 2027-02-12 |
| Results paper submitted | **2027-06-25** | 2027-05-14 |

## Target journal

**Nobody has named one.** That's true of #21 and every other thread in this repo (checked
2026-11-27). It doesn't block registration, because the OSF route doesn't depend on a journal. For
the results paper I'd suggest **Digital Discovery** (RSC): it publishes self-driving-lab hardware
and methods, and its guidelines expect a data availability statement that also covers custom code.
The [data and code availability](PROTOCOL.md#11-data-recorded-and-availability) plan in PROTOCOL.md
is written to that standard. Pick before the campaign ends, not before registering.

## Files

| File | What it is |
|---|---|
| [`PROTOCOL.md`](PROTOCOL.md) | The full protocol. Uploaded with both registrations |
| [`osf/A-transfer-reliability.md`](osf/A-transfer-reliability.md) | Answers to every OSF Preregistration question for E1 and E2 |
| [`osf/B-pose-repeatability.md`](osf/B-pose-repeatability.md) | The same for E3 |
| [`study-design-table.md`](study-design-table.md) | One row per hypothesis: test, sample, sensitivity, interpretation (PCI RR format) |
| [`bench-readiness.md`](bench-readiness.md) | What must be true on the bench before registration and before the first counted trial |
| [`hardware-and-safety-check.md`](hardware-and-safety-check.md) | The protocol checked against the cell as it is and against the PR 23 safety drafts |
| [`references.md`](references.md) | References, each DOI checked against Crossref |
| [`analysis/`](analysis/) | `prereg_stats.py` (the registered estimators), `power.py`, `simulate_and_check.py`, `crossref_check.py` and their outputs in `out/` |

To reproduce the numbers: `pip install -r analysis/requirements.txt`, then
`python analysis/power.py --check-rejected` (about an hour on one core: 54 minutes on the CI runner) and
`python analysis/simulate_and_check.py` (about 4 minutes).
