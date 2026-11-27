# Database searches: Scopus, Engineering Village (Compendex + Inspec), IEEE Xplore

Drafted in WRTG-Proposal-1 (issue #64) to fill the gap left by the Edison queries, which did
not search any subscription database. Run each through BYU Library (lib.byu.edu → Databases)
so you get BYU's access, then export the results (RIS or CSV, **with abstracts**) into
`Proposal/searches/` and fill in the log at the bottom.

## Why these searches

The nine Edison picks lean on arXiv copies, ICRA/RA-L and *Nature*. The engineering journals
that Compendex and Inspec index well (*Industrial Robot*, *Robotics and Computer-Integrated
Manufacturing*, *Measurement*, *Precision Engineering*, *SLAS Technology*, *JALA*) and the
IEEE CASE conference (automation science, where much lab-automation work appears) are thin in
that set. In priority order:

| # | Search | Edison question | Why it matters |
|---|---|---|---|
| S1 | Measured performance of low-cost arms | Q3 | Only two picks ([5], [6]) carry measured low-cost data |
| S2 | ISO 9283 and repeatability measurement methods | Q2 | Metrology journals are Compendex/Inspec territory |
| S3 | Robot arms in self-driving labs | Q1, Q5 | *SLAS Technology* and *JALA* are indexed there, not on arXiv |
| S4 | The case against low-cost arms | Q4 | Only one counter-argument pick ([7]) |
| S5 | Lab tasks with fiducial or wrist-camera localization | Q5 | No pick covers it yet |
| S6 | Reporting success rates with confidence intervals | Q6 | Lower priority: [8] already covers it |

Q7 (imitation learning) is skipped: that field publishes on arXiv, CoRL and RSS, which Edison
already covers. Q8 is low priority.

Every search is limited to 2015–2026. Apply that and English-only with the database's filters
if the string doesn't already do it.

---

## Scopus (Advanced search)

Paste into **Advanced document search**. `W/3` = within 3 words, `*` = truncation, `"..."` =
loose phrase (hyphens and plurals are matched).

**S1: low-cost arms, measured performance**
```
TITLE-ABS-KEY( ( ( "low-cost" OR "low cost" OR inexpensive OR affordable OR "open-source" OR "open source" OR frugal OR "3D-printed" ) W/3 ( "robot* arm*" OR manipulator* OR cobot* ) OR ( piper W/2 robot* ) OR "SO-101" OR "SO-100" OR widowx OR mycobot OR xarm ) AND ( repeatab* OR "pose accuracy" OR "positioning accuracy" OR "position accuracy" OR "absolute accuracy" OR "ISO 9283" OR backlash OR payload ) ) AND PUBYEAR > 2014 AND PUBYEAR < 2027
```

**S2: repeatability measurement methods**
```
TITLE-ABS-KEY( ( "ISO 9283" OR ( ( repeatab* OR "pose accuracy" OR "positioning accuracy" ) W/5 ( robot* OR manipulator* ) ) ) AND ( camera* OR vision OR photogramm* OR "dial indicator*" OR "dial gauge*" OR fiducial* OR apriltag* OR aruco OR "low-cost" OR "low cost" ) ) AND PUBYEAR > 2014 AND PUBYEAR < 2027
```

**S2b: manipulation benchmarks with protocols (optional)**
```
TITLE-ABS-KEY( ( benchmark* OR "task board*" OR "test method*" OR "standard* test*" ) W/5 ( manipulat* OR grasp* OR "pick-and-place" OR "peg-in-hole" OR assembly ) AND ( reproducib* OR repeatab* OR protocol* ) AND ( robot* ) ) AND PUBYEAR > 2014 AND PUBYEAR < 2027
```

**S3: robot arms in self-driving labs**
```
TITLE-ABS-KEY( ( "self-driving lab*" OR "autonomous lab*" OR "laboratory automation" OR "automated laborator*" OR "robotic chemist" OR "materials acceleration platform*" OR "autonomous experimentation" OR "cloud lab*" ) AND ( "robot* arm*" OR manipulator* OR cobot* OR "collaborative robot*" OR "mobile manipulat*" ) ) AND PUBYEAR > 2014 AND PUBYEAR < 2027
```
If that returns more than ~300 results, narrow it with
`AND TITLE-ABS-KEY( "low-cost" OR "low cost" OR affordable OR frugal OR "open-source" OR "open source" )`.

**S4: the case against**
```
TITLE-ABS-KEY( ( "low-cost" OR "low cost" OR inexpensive OR affordable OR "open-source" OR "open source" OR hobby* OR "consumer-grade" ) W/3 ( robot* OR manipulator* ) AND ( limitation* OR drawback* OR backlash OR wear OR durabilit* OR failure* OR maintenance OR reliabilit* OR safety OR "total cost" OR "hidden cost*" ) AND ( laborator* OR "lab automation" OR industrial ) ) AND PUBYEAR > 2014 AND PUBYEAR < 2027
```

**S5: lab tasks with fiducial or wrist-camera localization**
```
TITLE-ABS-KEY( ( vial* OR pipett* OR "sample handling" OR labware OR "tool chang*" OR "well plate*" OR microplate* OR rack* ) AND ( "robot* arm*" OR manipulator* OR cobot* ) AND ( apriltag* OR aruco OR "fiducial marker*" OR "eye-in-hand" OR "wrist camera*" OR "visual servo*" OR localization OR localisation ) ) AND PUBYEAR > 2014 AND PUBYEAR < 2027
```

**S6: reporting success rates**
```
TITLE-ABS-KEY( ( "success rate*" OR "failure rate*" OR "mean time between failure*" OR intervention* ) W/10 ( "confidence interval*" OR "Clopper-Pearson" OR "Wilson score" OR binomial OR "sample size" ) AND robot* AND ( manipulat* OR grasp* OR "pick-and-place" OR "lab automation" ) ) AND PUBYEAR > 2014 AND PUBYEAR < 2027
```

Useful filters afterwards: Document type → Article, Conference Paper, Review. Subject area →
Engineering, Computer Science, Chemistry, Materials Science.

---

## Engineering Village (Compendex + Inspec)

Use **Expert search**, and tick both Compendex and Inspec if BYU has Inspec (then use
**Remove duplicates**). `WN KY` searches subject, title and abstract. Set the year range
2015–2026 with the date limiter under the search box. Engineering Village does not take
proximity operators next to phrases, so these use AND instead; expect more noise than Scopus.

**S1**
```
((("low cost" OR inexpensive OR affordable OR "open source" OR frugal OR "3D printed") AND ("robot arm" OR "robotic arm" OR manipulator* OR cobot*) AND (repeatab* OR "pose accuracy" OR "positioning accuracy" OR "position accuracy" OR "ISO 9283" OR backlash)) WN KY)
```

**S2**
```
((("ISO 9283" OR "pose repeatability" OR "positioning repeatability" OR "pose accuracy" OR "positioning accuracy") AND (robot* OR manipulator*) AND (camera* OR vision OR photogrammetr* OR "dial indicator" OR "dial gauge" OR fiducial* OR apriltag* OR aruco OR "low cost")) WN KY)
```

**S3**
```
((("self driving laboratory" OR "self driving lab" OR "autonomous laboratory" OR "laboratory automation" OR "automated laboratory" OR "robotic chemist" OR "materials acceleration platform" OR "autonomous experimentation") AND ("robot arm" OR "robotic arm" OR manipulator* OR cobot* OR "collaborative robot")) WN KY)
```

**S4**
```
((("low cost" OR inexpensive OR affordable OR "open source" OR hobby*) AND ("robot arm" OR "robotic arm" OR manipulator* OR cobot*) AND (limitation* OR drawback* OR backlash OR wear OR durability OR failure* OR maintenance OR reliability OR safety)) WN KY)
```

**S5**
```
(((vial* OR pipett* OR "sample handling" OR labware OR "tool changer" OR microplate*) AND ("robot arm" OR "robotic arm" OR manipulator* OR cobot*) AND (apriltag* OR aruco OR "fiducial marker" OR "eye in hand" OR "wrist camera" OR "visual servoing" OR localization)) WN KY)
```

**S6**
```
((("success rate" OR "failure rate" OR "mean time between failures") AND ("confidence interval" OR "Clopper Pearson" OR "Wilson score" OR binomial) AND robot*) WN KY)
```

**Controlled terms.** After a search, open a few good hits and look at their *Compendex
controlled terms* and *Inspec controlled terms*. Clicking one runs a search on that indexed
subject, which often finds papers whose abstracts use different words. The **Thesaurus** tab
lets you browse them (for example the terms near "robot", "accuracy", "laboratory").

---

## IEEE Xplore (Command Search)

Advanced Search → **Command Search**. Each term needs its own field prefix. Set the year range
with the filter on the results page. Xplore rejects very long strings, so these are shorter;
if one is rejected, drop the least useful terms.

**S1**
```
("All Metadata":"low-cost" OR "All Metadata":"low cost" OR "All Metadata":affordable OR "All Metadata":"open-source") AND ("All Metadata":"robot arm" OR "All Metadata":"robotic arm" OR "All Metadata":manipulator) AND ("All Metadata":repeatability OR "All Metadata":"positioning accuracy" OR "All Metadata":"pose accuracy" OR "All Metadata":"ISO 9283")
```

**S2**
```
("All Metadata":"ISO 9283" OR "All Metadata":"pose repeatability" OR "All Metadata":"positioning repeatability") AND ("All Metadata":robot*) AND ("All Metadata":camera OR "All Metadata":vision OR "All Metadata":fiducial OR "All Metadata":"dial indicator")
```

**S3**
```
("All Metadata":"self-driving lab" OR "All Metadata":"self-driving laboratory" OR "All Metadata":"laboratory automation" OR "All Metadata":"autonomous laboratory" OR "All Metadata":"lab automation") AND ("All Metadata":"robot arm" OR "All Metadata":"robotic arm" OR "All Metadata":manipulator OR "All Metadata":cobot)
```

**S4**
```
("All Metadata":"low-cost" OR "All Metadata":"low cost" OR "All Metadata":affordable) AND ("All Metadata":"robot arm" OR "All Metadata":"robotic arm" OR "All Metadata":manipulator) AND ("All Metadata":backlash OR "All Metadata":durability OR "All Metadata":reliability OR "All Metadata":limitations OR "All Metadata":failure)
```

**S5**
```
("All Metadata":vial OR "All Metadata":pipette OR "All Metadata":labware OR "All Metadata":"tool changer") AND ("All Metadata":"robot arm" OR "All Metadata":"robotic arm" OR "All Metadata":manipulator) AND ("All Metadata":AprilTag OR "All Metadata":ArUco OR "All Metadata":fiducial OR "All Metadata":"eye-in-hand")
```

**S6**
```
("All Metadata":"success rate" OR "All Metadata":"failure rate") AND ("All Metadata":"confidence interval" OR "All Metadata":"Clopper-Pearson" OR "All Metadata":binomial) AND ("All Metadata":robot*) AND ("All Metadata":manipulation OR "All Metadata":grasping)
```

Worth scanning by hand in Xplore: the **IEEE CASE** proceedings and *IEEE Transactions on
Automation Science and Engineering* (filter by Publication Title) for lab automation.

---

## If a string fails

- **Zero results:** drop the third AND block first, then loosen the phrases.
- **Too many results (over ~500):** search titles only (`TITLE(...)` in Scopus, `WN TI` in
  Engineering Village, `"Document Title":` in Xplore), or add the low-cost block to S3.
- **Syntax error:** paste the error message into a Claude session and it can fix the string.

## Search log

Record each run; the proposal's method section can cite this.

| Date | Database | Search | Filters applied | Hits | Exported file |
|---|---|---|---|---|---|
| | Scopus | S1 | | | |
| | Scopus | S2 | | | |
| | Scopus | S3 | | | |
| | Scopus | S4 | | | |
| | Scopus | S5 | | | |
| | Scopus | S6 | | | |
| | Engineering Village | S1 | | | |
| | Engineering Village | S2 | | | |
| | Engineering Village | S3 | | | |
| | Engineering Village | S4 | | | |
| | Engineering Village | S5 | | | |
| | Engineering Village | S6 | | | |
| | IEEE Xplore | S1 | | | |
| | IEEE Xplore | S2 | | | |
| | IEEE Xplore | S3 | | | |
| | IEEE Xplore | S4 | | | |
| | IEEE Xplore | S5 | | | |
| | IEEE Xplore | S6 | | | |
