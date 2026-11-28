# Survey of vertical-cloud-lab/byu-vcl, for 6-DOF arm project selection

Snapshot taken 2026-11-28. Repo: https://github.com/vertical-cloud-lab/byu-vcl (PI: sgbaird).

**What was read.** The README, CLAUDE.md and `docs/stream-cams.md` on `main`. The org profile README (vertical-cloud-lab/.github). The index of all 180 issues and 189 PRs. Full threads, with long bot comments trimmed, for about 70 issues and 55 PRs updated since 2026-08-01. All 139 comments of #133 (CubXL setup) were fetched over REST.

**Two structural facts to keep in mind:**
- **Work has moved out of this repo.** The 6-DOF arm work left for vertical-cloud-lab/robot-arms on 2026-10-09; the closed PRs here say "Moved to vertical-cloud-lab/robot-arms#…" (e.g. [PR 240](https://github.com/vertical-cloud-lab/byu-vcl/pull/240#issuecomment-6089435866), [PR 56](https://github.com/vertical-cloud-lab/byu-vcl/pull/56#issuecomment-6089438114)). On 2026-10-22 the atomizer, powder-enclosure and metal-AM work moved to vertical-cloud-lab/digital-alloy-lab (DAL), with 40 issues transferred ([PR 300](https://github.com/vertical-cloud-lab/byu-vcl/pull/300)). That PR says what stays here: "room-wide lab operations, the CubXL and powder doser, alloy characterization, and the TMS 2027 paper kit".
- **Most recent output lives on open PR branches, not on `main`.** That includes the vertical-lab design, the digital twin and the facility study. `main` holds CLAUDE.md, `cubos/`, `wireless-color-sensor/`, `potentiostat/`, `modules/electromagnetic-capper/`, `hardware/`, `SOP/` and `docs/stream-cams.md`.

---

## Decision-relevant takeaways (my synthesis; facts are sourced in the sections below)

1. **The lab's strategic direction is a "vertical cloud lab" for autonomous alloy discovery.** The design runs two campaigns: aluminium (FLAIME, for DOE's Genesis Mission) and copper/DED (the ONR YIP). It has been drawn over 16 rounds with **two MiR250 + UR12e mobile manipulators and Kardex vertical lift modules (VLMs)**. In it the PiPER was swapped out for a UR ([#303](https://github.com/vertical-cloud-lab/byu-vcl/issues/303#issuecomment-6450405539), 10-27).
   - On 11-27 the lab's own analysis concluded the VLM is **not** worth it under current conditions, and that two mobile manipulators serving benches beat it once outside users are added ([#407](https://github.com/vertical-cloud-lab/byu-vcl/issues/407#issuecomment-7212034341)).
   - The same analysis flags that **"The handling times are stand-ins. Nobody has timed a MiR250 + UR12e at our instruments."**
   - **Implication:** a PiPER cell producing *measured* handling times and reliability numbers at real instruments would feed the twin (PRs 393–427) directly. That fits the lab's "frugal twin" doctrine.
2. **The most fully specified arm task in this repo is CubXL vial and carrier handoff** ([#266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266#issuecomment-6038926935), 10-07).
   - The analysis there gives the dock geometry, the payload, the PiPER's reach and joint limits, a tolerance budget and a staged test plan with pass criteria (200 carrier swaps and 200 vial moves, then ±2 mm capture), plus an MQTT handshake.
   - [PR 272](https://github.com/vertical-cloud-lab/byu-vcl/pull/272#issuecomment-6103301940) (10-10) asked for printable parts. There has been no activity on it here since.
3. **The most timely task is clearing printer plates.**
   - On 11-26 sgbaird wrote that multi-colour Rexagons will be printed on the A1 mini and "we will probably try auto-removing them via a ping to robot-arms" ([PR 402](https://github.com/vertical-cloud-lab/byu-vcl/pull/402#issuecomment-7201176343)). That is for the ME toy drive: first delivery Dec 10, last day Dec 18 ([#399](https://github.com/vertical-cloud-lab/byu-vcl/issues/399)).
   - Today people clear every plate, and the print workflow won't send without a camera frame showing the plate clear.
   - A DAL PR reframed an NSF EAGER concept as an "FDM print-farm integration testbed (50× Bambu A1 Mini + UR5e)" ([DAL PR 10](https://github.com/vertical-cloud-lab/digital-alloy-lab/pull/10); pointer only, not read).
4. **Deadlines an arm result could feed:**
   - TMS 2027 in March: the CubXL talk and the camera poster are among 13 student abstracts. Drafts go to co-authors Jan 29, and preprints/submissions are due Feb 26 ([#273](https://github.com/vertical-cloud-lab/byu-vcl/issues/273)).
   - The Genesis Mission Graduate Fellowship: full applications are due **Jan 12, 2027**, and topic **11-A "Advanced Robotics for Dynamic Laboratory Environments"** qualifies a thesis ([#324](https://github.com/vertical-cloud-lab/byu-vcl/issues/324#issuecomment-6641925527)).
   - The Anthropic AI for Science credit application, submitted 11-06, puts an **"arm cell" in months 2–4** ([#325](https://github.com/vertical-cloud-lab/byu-vcl/issues/325#issuecomment-6666720744)).
   - The ONR YIP proposal was slated for submission by BYU's sponsored-programs office on 10-28 ([PR 291](https://github.com/vertical-cloud-lab/byu-vcl/pull/291#issuecomment-6379396044)). Its Fig. 6 is the CubXL copper corrosion screen ([#350](https://github.com/vertical-cloud-lab/byu-vcl/issues/350#issuecomment-6958212534)).
5. **Remote operation works today through one path:** a GitHub comment starts Claude Code in Actions, which reaches a Raspberry Pi over Tailscale SSH, and the Pi drives the instrument.
   - Risky actions sit behind GitHub environment approvals (`@claude-print`). Stream cameras push to YouTube.
   - The older cloud-lab demo stack (MQTT, MongoDB, the OT-2-LCM Hugging Face Space) exists on paper but is effectively dark. The OT-2's camera and network Pi left on 11-10, and the YouTube API key was never provisioned.
6. **The CubXL Pi is a single point of failure.** It runs CubOS and a deck camera. It is also the OT-2's network link (since 11-17), the Remote Desktop relay to the potentiostat PC, and the lab's residential-IP proxy for web research. It stopped passing traffic mid-calibration on 11-17 ([#349](https://github.com/vertical-cloud-lab/byu-vcl/issues/349#issuecomment-6936317028)). An arm reliability campaign loading the CubXL should not add to that Pi's load.
7. **The OT-2 "needs new direction"** (timothy-commins, 11-12, [#322](https://github.com/vertical-cloud-lab/byu-vcl/issues/322#issuecomment-6832033627)). It has a heater-shaker, its P300 isn't calibrated, it has no overhead camera, and its BaSO4 precipitation runs are only partly working. It is a candidate second instrument for arm tending.
8. **Constraints:**
   - Few people doing hands-on hardware work in this repo over the last two weeks: benwhitney5463 on the CubXL, timothy-commins on the OT-2. Atomizer, LPBF and doser work happens in DAL and powder-doser.
   - sgbaird's attention is on the twin and the visualizations: 22 comments on PR 318 in the last 2 weeks.
   - The semester ends in December.
   - BYU discourages charging external users ([#106](https://github.com/vertical-cloud-lab/byu-vcl/issues/106#issuecomment-4909744481)).
   - Purchases go through ME Orders approved by sgbaird, and the budget is tight.
   - Metal-powder safety rules apply: Class D extinguishers, cylinder limits, PPE including full-face respirators.

---

## (a) The lab's stated mission and strategic goals

- **Org profile README** ([vertical-cloud-lab/.github](https://github.com/vertical-cloud-lab/.github/blob/main/profile/README.md), current):
  - "we integrate the concepts of vertical automation, cloud experimentation, and frugal twins into self-driving labs focused on discovering new structural, aerospace, and energy materials."
  - **Vertical automation:** "Vertical labs maximize *automation-friendly* vertical space utilization—so equipment comes to the operator (e.g., via a vertical lift module) rather than the operator moving between instruments." The figure caption reads: "When samples need to be transferred or maintenance needs to occur, the tray is brought back to the operator (e.g., robotic arm, human)."
  - **Cloud experimentation:** "Cloud labs enable remote, decentralized access to experimental resources." The color-mixing demo (AccelerationConsortium/OT-2-LCM): "As of Aug 2025, 1000+ experiments have been run asynchronously by dozens of users… used for … outreach, demos, coursework, and workshops."
  - **Frugal twins:** "low-cost, modular physical twins … enabling low-risk prototyping, lower barriers to lab automation, and multi-fidelity optimization."
  - **Alloy thrust:** "we will begin by creating a remotely accessible self-driving lab workflow that integrates a vertical lift module, low-cost powder dosing units, an ultrasonic atomizer, a small-scale metal 3D printer, and mechanical testing equipment."
  - **The other two thrusts:** autonomous electrochemistry ("3D printed electrochemical cells, automated sample exchange") and advanced Bayesian optimization (Honegumi).
- **ME department handout entry** (bullets sgbaird used, [#214](https://github.com/vertical-cloud-lab/byu-vcl/issues/214#issuecomment-5671076211), 09-14): "closing the loop between powder dosing, ultrasonic atomization, metal 3D printing, and mechanical testing so that new additively manufactured aerospace alloys are proposed, produced, and tested with minimal human intervention". Cloud labs are "remotely operated experiments that students and collaborators anywhere can queue from a web browser or a Python script and watch on a livestream".
- **AI for Science application, submitted 11-06** (sgbaird's own edits, [#325](https://github.com/vertical-cloud-lab/byu-vcl/issues/325#issuecomment-6666720744); "Submitted." [11-06](https://github.com/vertical-cloud-lab/byu-vcl/issues/325#issuecomment-6679028619)):
  - "The bottleneck is the physical workflow: sample holders, camera mounts, docking plates robot motions, custom tooling, etc. that move liquids, powders, and parts across synthesis, characterization, and testing equipment."
  - The question it poses: "can a language-model agent design and validate this connecting hardware, and the robot workflows around it, well enough that the alloy loop runs with minimal human handling, with full provenance and traceability?"
  - **Timeline:** "Months 1–2: pipeline and first fixtures (cup station, press nest and ejector, cup carrier, SEM stub holder). Months 2–4: arm cell, corrosion station and sieving modules … Months 4–6: closed-loop runs on at least ten compositions."
  - "We plan to extend this to over 100 independent modules."
  - It also counts 575 executed Claude sessions in 30 days across seven lab repos.
- **Current priorities stated by sgbaird:**
  - **CubXL direction** ([#298](https://github.com/vertical-cloud-lab/byu-vcl/issues/298), 10-22): "copper corrosion testing takes priority over automated dosing into multiple cups which takes priority over spectroscopy work, at least for now." On corrosion: "I see this as a priority right now" ([comment](https://github.com/vertical-cloud-lab/byu-vcl/issues/298#issuecomment-6352253304)).
  - **10-24, on the potentiostat PR:** "we're actually going to focus much more on the corrosion work for alloys" ([PR 291](https://github.com/vertical-cloud-lab/byu-vcl/pull/291#issuecomment-6379392718)). Later the same day, with the ONR deadline close: "demonstrating atomization is the priority right now" ([PR 291](https://github.com/vertical-cloud-lab/byu-vcl/pull/291#issuecomment-6388624186)).
  - **Throughput goal** (PR 318, 11-08): "Approx. one full alloy tested per day was the estimation. How can we get that up to 10/day?" ([comment](https://github.com/vertical-cloud-lab/byu-vcl/pull/318#issuecomment-6718366653)).
  - **Mobile manipulators, not rails** (11-20): "We moved fully over to the mobile manipulator setup, no?" ([PR 318](https://github.com/vertical-cloud-lab/byu-vcl/pull/318#issuecomment-7046840630)).
  - **Scale-up vision** (11-24): a render of the lab "scaled to a $200M facility, with many vertical lift modules …, many ultrasonic atomizers, several gas atomizers, all operating … independently and asynchronously" ([PR 318](https://github.com/vertical-cloud-lab/byu-vcl/pull/318#issuecomment-7123157918)).
- **Provenance as lab culture** (gage-erickson, [#322](https://github.com/vertical-cloud-lab/byu-vcl/issues/322#issuecomment-6809538709), 11-11): "GitHub provides a unique platform for use to complete 100% provenance on the things going on in the lab. The purpose of that is ENTIRELY CRUCIAL to the PURPOSE of the lab."
- **Commercialization and open science:**
  - Startup landscape study ([PR 267](https://github.com/vertical-cloud-lab/byu-vcl/pull/267), 10-09 onward).
  - Faculty-founder and COI groundwork ([PR 156](https://github.com/vertical-cloud-lab/byu-vcl/pull/156), Jul).
  - "The value of open science in the age of AI" ([#380](https://github.com/vertical-cloud-lab/byu-vcl/issues/380#issuecomment-7114876231), 11-23, four public videos). Its investor-view memo concludes "underwrite the business, not the openness label" ([11-25](https://github.com/vertical-cloud-lab/byu-vcl/issues/380#issuecomment-7148684899)).
  - Facility siting for a full-scale lab ([#343](https://github.com/vertical-cloud-lab/byu-vcl/issues/343#issuecomment-7236695997), 11-28: "Consider options between 3000 to 10k square feet. Keep the high ceiling requirements. Also look at things close to or part of UofU").

---

## (b) Active projects/workflows and their automation status

### b1. CubXL (liquid handling, capping, stirring, electrochemistry). Full detail in (f).
- **Closed-loop or remote today:**
  - CubOS protocols are launched from GitHub comments (`@claude` runs on the CubXL Pi). The remote pipette test passed 12/12 on 10-20, and the "Mix" protocol passed 12/12 in 218 s on 10-09 (both per [#312](https://github.com/vertical-cloud-lab/byu-vcl/issues/312#issuecomment-6534736887), 10-30).
  - Electromagnetic decap/recap with an IR capture check, a P20 GEN2 pipette with tip pickup and eject, and two head cameras ([#307](https://github.com/vertical-cloud-lab/byu-vcl/issues/307#issuecomment-6461777920), 10-28).
  - A stir module is integrated into a protocol, and as of 11-24 "The under-the-deck module generally works a lot better!" ([PR 348](https://github.com/vertical-cloud-lab/byu-vcl/pull/348#issuecomment-7147364427)).
- **Manual today:**
  - Loading vials and tips, placing holders, re-calibrating, swapping resistors for potentiostat checks, and power-cycling the Pi.
  - The potentiostat is only validated on dummy resistors and runs over Remote Desktop, not CubOS ([#307](https://github.com/vertical-cloud-lab/byu-vcl/issues/307#issuecomment-6461777920)).
- **Objects and tolerances relevant to an arm:**
  - Glass 20 mL VOA vials, about 20 g empty and 45 g full, with PANDA magnetic press-fit caps. Never grip by the cap: it is designed to pull off.
  - The PandaDeck is 480 × 490 mm with 18 × 10 slots at 45 × 25 mm pitch.
  - The 9-vial holder has 33 mm vial pitch and is located by two pill keys 225 mm apart.
  - The capper and pipette reach 334 mm in X but only 221 mm in Y.
  - All from [#266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266#issuecomment-6038926935), 10-07. Deck-key fit was re-tuned on 11-20 to 11-23: 0.7 mm clearance "still wobbles", and 0.1 mm (a 10.4 mm pill in a 10.5 mm slot) is the best fit ([#354](https://github.com/vertical-cloud-lab/byu-vcl/issues/354#issuecomment-7048533636), [11-20](https://github.com/vertical-cloud-lab/byu-vcl/issues/354#issuecomment-7050646561)).

### b2. OT-2 (liquid handling; BaSO4 precipitation; wireless colour sensor)
- **State on 11-17** ([#349](https://github.com/vertical-cloud-lab/byu-vcl/issues/349#issuecomment-6935312729)):
  - Reached through the CubXL Pi's USB (`ot2-usb` profile).
  - The P300 GEN2 on the left mount has "no pipette offset and no tip length saved".
  - The deck calibration dates from 01-27, before a September move.
  - The heater-shaker is in the robot (placed 10-13, [#81](https://github.com/vertical-cloud-lab/byu-vcl/issues/81#issuecomment-6157219356)).
- **Camera calibration attempt failed.** Claude tried calibrating by the robot's own 1080p camera and stalled the Z motor. Then the CubXL Pi dropped, leaving "The bare nozzle … parked 40 mm above empty slot 8" ([#349](https://github.com/vertical-cloud-lab/byu-vcl/issues/349#issuecomment-6936317028)).
- **No overhead camera.** "Until then the OT-2 has no network link and no overhead camera" (CLAUDE.md, after the lid-camera Pi went to a University of Utah lab on 11-10). The network link has since been restored through the CubXL Pi.
- **Colour sensing is human-in-the-loop.** The P300 picks up a sensor enclosure from a charging base. A person nudges positions in mm through comments ([#197](https://github.com/vertical-cloud-lab/byu-vcl/issues/197), Sep–Oct, closed 10-15). Readings were unreliable, e.g. "it is only reading yellow".
- **No current project.** "with the ot-2 not currently having a project, it needs new direction" ([#322](https://github.com/vertical-cloud-lab/byu-vcl/issues/322#issuecomment-6832033627), 11-12).

### b3. 3D printers: H2D "Théoden", A1 minis "Thumbelina" and "Tinkerbell"
- **Sending is agent-driven, with human approval.** `@claude-print` runs need approval from the `bambu-print-approvers` team. Each run slices, reads nozzle diameters, posts a fresh camera frame of the plate, waits 90 s for objections, then sends (CLAUDE.md, "Printing…"; plate rule changed 10-23).
- **People remove prints and clear the plate:**
  - 11-19, [#354](https://github.com/vertical-cloud-lab/byu-vcl/issues/354#issuecomment-7018413387): "the last job's part was still on the plate, so I held". sgbaird later replied that a lab member had cleared it ([comment](https://github.com/vertical-cloud-lab/byu-vcl/issues/354#issuecomment-7018891403)).
  - 11-20: "Someone at the printer took them off the plate right after it finished" ([#354](https://github.com/vertical-cloud-lab/byu-vcl/issues/354#issuecomment-7049228057)).
  - 11-23: "They're still on the plate unless someone has taken them off" ([#354](https://github.com/vertical-cloud-lab/byu-vcl/issues/354#issuecomment-7117502966)).
  - A failed print, stopped at layer 4, needed "a person at the H2D: Clear the plate" ([#336](https://github.com/vertical-cloud-lab/byu-vcl/issues/336#issuecomment-6754079900), 11-09).
- **Other printer issues:**
  - Tinkerbell's vibration made it "spin in a circle" on a polished wood countertop; a laminate counter helped ([#345](https://github.com/vertical-cloud-lab/byu-vcl/issues/345#issuecomment-6858812043), 11-13).
  - A dedicated printer for programmatic access was proposed in July ([#170](https://github.com/vertical-cloud-lab/byu-vcl/issues/170)).
  - Every approval request emails all 20 approvers ([#299](https://github.com/vertical-cloud-lab/byu-vcl/issues/299)).
  - Setting up Studio on a fresh runner costs about 10 minutes ([#314](https://github.com/vertical-cloud-lab/byu-vcl/issues/314)).
- **Arm hook:** the toy drive's Rexagons, with the draft robot-arms prompt in [PR 402](https://github.com/vertical-cloud-lab/byu-vcl/pull/402#issuecomment-7201185885), 11-26. The draft says to read the printer over LAN first ("gcode_state FINISH, no HMS alerts, bed cooled"). It compares lifting the magnetic plate off and flexing it against pushing the print off. It finishes "each cycle with a camera frame showing the plate clear". It also notes robot-arms#86's stuck job that "held the bed at 65 °C for days".

### b4. Alloy line (now in DAL; listed here because the twin and the design live here)
- **Atomizer (AMAZEMET rePowder): manual.** 630 bronze runs gave "91% yield in our first run and ~75% yield in our most recent run" ([#322](https://github.com/vertical-cloud-lab/byu-vcl/issues/322#issuecomment-6831663483), 11-12).
- **Throughput limit is staffing.** "The crucible's staffing sets it, not a machine": about 0.91 alloys a day ([PR 332](https://github.com/vertical-cloud-lab/byu-vcl/pull/332), 11-08).
- **Turnaround automation is designed and animated only.** Plate swap, crucible change and BN recoat, explosion-proof vacuuming, container removal and the latch, done by two MiR250 + UR10e units ([PR 353](https://github.com/vertical-cloud-lab/byu-vcl/pull/353), merged 11-20). The arms' step times are "estimates, not measurements". sgbaird asked whether the arm needs "a whole sleeve that the arm fits into, sorry [sic] of like a shoulder length glove" against powder ([comment](https://github.com/vertical-cloud-lab/byu-vcl/pull/353#issuecomment-7018521266)).
- **SEM/EDS sample prep: manual.** Sawing, bakelite mounting, grinding at 320–1200 grit, 1 µm alumina then 0.1 µm diamond. sgbaird: "Since we're a ways out from having this aspect autonomous, robotics-wise, probably fine to assume use of the mill" ([#110](https://github.com/vertical-cloud-lab/byu-vcl/issues/110#issuecomment-5841479470), 09-26).
- **Charge cups and plugs** are machined and pressed. One CubXL concept fills 50 Al charge cups from clip-in auger cartridges; it is a concept only ([PR 297](https://github.com/vertical-cloud-lab/byu-vcl/pull/297)).
- **Handling demand at 10 a day** ([PR 332](https://github.com/vertical-cloud-lab/byu-vcl/pull/332)):
  - "an alloy takes 13.3 unit-hours, so ten a day needs 7 units" if mobile arms do everything.
  - "Fixed cobots in five floor cells" (charge, powder, print, prep, tensile) appear in its 10-a-day plan, and "Moving attended work off the trays adds 52 %" ([comment](https://github.com/vertical-cloud-lab/byu-vcl/pull/332#issuecomment-6751696986)).
  - Consumables per day: "67 charge cups … 76 sieved jars … 12 build plates … 21 mounts and 41 tensile specimens".

### b5. Powder doser (its own repo, run from here and DAL)
- Multi-doser mockups "for the U, end of semester deadline" (swcharles, [#322](https://github.com/vertical-cloud-lab/byu-vcl/issues/322#issuecomment-6831830271), 11-12).
- "PiPER swapping the doser's auger" (robot-arms#44) was "Designed over six rounds. I found no print in the thread" ([#350](https://github.com/vertical-cloud-lab/byu-vcl/issues/350#issuecomment-6958212534), 11-17).
- The vial-orientation catch at the multi-doser: the vial "stands upright, mouth up, in a closed 18 mm cup" ([#303](https://github.com/vertical-cloud-lab/byu-vcl/issues/303#issuecomment-6610862903), 11-03).

### b6. The vertical-lab design and the digital twin (where arms are assumed)
- **[PR 318](https://github.com/vertical-cloud-lab/byu-vcl/pull/318)** (rounds 3–16, 102 comments, open):
  - Two 30 ft (9.15 m) Kardex Shuttle XP 500s with 2450 × 864 mm trays. The powered trays carry a UPS and Stäubli CombiTac couplings (mains, Ethernet, air, N₂, chilled water). The body gives both 15 and 19 trays.
  - Two UR12e on MiR250s, each "with a 131 kg ballast plate", a Class D extinguisher and three cameras.
  - Long-form video, round 16: https://www.youtube.com/watch?v=YWbplBXPC84
- **The digital twin of the manufacturing network:** rounds 1–2 [PR 393](https://github.com/vertical-cloud-lab/byu-vcl/pull/393), round 3 [PR 394](https://github.com/vertical-cloud-lab/byu-vcl/pull/394), round 4 [PR 397](https://github.com/vertical-cloud-lab/byu-vcl/pull/397), round 3b [PR 400](https://github.com/vertical-cloud-lab/byu-vcl/pull/400), round 5 [PR 405](https://github.com/vertical-cloud-lab/byu-vcl/pull/405), round 6 [PR 427](https://github.com/vertical-cloud-lab/byu-vcl/pull/427). All dated 11-24 to 11-28.
  - It runs the Al (FLAIME) and Cu (ONR) campaigns with BOFN/pKGFN.
  - Round 5 adds "Decision windows for people" and a 24/7 automated atomizer at about 2.2 h per composition.
  - Round 6 needs "About 813-1,157 runner-hours" of compute slices.
- **[#407](https://github.com/vertical-cloud-lab/byu-vcl/issues/407#issuecomment-7212034341)** (11-27, answered in [PR 410](https://github.com/vertical-cloud-lab/byu-vcl/pull/410)):
  - "Transport doesn't bind … the robots are 1–2 % busy."
  - "What binds is money, the atomizer, DED, the 30-day immersion and decision time … about 250 results a run wait a median of 77 h for a person."
  - "two mobile manipulators on benches serve every request in 2.1 h"; the VLM "turns away 6 % and takes 7.6 h".
  - "Measurements … would replace the biggest stand-ins: a timed dock-and-load".

**Summary table: objects, instruments, current handling and arm relevance**

| Object or task | Instrument | Known specs / tolerances | Who does it now | Source |
|---|---|---|---|---|
| 20 mL glass vials, 9-vial holder (8+1 carrier proposed) | CubXL | 20–45 g per vial; keys 0.1–0.2 mm clearance; PiPER error ±0.64 mm typical / ±1.15 mm worst; dock lead-in 3 mm × 45° catches ±3 mm | person | [#266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266#issuecomment-6038926935), [#354](https://github.com/vertical-cloud-lab/byu-vcl/issues/354#issuecomment-7050646561) |
| Tip racks, pipette tips | CubXL, OT-2 | OT-2 tip pitch 9 mm; the P300 offset is unsaved | person | [#349](https://github.com/vertical-cloud-lab/byu-vcl/issues/349#issuecomment-6935312729) |
| 96-well plates, heater-shaker | OT-2 | the well plate is to be imaged "as high-res as possible" | person | [PR 234](https://github.com/vertical-cloud-lab/byu-vcl/pull/234#issuecomment-6326481859) |
| Finished prints / build plates | H2D, A1 mini ×2 | LAN state (FINISH, HMS, bed temperature) readable; a clear-plate frame is required before each send | person | CLAUDE.md, [PR 402](https://github.com/vertical-cloud-lab/byu-vcl/pull/402#issuecomment-7201185885) |
| Atomizer plate, crucible, container | rePowder (DAL) | designed for MiR250+UR10e; step times are estimates | person | [PR 353](https://github.com/vertical-cloud-lab/byu-vcl/pull/353) |
| SEM stubs, polishing pucks | polisher, saw (shared PSC lab) | 1 µm alumina then 0.1 µm diamond | person | [#110](https://github.com/vertical-cloud-lab/byu-vcl/issues/110#issuecomment-5920913739) |
| Tensile bars (three build orientations), EDM | design only | the gripper may need "its own tool/end effector" | — | [PR 318](https://github.com/vertical-cloud-lab/byu-vcl/pull/318#issuecomment-6867635611), [PR 328](https://github.com/vertical-cloud-lab/byu-vcl/pull/328) |

---

## (c) Deliverables and deadlines

| Date | Item | Status / relevance | Source |
|---|---|---|---|
| 2026-10-28 (SPO submission date) | **ONR YIP**, copper alloys for blown-powder DED (Cu + 8 elements; 1 h corrosion screen plus 30-day immersion) | "before SPO submits the ONR proposal on Oct 28"; later threads call it "the ONR YIP proposal". Its Equipment attachment uses a CubXL schematic. The CubXL Cu corrosion screen (DAL PR 264, "Proposed; parts on order") is Fig. 6. | [#307](https://github.com/vertical-cloud-lab/byu-vcl/issues/307), [PR 308](https://github.com/vertical-cloud-lab/byu-vcl/pull/308), [PR 291](https://github.com/vertical-cloud-lab/byu-vcl/pull/291#issuecomment-6379396044), [#350](https://github.com/vertical-cloud-lab/byu-vcl/issues/350#issuecomment-6958212534) |
| submitted earlier; next round FY27 | **FLAIME**, DOE Genesis Mission DE-FOA-0003612 Topic 3-B (Al + 15 elements, LPBF) | BYU not on the 07-22 or 10-08 award lists; "A second round is planned but not yet posted". Drafts are in DAL `genesis-mission-proposal/`. | [#324](https://github.com/vertical-cloud-lab/byu-vcl/issues/324#issuecomment-6641925527) (11-04) |
| LOI 11-09; DOE reply by 11-23; **full application 2027-01-12** | **Genesis Mission Graduate Fellowship Pilot** (DE-FOA-0003673; universities apply; 4–8 awards of $12–25M) | BYU limited submission (one lead). Qualifying topics include **11-A Advanced Robotics for Dynamic Laboratory Environments**, 11-C, 12-B and 1-B. Whether BYU sent an LOI is not recorded in the repo. | [#324](https://github.com/vertical-cloud-lab/byu-vcl/issues/324#issuecomment-6641925527) |
| submitted 2026-11-06 | **Anthropic AI for Science** credits (up to $50k), "generative CAD and systems design for robotic workflows" | 6-month plan with an **arm cell in months 2–4** and fixtures in months 1–2 (cup station, press nest, cup carrier, SEM stub holder) | [#325](https://github.com/vertical-cloud-lab/byu-vcl/issues/325#issuecomment-6666720744) |
| undated | NSF EAGER concept, reframed as an FDM print-farm integration testbed (50× A1 mini + UR5e) | in DAL; pointer only | [DAL #9](https://github.com/vertical-cloud-lab/digital-alloy-lab/issues/9), [DAL PR 10](https://github.com/vertical-cloud-lab/digital-alloy-lab/pull/10); listed among "The proposals and plans (4)" in [PR 385](https://github.com/vertical-cloud-lab/byu-vcl/pull/385) |
| on hold | BYU IDR internal grant (spectroscopy path with a collaborator) | ranked third behind corrosion and dosing | [#298](https://github.com/vertical-cloud-lab/byu-vcl/issues/298#issuecomment-6352253304) (10-22) |
| "almost ready" (11-12) | MSA Strategic Initiatives proposal (ronnie-guymon) | EDS standards work | [#322](https://github.com/vertical-cloud-lab/byu-vcl/issues/322#issuecomment-6832034472) |
| 2026-12-10 first delivery; **2026-12-18 last day** | ME Christmas toy drive (3D-printed toys; possible extra credit in sgbaird's machine design class) | 13 toys sliced for the A1 mini; printer-use proposal; Rexagons with arm plate-clearing idea (their license blocks giving them away) | [#399](https://github.com/vertical-cloud-lab/byu-vcl/issues/399), [PR 402](https://github.com/vertical-cloud-lab/byu-vcl/pull/402) |
| ~2026-12-21 | Bambu S1 3D scanner arrives (pre-order, $1,699; approved 11-28, order "on Monday") | needs a Windows PC with an RTX 2060 or better; could scan lab objects for grasp and twin models | [#285](https://github.com/vertical-cloud-lab/byu-vcl/issues/285#issuecomment-7201652805), [approval](https://github.com/vertical-cloud-lab/byu-vcl/issues/285#issuecomment-7237151711) |
| end of semester (Dec) | Multi-doser mockups "for the U" | powder-doser team | [#322](https://github.com/vertical-cloud-lab/byu-vcl/issues/322#issuecomment-6831830271) |
| 2027-01-15 (realistic) | "Democratizing SDL" Perspective resubmission (Digital Discovery, DD-PER-12-2024-000410) | blocked on co-author sign-offs (28 authors), the P3 repo and a clean Figure 8 | [PR 193](https://github.com/vertical-cloud-lab/byu-vcl/pull/193#issuecomment-7226069966) (11-27) |
| open | BO Hackathon manuscript revision (Digital Discovery DD-ART-06-2026-000353) | "not submitted yet; the upload set is ready" | [#185](https://github.com/vertical-cloud-lab/byu-vcl/issues/185#issuecomment-7226074182) (11-27) |
| G1 10-23; G3 **01-29**; G5 **02-26**; G6 03-05; meeting in March 2027 | **TMS 2027**: 16 lab abstracts, 13 student talks/posters, incl. the CubXL system (benwhitney5463) and the camera poster | paper-kit gates; the CubXL team wants a manuscript with Ursa "ready by then" | [#273](https://github.com/vertical-cloud-lab/byu-vcl/issues/273), [#133](https://github.com/vertical-cloud-lab/byu-vcl/issues/133#issuecomment-6425470229) (10-26), [#159](https://github.com/vertical-cloud-lab/byu-vcl/issues/159#issuecomment-5081351038) |
| invited, date not in repo | MRS MT03 invited talk "Agentic Materials Research in the Era of AI" | abstract drafted 07-09 | [#158](https://github.com/vertical-cloud-lab/byu-vcl/issues/158) |
| past | Lab-o-ween demo of the CubXL and OT-2 to visitors (10-30); CNMS 2026 talk (Aug); ME faculty meeting talk (09-15); research lunch-and-learn lightning talk with a showreel incl. the PiPER wrist camera mount and auger swap (11-17) | evidence of outreach use | [#312](https://github.com/vertical-cloud-lab/byu-vcl/issues/312#issuecomment-6534736887), [#175](https://github.com/vertical-cloud-lab/byu-vcl/issues/175), [#216](https://github.com/vertical-cloud-lab/byu-vcl/issues/216), [#350](https://github.com/vertical-cloud-lab/byu-vcl/issues/350#issuecomment-6958212534) |
| being arranged | Texas Instruments Lehi fab tour (through BYU recruiting) | — | [#319](https://github.com/vertical-cloud-lab/byu-vcl/issues/319#issuecomment-6692233505) (11-06) |

**Courses and education:**
- sgbaird teaches a machine design class ([#399](https://github.com/vertical-cloud-lab/byu-vcl/issues/399)).
- The AC microcourse templates were inventoried after GitHub Classroom shut down on 2026-08-28. Their "hardware modules still need hardware" ([#225](https://github.com/vertical-cloud-lab/byu-vcl/issues/225#issuecomment-5736707969), 09-18).
- Weekly lab meetings follow a set format: vision talk, 60 s updates per project, and a 15 min deep dive ([#322](https://github.com/vertical-cloud-lab/byu-vcl/issues/322)).

---

## (d) Recent ideas (Sep–Nov 2026) relevant to arms, vision, agents and cloud operation

**Arms and manipulation**
- **CubXL vial handling with the PiPER** (chris-policky, [#266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266#issuecomment-6038577665), 10-07). Goal: "Pick up and replace single vials; Move single vials to and from the CubXL; Move a carrier of 8–9 vials". The recommendation is "C + B, a fixed dock with an 8 + 1 carrier and the CubXL side-on to the arm" ([analysis](https://github.com/vertical-cloud-lab/byu-vcl/issues/266#issuecomment-6038926935)). Key findings:
  - "The PiPER can't grip straight down at deck height. J5 stops at ±70°", so it has to come in at about 45°.
  - A full carrier is 0.53–0.66 kg, which is 35–44 % of the 1.5 kg payload.
  - Gripping reach band: 0.23–0.65 m.
  - Test plan: "Run 200 carrier swaps … and 200 single-vial moves … Pass: no misses in 200 at the nominal position, and at least ±2 mm of capture". Then 50 dry cycles on the real CubXL and 20 with water.
  - Handshake: "Stub the handshake as MQTT messages … `command/cubxl/<id>/park` and `status/cubxl/<id>/dock`". If the GRBL controller has a safety-door input, a break-beam across the dock would make the interlock physical.
  - Follow-up ask: printable dock, carrier, finger inserts, and ±1–4 mm / ±2–4° offset plates for the capture-envelope test ([PR 272](https://github.com/vertical-cloud-lab/byu-vcl/pull/272#issuecomment-6103301940), 10-10).
- **Arm plate removal on the A1 mini** for the toy drive ([PR 402](https://github.com/vertical-cloud-lab/byu-vcl/pull/402#issuecomment-7201176343), 11-26).
- **The vision swaps the PiPER for URs on MiR250s.** "The mobile base for the piper looks weird. Put a UR10e or a UR7e in there instead … The robot arm should actually do something.. not just move side to side. Demonstrate an actual workflow" ([#303](https://github.com/vertical-cloud-lab/byu-vcl/issues/303#issuecomment-6450405539), 10-27).
- **Collisions in the animations.** sgbaird spotted "Insertion / removal of the tensile bars … another collision. Not sure if the gripper has enough clearance. Maybe OK if angled, otherwise needs it's own tool/end effector" ([PR 318](https://github.com/vertical-cloud-lab/byu-vcl/pull/318#issuecomment-6867635611), 11-13).
- **Floor cleaning for spilled powder.** "no robot is rated for it, so a third MiR250 + UR12e" with an explosion-proof vacuum ([PR 369](https://github.com/vertical-cloud-lab/byu-vcl/pull/369), merged 11-23).
- **Glovebox arm integration** research moved to robot-arms#11 ([PR 217](https://github.com/vertical-cloud-lab/byu-vcl/pull/217#issuecomment-6089437517)).

**Vision, cameras and AprilTags**
- **Three cameras on each mobile manipulator** ([PR 374](https://github.com/vertical-cloud-lab/byu-vcl/pull/374), merged 11-23; after robot-arms PR 40):
  - two side posts at 0.88 m and a mast at 1.75 m, each a Camera Module 3 Wide with its own Pi 5;
  - "L + R see AprilTags on the station's face in 3-D the moment the base stops";
  - fixed aims, because "cameras which move are what learned policies cope with worst".
- **Security cameras** with a Pi 5 instead of HQ/Wide modules ([PR 370](https://github.com/vertical-cloud-lab/byu-vcl/pull/370), merged 11-23).
- **"Provenance Eyes" head-worn recorder** (gage-erickson, [#342](https://github.com/vertical-cloud-lab/byu-vcl/issues/342#issuecomment-6836632272), 11-12):
  - Spec: "with the press of a button it records a video and then when ended is uploaded to Youtube … deposit the transcript data, analysis … on GitHub automatically".
  - Design: Pi Zero 2 W, Camera Module 3 Wide and I2S mics on ratchet headgear, BOM about $177. Full-face respirator and lab-coat fit were checked after sgbaird's [note](https://github.com/vertical-cloud-lab/byu-vcl/issues/342#issuecomment-6842439882).
  - Head-camera jitter handling: keep the raw clip as the record and publish a steadied copy ([#290](https://github.com/vertical-cloud-lab/byu-vcl/issues/290#issuecomment-7237046924), 11-28).
- **OT-2's own camera for calibration.** It gives "1920×1080 pictures"; "One camera can't show whether a tip is touching" ([#349](https://github.com/vertical-cloud-lab/byu-vcl/issues/349#issuecomment-6936317028), 11-17).
- **Bambu S1 scanner** (11-26 to 11-28, [#285](https://github.com/vertical-cloud-lab/byu-vcl/issues/285)).
- **Camera-data rationale** (TMS 2027 camera abstract brief, [#143](https://github.com/vertical-cloud-lab/byu-vcl/issues/143), 07-01): "potential for roboticists to use this as training data for models" and "non-invasively estimate utilization of equipment".
- **Privacy by design.** One camera per module so "only forearms or hands would be captured" ([#173](https://github.com/vertical-cloud-lab/byu-vcl/issues/173#issuecomment-5185751204), 08-04).

**Simulation, twins and agents**
- **Digital twin rounds 1–6** (11-24 to 11-28, see b6). "Is the vertical lab worth it?" ([#407](https://github.com/vertical-cloud-lab/byu-vcl/issues/407)).
- **Bottleneck ladder to 10 alloys a day,** including fixed cobots in floor cells ([PR 332](https://github.com/vertical-cloud-lab/byu-vcl/pull/332), 11-08).
- **Argon Robotics' Alloy engine** (MuJoCo plus MPM powder and SPH liquids) was tried on VLM tray accelerations and powder dosing, CPU-only ([#351](https://github.com/vertical-cloud-lab/byu-vcl/issues/351#issuecomment-6956074499), 11-17). sgbaird's reaction: "Interesting".
- **Frontier3D lessons:** learn "how Frontier3D *evaluates* 3D work" for generative CAD. About 160 past agent-CAD attempts across 11 repos were inventoried ([#330](https://github.com/vertical-cloud-lab/byu-vcl/issues/330#issuecomment-6701795386), 11-07).
- **Claude Science vs Actions.** sgbaird found "adding the reviewer step and splitting into skills" reasonable, possibly with Codex as reviewer ([#326](https://github.com/vertical-cloud-lab/byu-vcl/issues/326#issuecomment-6696276351), 11-06). DOE's Genesis Agent Skills (SKILL.md, BSD-2) were flagged ([#324](https://github.com/vertical-cloud-lab/byu-vcl/issues/324#issuecomment-6641925527)).
- **Orchestration changes:**
  - `@claude-super` (11-20; [PR 357](https://github.com/vertical-cloud-lab/byu-vcl/pull/357), [PR 360](https://github.com/vertical-cloud-lab/byu-vcl/pull/360)) hands tasks to up to 10 child threads after sgbaird's approval.
  - A 13-seat Claude pool (11-26, [PR 391](https://github.com/vertical-cloud-lab/byu-vcl/pull/391)).
  - Runs can open new PRs (11-24, [PR 381](https://github.com/vertical-cloud-lab/byu-vcl/pull/381)).
  - A **weekly automated lab-safety review** ([PR 375](https://github.com/vertical-cloud-lab/byu-vcl/pull/375), open since 11-20).

**Cloud operation**
- **Hugging Face Spaces alternatives and credit-based apps.** HF's billing change "wip[ed] out free-tier spaces running on CPU" ([#191](https://github.com/vertical-cloud-lab/byu-vcl/issues/191), 08-26).
- **External-user queueing modelled.** At 0/30/60 % outside load, a VLM loses to two mobile manipulators ([#407](https://github.com/vertical-cloud-lab/byu-vcl/issues/407#issuecomment-7212034341)).
- **Facility for the scaled lab** ([#343](https://github.com/vertical-cloud-lab/byu-vcl/issues/343), [PR 344](https://github.com/vertical-cloud-lab/byu-vcl/pull/344)). A commercial-real-estate contact told gage-erickson "36' ceiling height is usually the max" ([comment](https://github.com/vertical-cloud-lab/byu-vcl/issues/343#issuecomment-6837686929), 11-12).

---

## (e) The cloud-lab infrastructure as it stands, and what an arm would need to plug in

**What exists and works (late Nov 2026):**
- **Control plane: GitHub plus Claude Code in Actions.** Anyone with write access comments `@claude` on an issue or PR. The run joins the tailnet and SSHes to a Pi. Examples:
  - benwhitney5463 runs CubXL protocols this way ([PR 348](https://github.com/vertical-cloud-lab/byu-vcl/pull/348#issuecomment-6962531223));
  - timothy-commins drove the OT-2 and replied "ready" / "down 1mm" to a calibration loop ([#349](https://github.com/vertical-cloud-lab/byu-vcl/issues/349)).
  - Results come back as committed camera frames, logs and YouTube clips.
- **Gated workflows**, each a GitHub environment with an approval step (CLAUDE.md):
  - `@claude-print`, approved by the `bambu-print-approvers` team (20 members);
  - `@claude-youtube` and `@claude-onshape-admin`, approved by sgbaird only;
  - `@claude-super`, approved by sgbaird, which dispatches up to 10 child runs.
- **Tailscale** (CLAUDE.md; policy in vertical-cloud-lab/tailscale-policy, edited by PR):
  - CI joins as an ephemeral node with tags (`tag:stream-cam-test`, `tag:rpi-5-des4`).
  - Devices reach only their own tag group, and only on `tcp:22`. "a service that starts listening on a Pi is unreachable from other devices, CI runners included, until a port is added to that tag's grant". The advice is to bind new services to `127.0.0.1`.
  - The CubXL Pi also carries `tag:ezstat-pc-router`, as a subnet router to the potentiostat PC.
- **Pis in use:**
  - **The CubXL Pi 5:** CubOS (loopback `:8742`), `deckcam.service`, the OT-2 USB link (since 11-17), the RDP relay to the Win7 EZstat PC, and the residential-IP proxy for agent web research. That last use shows up in [#324](https://github.com/vertical-cloud-lab/byu-vcl/issues/324#issuecomment-6641925527), [#290](https://github.com/vertical-cloud-lab/byu-vcl/issues/290), [#407](https://github.com/vertical-cloud-lab/byu-vcl/issues/407#issuecomment-7212034341) and [#285](https://github.com/vertical-cloud-lab/byu-vcl/issues/285#issuecomment-7237169575).
  - **The atomizer-room Zero 2 W** now belongs to DAL, and this repo's CI can't reach it ([PR 300](https://github.com/vertical-cloud-lab/byu-vcl/pull/300)).
  - **The OT-2 lid camera Pi is gone** (11-10, CLAUDE.md; [PR 340](https://github.com/vertical-cloud-lab/byu-vcl/pull/340)).
- **Stream cameras** ([`docs/stream-cams.md`](https://github.com/vertical-cloud-lab/byu-vcl/blob/main/docs/stream-cams.md)):
  - The AC picam client pipes `rpicam-vid` to `ffmpeg` and pushes RTMP to the *BYU VCL Hardware Streams* YouTube channel. A streamingLambda files each broadcast into a per-workflow playlist.
  - Each camera has a watchdog timer and reboots three times a day. The burned-in timestamp overlay is "the clock", since the archive timeline drifts.
  - The atomizer room streams at 144p, 2 fps, pixelated to 128×72 blocks for privacy.
- **YouTube uploads:** an upload-only token for the *BYU Vertical Cloud Lab* channel (`youtube/yt_service.py`). Uploads have defaulted to public since 11-19 ([PR 355](https://github.com/vertical-cloud-lab/byu-vcl/pull/355)), and each description links the triggering comment ([PR 356](https://github.com/vertical-cloud-lab/byu-vcl/pull/356)).
- **Data and messaging** (CLAUDE.md):
  - HiveMQ Cloud MQTT on the free tier, with no per-topic ACLs ("topic isolation is a convention"). Per-client credentials: `vcl-agent`, `picow-color-sensor`, `hf-space`, `ot2-robot`.
  - Topic scheme (matching AC's OT-2-LCM): `command/<device>/<id>/…` for commands (e.g. `command/ot2/<serial>/pipette`), `status/<device>/<id>/…` for status, and workflow-named data topics (e.g. `color-mixing/picow/<id>/as7341`).
  - MongoDB Atlas M0 (`digital-wetlab` DB: `sensor-data`, `ot2-runs`).
- **Hugging Face Spaces:** `byu-vcl/OT-2-LCM` and `byu-vcl/light-mixing`, both private, cpu-basic duplicates of the AC demos. `YT_API_KEY` is "Not yet provisioned" (CLAUDE.md). The OT-2 has had no camera since 11-10, and the Pico W colour sensor lived on the departed Pi. **So the public, queue-from-a-browser cloud demo isn't running at BYU now** (my inference from those facts).
- **Printers:** LAN mode. Status and camera are read from a Pi on the lab LAN. Sends go through Bambu Studio on the runner, logged in with an authenticator code. This exists because cloud-bound firmware rejects unsigned LAN start commands (HMS `0500-0500-0001-0007`).
- **Other services:** Edison Scientific literature and analysis tasks; Onshape (API quota exhausted since 10-29, so browser export through a Pi tunnel); Zenodo.

**What an arm would need to plug in, based on how other devices were added:**
1. **A host on the tailnet with its own tag,** added in this order: a tailscale-policy PR, a console tag, the OAuth client or trust credential, then `tags:` in `claude.yml`. An OAuth client "must request every one of them" (all its tags); asking for a subset fails. Use SSH only and bind controllers to loopback (CLAUDE.md "Tailscale"). Don't reuse the CubXL Pi; see takeaway 6.
2. **A runbook section in CLAUDE.md:**
   - device paths by `/dev/serial/by-id`, never `ttyACM*` (the CubXL Arduino vs Pico trap);
   - which calls are read-only and which move hardware (as done for the OT-2's `/health` vs `/maintenance_runs`);
   - "Treat the Pi as a live production device".
3. **An approval gate for motion,** following the `@claude-print` pattern: start from a fresh camera frame, wait a window for objections, and record the go. The plate-clear frame rule makes a printer-tending arm a natural fit.
4. **Interlocks with instruments.** For the CubXL: CubOS parks the gantry, sends "dock free", the arm works, then "dock released". Use MQTT topics in the lab scheme, and optionally a break-beam wired to GRBL's safety-door input ([#266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266#issuecomment-6038926935)). For printers: read the LAN state (`gcode_state`, HMS, bed temperature) before and after each cycle ([PR 402](https://github.com/vertical-cloud-lab/byu-vcl/pull/402#issuecomment-7201185885)).
5. **Cross-repo dispatch.** robot-arms' `claude.yml` "skips events sent by bots and has no `allowed_bots: vcl-bot`", so byu-vcl's `@claude-super` can't hand work to robot-arms until a human edits it ([PR 402](https://github.com/vertical-cloud-lab/byu-vcl/pull/402#issuecomment-7201185885), 11-26).
6. **Video and provenance.** Fixed-aim cameras, timestamp overlays, framing that shows hands only, and uploads to the lab channel, as the lab does for every procedure. sgbaird: "we'll want operator video or (temporary) hardware livestreams … for the full polishing process … similar to other procedures in the lab" ([#110](https://github.com/vertical-cloud-lab/byu-vcl/issues/110#issuecomment-6032143750), 10-07).

---

## (f) What the CubXL is, and every mention of it

**What it is**
- **Origin:** the CubXL (CubXL+) from Ursa Laboratories. Its developer is alexc2684, an active external collaborator in [#133](https://github.com/vertical-cloud-lab/byu-vcl/issues/133).
  - It is part of moving the BU-KABlab PANDA system onto CubOS. Its open-source software is CubOS (Python; YAML gantry, deck and protocol files; a FastAPI server and operator UI), and its hardware repo is Cubware.
  - The package arrived **2026-06-18**, while CB 154 was being renovated ([#133 body](https://github.com/vertical-cloud-lab/byu-vcl/issues/133)). Ursa collects feedback "as part of our grant" ([06-29](https://github.com/vertical-cloud-lab/byu-vcl/issues/133#issuecomment-4835482810)).
- **Base:** a Genmitsu (SainSmart) PROVerXL 4030 V2 CNC gantry with a GRBL controller, 641 × 755.5 × 580 mm overall ([#266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266#issuecomment-6038926935)), and a polycarbonate PandaDeck. It moved from the SMASH Lab to CB 154 on 09-22 ([#133](https://github.com/vertical-cloud-lab/byu-vcl/issues/133#issuecomment-5769300117)).
- **Implemented and tested** (evidence table in [#307](https://github.com/vertical-cloud-lab/byu-vcl/issues/307#issuecomment-6461777920), 10-28):
  - magnetic decapping and recapping with an IR capture check (27/27 steps on 08-03);
  - an Opentrons P20 GEN2 pipette, first liquid transfer 09-30. It is driven by an Arduino Uno (PAW/"Pawduino" firmware) through a Tic T500 or a TMC2209 with a firmware UART bypass ([PR 260](https://github.com/vertical-cloud-lab/byu-vcl/pull/260)). "The volume hasn't been checked on a balance yet";
  - tip pickup and eject; remote CubOS runs since 07-27;
  - two head cameras;
  - a hardware E-stop, which "seemed to work in all 3 instances" (protocol, jog, homing; [#182](https://github.com/vertical-cloud-lab/byu-vcl/issues/182#issuecomment-5432413901), 08-26);
  - a potentiostat beside the deck, on dummy loads only.
  - Since then the magnetic stir module has been integrated: "the stir module works" on 11-05 ([#133](https://github.com/vertical-cloud-lab/byu-vcl/issues/133#issuecomment-6672004682)), and it moved under the deck on 11-24 ([PR 348](https://github.com/vertical-cloud-lab/byu-vcl/pull/348#issuecomment-7147364427)).
- **Planned:** a Cu corrosion cell (DAL PR 180: "Nothing here has been bought, built or run"), an OpenRAMAN dock, a pH meter ([#148](https://github.com/vertical-cloud-lab/byu-vcl/issues/148)), powder-dosing concepts ([PR 274](https://github.com/vertical-cloud-lab/byu-vcl/pull/274), [PR 297](https://github.com/vertical-cloud-lab/byu-vcl/pull/297)), and a P300 next to the P20 ([PR 372](https://github.com/vertical-cloud-lab/byu-vcl/pull/372), 11-20: "keep the P20 and add a P300; not a Flex yet").
- **How it is used:**
  - benwhitney5463 is the lead, with jarrettshupe (potentiostat) and chris-policky (arm handling).
  - Runs start from GitHub comments. Example: "`@claude` run the pipette test again … post pictures from both cameras" ([#169](https://github.com/vertical-cloud-lab/byu-vcl/issues/169#issuecomment-6025504735)).
  - CLAUDE.md describes the CubXL Pi as the access point benwhitney5463 uses by commenting `@claude` on this repo.
- **Role in the strategic design:**
  - It is the copper corrosion station (the ONR YIP Fig. 6 reel).
  - "2 CubXLs (2.2 h)" per alloy are needed for 10 alloys a day ([PR 332](https://github.com/vertical-cloud-lab/byu-vcl/pull/332)).
  - "Three CubXL-s" appear in the vertical-lab visualization ([#303](https://github.com/vertical-cloud-lab/byu-vcl/issues/303#issuecomment-6610848755), 11-03).

**Reliability and fit issues** (an arm campaign will hit these)
- Caps: "the cap falling out a couple times and the aspiration failing" in a demo video ([#200](https://github.com/vertical-cloud-lab/byu-vcl/issues/200#issuecomment-5643671824), 09-12). "the capper couldn't take vial_1's cap off" on 10-09 ([#169](https://github.com/vertical-cloud-lab/byu-vcl/issues/169#issuecomment-6089677393)). The cap-capture pill pins "give no resistance" ([#147](https://github.com/vertical-cloud-lab/byu-vcl/issues/147#issuecomment-5028148800), 07-20).
- Gantry homing and calibration: after UI calibration the home is sometimes recorded "above the safe volume limits" ([#133](https://github.com/vertical-cloud-lab/byu-vcl/issues/133#issuecomment-5960677930), 10-02). Calibration is redone after deck changes.
- Holder fit: "the vial holder is still loose on the deck (it won't exit vertically, but it still wobbles)". "The new vial holder actually holds the vials with less force than the original design" ([#354](https://github.com/vertical-cloud-lab/byu-vcl/issues/354#issuecomment-7048756807), 11-20). sgbaird asked on 11-26 for fit-check videos ([comment](https://github.com/vertical-cloud-lab/byu-vcl/issues/354#issuecomment-7184359687)).
- Electronics: shorts in the stir-module wiring and a paint-clogged tip ([PR 348](https://github.com/vertical-cloud-lab/byu-vcl/pull/348#issuecomment-7000926440), 11-19). The broken electromagnet prong was reprinted ([#354](https://github.com/vertical-cloud-lab/byu-vcl/issues/354), 11-19).
- Vial height is inconsistent: 64.2 mm (printed) vs 83 mm in the CubOS deck YAMLs ([#266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266#issuecomment-6038926935)).

**Chronological ledger of CubXL threads** (I = issue, PR = pull request)
- 06-18 → 11-23, [I 133](https://github.com/vertical-cloud-lab/byu-vcl/issues/133): setup thread, 139 comments; latest is alexc2684 asking about calibration-flow improvements (11-23).
- 06-27, [PR 140](https://github.com/vertical-cloud-lab/byu-vcl/pull/140): gantry-connection troubleshooting. 07-02, [I 149](https://github.com/vertical-cloud-lab/byu-vcl/issues/149) and [PR 152](https://github.com/vertical-cloud-lab/byu-vcl/pull/152): pipette choice.
- 07-02, [I 147](https://github.com/vertical-cloud-lab/byu-vcl/issues/147) and [PR 174](https://github.com/vertical-cloud-lab/byu-vcl/pull/174): electromagnetic capper (built Jul, closed 10-01).
- 07-02, [I 148](https://github.com/vertical-cloud-lab/byu-vcl/issues/148): pH meter (closed 11-04).
- 07-02, [I 150](https://github.com/vertical-cloud-lab/byu-vcl/issues/150), [PR 274](https://github.com/vertical-cloud-lab/byu-vcl/pull/274), [PR 297](https://github.com/vertical-cloud-lab/byu-vcl/pull/297): powder-doser integration concepts (merged 11-06).
- 07-02, [I 151](https://github.com/vertical-cloud-lab/byu-vcl/issues/151): deck modules printed (closed 10-01).
- 07-06, [I 154](https://github.com/vertical-cloud-lab/byu-vcl/issues/154): dedicated computer, which became a Pi 5 (07-31).
- 07-10, [I 159](https://github.com/vertical-cloud-lab/byu-vcl/issues/159) and [PR 160](https://github.com/vertical-cloud-lab/byu-vcl/pull/160): TMS 2027 abstract (submitted 07-26).
- 07-27, [I 165](https://github.com/vertical-cloud-lab/byu-vcl/issues/165) and [PR 171](https://github.com/vertical-cloud-lab/byu-vcl/pull/171): CubOS on the Pi, setup guide and run artifacts.
- 07-29, [I 169](https://github.com/vertical-cloud-lab/byu-vcl/issues/169) and [PR 269](https://github.com/vertical-cloud-lab/byu-vcl/pull/269): P20 integration and dummy pipette (merged 11-09). [PR 228](https://github.com/vertical-cloud-lab/byu-vcl/pull/228): pipette troubleshooting. [PR 260](https://github.com/vertical-cloud-lab/byu-vcl/pull/260): TMC2209 firmware fix.
- 08-18, [I 182](https://github.com/vertical-cloud-lab/byu-vcl/issues/182): E-stop.
- 09-09, [I 200](https://github.com/vertical-cloud-lab/byu-vcl/issues/200): shareable photo and video (`docs/cubxl-media.md` on its branch).
- 09-12: [I 206](https://github.com/vertical-cloud-lab/byu-vcl/issues/206), [I 207](https://github.com/vertical-cloud-lab/byu-vcl/issues/207), [I 211](https://github.com/vertical-cloud-lab/byu-vcl/issues/211), [PR 203](https://github.com/vertical-cloud-lab/byu-vcl/pull/203), [PR 210](https://github.com/vertical-cloud-lab/byu-vcl/pull/210): CI access to the CubXL Pi. [PR 212](https://github.com/vertical-cloud-lab/byu-vcl/pull/212): its serial boards (Arduino Uno `2341:0043`, CH340 `1a86:7523`).
- 09-14, [I 214](https://github.com/vertical-cloud-lab/byu-vcl/issues/214): a CubXL photo in the department handout collage.
- 09-23, [I 231](https://github.com/vertical-cloud-lab/byu-vcl/issues/231), [PR 291](https://github.com/vertical-cloud-lab/byu-vcl/pull/291), [PR 294](https://github.com/vertical-cloud-lab/byu-vcl/pull/294): potentiostat (EZstat Pro on a Win7 PC, RDP through the CubXL Pi; closed and merged 11-04 to 11-06).
- 10-07, [I 266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266) and [PR 272](https://github.com/vertical-cloud-lab/byu-vcl/pull/272): **6-DOF arm vial handling** (open).
- 10-10 / 10-13, [PR 270](https://github.com/vertical-cloud-lab/byu-vcl/pull/270) and [PR 278](https://github.com/vertical-cloud-lab/byu-vcl/pull/278): electrochemistry use cases (moved to DAL 10-22).
- 10-22, [I 298](https://github.com/vertical-cloud-lab/byu-vcl/issues/298): future direction (corrosion > dosing > spectroscopy).
- 10-28, [I 307](https://github.com/vertical-cloud-lab/byu-vcl/issues/307) and [PR 308](https://github.com/vertical-cloud-lab/byu-vcl/pull/308): ONR YIP schematic.
- 10-30, [I 312](https://github.com/vertical-cloud-lab/byu-vcl/issues/312): Lab-o-ween demo readiness.
- 11-16, [PR 348](https://github.com/vertical-cloud-lab/byu-vcl/pull/348): stir module into CubOS and the lab's CubOS fork (vertical-cloud-lab/CubOS). A PAT for opening PRs there "can't reach `@claude` runs" ([#133](https://github.com/vertical-cloud-lab/byu-vcl/issues/133#issuecomment-6758266781), 11-10).
- 11-17, [I 349](https://github.com/vertical-cloud-lab/byu-vcl/issues/349): the CubXL Pi becomes the OT-2's link, then drops offline.
- 11-19, [I 354](https://github.com/vertical-cloud-lab/byu-vcl/issues/354): vial holders, deck keys and electromagnet mount reprints (open).
- 11-20, [I 365](https://github.com/vertical-cloud-lab/byu-vcl/issues/365) and [PR 372](https://github.com/vertical-cloud-lab/byu-vcl/pull/372): pipettes, evaporation and reference electrode, for the vertical-lab design.
- **Also uses the CubXL Pi as a web proxy:** [I 285](https://github.com/vertical-cloud-lab/byu-vcl/issues/285), [I 290](https://github.com/vertical-cloud-lab/byu-vcl/issues/290), [I 319](https://github.com/vertical-cloud-lab/byu-vcl/issues/319), [I 324](https://github.com/vertical-cloud-lab/byu-vcl/issues/324), [I 343](https://github.com/vertical-cloud-lab/byu-vcl/issues/343), [I 380](https://github.com/vertical-cloud-lab/byu-vcl/issues/380), [I 407](https://github.com/vertical-cloud-lab/byu-vcl/issues/407); and as the Onshape browser tunnel (CLAUDE.md).

---

## (g) Constraints

**Safety**
- **Inert-gas booth in 154 CB:** "at most two argon or nitrogen cylinders in the booth, not manifolded …, and no dewar. Under that limit, no oxygen detection is required." This is the College of Engineering industrial hygienist's ruling of 10-08 ([PR 271](https://github.com/vertical-cloud-lab/byu-vcl/pull/271), moved to DAL #190).
- **Metal powder:**
  - Class D extinguishers (Amerex B570, the lab's own unit, $958.01) at every powder station, and one proposed on each mobile base ([PR 379](https://github.com/vertical-cloud-lab/byu-vcl/pull/379), merged 11-23).
  - Anti-static lab coats near the enclosure ([#288](https://github.com/vertical-cloud-lab/byu-vcl/issues/288)).
  - "sometimes we need to use full face respirators" ([#342](https://github.com/vertical-cloud-lab/byu-vcl/issues/342#issuecomment-6842439882), 11-13).
  - An AirGradient alert traced to a new BN coat's first heat ([#305](https://github.com/vertical-cloud-lab/byu-vcl/issues/305), 10-28).
- **Safety process:** a training-video playlist ([#378](https://github.com/vertical-cloud-lab/byu-vcl/issues/378#issuecomment-7053506983), 11-20) and the proposed weekly automated review against the College risk matrix ([PR 375](https://github.com/vertical-cloud-lab/byu-vcl/pull/375)). BYU Engineering safety PDFs and an SOP template are in the repo root on `main`.
- **Rules for agents on hardware** (CLAUDE.md):
  - "Treat the Pi as a live production device. Inspect read-only first."
  - Moving the OT-2 is restricted (`/maintenance_runs` "moves real hardware").
  - Never take a full RDP session on the Win7 PC: it "locks out whoever is at the console, mid-experiment perhaps".
  - Demos are run read-only first ([#312](https://github.com/vertical-cloud-lab/byu-vcl/issues/312)).
  - The OT-2 incident: Claude drove the bare nozzle below its Z limit and stalled the motor three times ([#349](https://github.com/vertical-cloud-lab/byu-vcl/issues/349#issuecomment-6936317028)).
- **Privacy:** cameras framed on hands and forearms; the atomizer room stream pixelated; "Never upload footage of people without their OK" (robot-arms CLAUDE.md, repeated here).

**Budget and procurement**
- Purchases go through ME Orders (meorders.byu.edu) approved by sgbaird. Many examples: [#181](https://github.com/vertical-cloud-lab/byu-vcl/issues/181), [#309](https://github.com/vertical-cloud-lab/byu-vcl/issues/309#issuecomment-7050332591), [PR 323](https://github.com/vertical-cloud-lab/byu-vcl/pull/323).
- "our budget situation changed and we haven't been able to procure a Squidstat yet" ([#133](https://github.com/vertical-cloud-lab/byu-vcl/issues/133#issuecomment-4868764756), 07-02). The lab borrowed a collaborator's EZstat Pro instead ([#231](https://github.com/vertical-cloud-lab/byu-vcl/issues/231)).
- Big-ticket reference numbers:
  - VLM quotes of "$118k (Modula) and $97k (Kardex)" ([#53](https://github.com/vertical-cloud-lab/byu-vcl/issues/53#issuecomment-4179678435), 04-02). Trays "will not retain power while in motion" ([04-02](https://github.com/vertical-cloud-lab/byu-vcl/issues/53#issuecomment-4180394641)).
  - "two Shuttles … about $0.5M, about 3.5 mobile manipulators" ([#407](https://github.com/vertical-cloud-lab/byu-vcl/issues/407#issuecomment-7212034341)).
  - The arm procurement guide's 6-DOF price bands: PiPER "~$2.5K new", UR3e/5e/10e used "$7K–$38K", MiR used "$7.5K–$15K+" ([PR 56](https://github.com/vertical-cloud-lab/byu-vcl/pull/56), Feb; moved to robot-arms#12).
- **Software and service limits:**
  - Onshape API quota exhausted since 10-29.
  - HF free CPU Spaces ended in July ([#191](https://github.com/vertical-cloud-lab/byu-vcl/issues/191)).
  - Claude usage credits ran out mid-run on 11-20 ([PR 318](https://github.com/vertical-cloud-lab/byu-vcl/pull/318#issuecomment-7051716604)). A 5-seat, then 13-seat Claude pool followed on 11-25/26 ([PR 387](https://github.com/vertical-cloud-lab/byu-vcl/pull/387), [PR 391](https://github.com/vertical-cloud-lab/byu-vcl/pull/391)).
- **External users / recharge:** BYU's SEM-lab director said "university wide it is highly discouraged to set up something like this" (cost recovery). Pricing would have to sit above industry, and "external users … should never inhibit" student learning ([#106](https://github.com/vertical-cloud-lab/byu-vcl/issues/106#issuecomment-4909744481), 07-07).

**Space**
- **CB 154** is the VCL lab, renovated 06-18 to 09-22. The CubXL, the OT-2 and the colour-sensor test stand moved in during September ([#33](https://github.com/vertical-cloud-lab/byu-vcl/issues/33)).
- The H2D and its filament storage are in the **SMASH Lab** ([#181](https://github.com/vertical-cloud-lab/byu-vcl/issues/181#issuecomment-6218346529)). Supplies go to CB 152A.
- Polishing uses a shared lab and the PSC's vacuum pump ([#110](https://github.com/vertical-cloud-lab/byu-vcl/issues/110#issuecomment-5483230772)). The fume hood is borrowed in the interim from another lab ([#195](https://github.com/vertical-cloud-lab/byu-vcl/issues/195)).
- Bench issues: the CubXL was moved "closer to the power strip" ([#133](https://github.com/vertical-cloud-lab/byu-vcl/issues/133#issuecomment-5836841107), 09-25), and printers vibrate on some counters ([#345](https://github.com/vertical-cloud-lab/byu-vcl/issues/345#issuecomment-6858812043)).
- Room plans: `cb154.pdf` and `cb154-annotated.pdf` on `main`.

**People and time**
- **Last two weeks (11-14 to 11-28):** 36 issues and 68 PRs were updated. Across all issues plus the ~50 PRs I fetched there were about 306 comments. Humans: sgbaird 107, benwhitney5463 22, timothy-commins 17, ethanw-24 1, gage-erickson 1. Bots: claude 139, vcl-bot 14, github-actions 5.
  - sgbaird's effort is concentrated on the vertical-lab visualization and the digital-twin rounds (PR 318: 22 comments; PRs 393–427), open science (#380) and facility siting (#343).
  - Hands-on hardware work was the CubXL stir module and deck keys (benwhitney5463; PR 348, #354) and OT-2 BaSO4 runs (timothy-commins; #349).
- **The roster changed.** sgbaird noted that seth-leavitt has left the group ([PR 193](https://github.com/vertical-cloud-lab/byu-vcl/pull/193#issuecomment-6101511534), 10-10). Students rotate by semester. The 11-12 lab-meeting posts in #322 show the projects: atomizer, powder doser, OT-2, EDS/polishing, LPBF ("BYU LPBF system up and running, Start printing at U of U soon"), tensegrity and the drop tower ([#322](https://github.com/vertical-cloud-lab/byu-vcl/issues/322)).
- **Human decision latency is a modelled bottleneck:** "about 250 results a run wait a median of 77 h for a person" ([#407](https://github.com/vertical-cloud-lab/byu-vcl/issues/407#issuecomment-7212034341)).
- **Approval friction.** Each `@claude-print` approval emails 20 people ([#299](https://github.com/vertical-cloud-lab/byu-vcl/issues/299)), and Studio setup costs about 10 min a run ([#314](https://github.com/vertical-cloud-lab/byu-vcl/issues/314)).
- **The GitHub token dies at minute 60.** Long hardware sessions need a re-mint (CLAUDE.md).
