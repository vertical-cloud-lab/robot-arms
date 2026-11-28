# References

Every DOI below was looked up in Crossref (DataCite for the arXiv DOI) on 2026-11-27. Each one's
registered title, first author, year, journal, volume and first page match what is written here:
23 of 23. The report is [`analysis/out/crossref.md`](analysis/out/crossref.md), and
[`analysis/crossref_check.py`](analysis/crossref_check.py) reruns it. Items without a DOI are
marked; their links were checked to resolve on 2026-11-27.

## Failure taxonomy

1. Wang, H., Sun, B., Zou, A., Huang, D., Lv, Z., Wang, N., Li, R., Zhou, D., Guo, W., Wang, Z. and
   Ouyang, W. (2026). LabRobFail: A Benchmark for Robotic Failure Analysis in Chemical Self-driving
   Laboratory. arXiv:2607.23704, version 2. [doi:10.48550/arXiv.2607.23704](https://doi.org/10.48550/arXiv.2607.23704).
   Code: [Su-ISE-2001/LabRobFail](https://github.com/Su-ISE-2001/LabRobFail). The quotes in
   PROTOCOL.md §13 are from v2 and were checked against its text in October.

## Robot performance and metrology

2. ISO 9283:1998. *Manipulating industrial robots: performance criteria and related test methods.*
   International Organization for Standardization. No DOI. Cited for §6.2 (warm-up), §6.5
   (instrumentation and the 25 % uncertainty cap), §6.6 (load), §6.7 (velocities), §6.8 (test
   poses) and §7.2.2 (RP). Only the [free sample pages](https://cdn.standards.iteh.ai/samples/22244/d058a9d8bacf41cd85def67ab70afc87/ISO-9283-1998.pdf)
   were read, and they stop before §6.8; see bench gate RB2.
3. Kuric, I., Tlach, V., Ságová, Z., Císar, M. and Gritsuk, I. (2018). Measurement of industrial
   robot pose repeatability. *MATEC Web of Conferences* 244, 01015.
   [doi:10.1051/matecconf/201824401015](https://doi.org/10.1051/matecconf/201824401015).
   The ISO cube, the five-pose plane and the one-way approach.
4. AgileX Robotics. PiPER product page, [global.agilex.ai/products/piper-6-dof-robotic-arm](https://global.agilex.ai/products/piper-6-dof-robotic-arm),
   and the reseller listing at [openelab.io](https://openelab.io/products/agilex-piper-ros-ai-arm)
   (payload, reach, repeatability). No DOI. Vendor figures, not measured here.

## Fiducials and calibration

5. Olson, E. (2011). AprilTag: A robust and flexible visual fiducial system. *2011 IEEE
   International Conference on Robotics and Automation*, 3400–3407.
   [doi:10.1109/ICRA.2011.5979561](https://doi.org/10.1109/ICRA.2011.5979561).
6. Wang, J. and Olson, E. (2016). AprilTag 2: Efficient and robust fiducial detection. *2016
   IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)*, 4193–4198.
   [doi:10.1109/IROS.2016.7759617](https://doi.org/10.1109/IROS.2016.7759617).
7. Tsai, R. Y. and Lenz, R. K. (1989). A new technique for fully autonomous and efficient 3D
   robotics hand/eye calibration. *IEEE Transactions on Robotics and Automation* 5(3), 345–358.
   [doi:10.1109/70.34770](https://doi.org/10.1109/70.34770).

## Statistics

8. Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference.
   *Journal of the American Statistical Association* 22(158), 209–212.
   [doi:10.1080/01621459.1927.10502953](https://doi.org/10.1080/01621459.1927.10502953).
9. Clopper, C. J. and Pearson, E. S. (1934). The use of confidence or fiducial limits illustrated
   in the case of the binomial. *Biometrika* 26(4), 404–413.
   [doi:10.1093/biomet/26.4.404](https://doi.org/10.1093/biomet/26.4.404).
10. Newcombe, R. G. (1998). Interval estimation for the difference between independent
    proportions: comparison of eleven methods. *Statistics in Medicine* 17(8), 873–890.
    [doi:10.1002/(SICI)1097-0258(19980430)17:8<873::AID-SIM779>3.0.CO;2-I](https://doi.org/10.1002/(SICI)1097-0258(19980430)17:8%3C873::AID-SIM779%3E3.0.CO;2-I).
11. Boschloo, R. D. (1970). Raised conditional level of significance for the 2 × 2-table when
    testing the equality of two probabilities. *Statistica Neerlandica* 24(1), 1–9.
    [doi:10.1111/j.1467-9574.1970.tb00104.x](https://doi.org/10.1111/j.1467-9574.1970.tb00104.x).
12. Firth, D. (1993). Bias reduction of maximum likelihood estimates. *Biometrika* 80(1), 27–38.
    [doi:10.1093/biomet/80.1.27](https://doi.org/10.1093/biomet/80.1.27).
13. Heinze, G. and Schemper, M. (2002). A solution to the problem of separation in logistic
    regression. *Statistics in Medicine* 21(16), 2409–2419.
    [doi:10.1002/sim.1047](https://doi.org/10.1002/sim.1047).
14. Fieller, E. C. (1954). Some problems in interval estimation. *Journal of the Royal Statistical
    Society: Series B (Methodological)* 16(2), 175–185.
    [doi:10.1111/j.2517-6161.1954.tb00159.x](https://doi.org/10.1111/j.2517-6161.1954.tb00159.x).
15. Hodges, J. L. and Lehmann, E. L. (1963). Estimates of location based on rank tests. *The Annals
    of Mathematical Statistics* 34(2), 598–611.
    [doi:10.1214/aoms/1177704172](https://doi.org/10.1214/aoms/1177704172).
16. Bauer, D. F. (1972). Constructing confidence sets using rank statistics. *Journal of the
    American Statistical Association* 67(339), 687–690.
    [doi:10.1080/01621459.1972.10481279](https://doi.org/10.1080/01621459.1972.10481279).
17. Kaplan, E. L. and Meier, P. (1958). Nonparametric estimation from incomplete observations.
    *Journal of the American Statistical Association* 53(282), 457–481.
    [doi:10.1080/01621459.1958.10501452](https://doi.org/10.1080/01621459.1958.10501452).
18. Royston, P. and Parmar, M. K. B. (2013). Restricted mean survival time: an alternative to the
    hazard ratio for the design and analysis of randomized trials with a time-to-event outcome.
    *BMC Medical Research Methodology* 13, 152.
    [doi:10.1186/1471-2288-13-152](https://doi.org/10.1186/1471-2288-13-152).
19. Klein, J. P. and Moeschberger, M. L. (2003). *Survival Analysis: Techniques for Censored and
    Truncated Data*, 2nd ed. Springer. [doi:10.1007/b97377](https://doi.org/10.1007/b97377).
    The variance of the restricted mean (§4.5).
20. Garwood, F. (1936). Fiducial limits for the Poisson distribution. *Biometrika* 28(3–4),
    437–442. [doi:10.1093/biomet/28.3-4.437](https://doi.org/10.1093/biomet/28.3-4.437).
21. Aalen, O. O. and Johansen, S. (1978). An empirical transition matrix for non-homogeneous Markov
    chains based on censored observations. *Scandinavian Journal of Statistics* 5(3), 141–150.
    No DOI. Volume and pages confirmed from secondary listings (for example the R `etm` package's
    documentation), not from the journal itself.
22. Efron, B. (1987). Better bootstrap confidence intervals. *Journal of the American Statistical
    Association* 82(397), 171–185.
    [doi:10.1080/01621459.1987.10478410](https://doi.org/10.1080/01621459.1987.10478410).
23. Efron, B. and Tibshirani, R. J. (1994). *An Introduction to the Bootstrap.* Chapman and
    Hall/CRC. [doi:10.1201/9780429246593](https://doi.org/10.1201/9780429246593). First published
    1993; the DOI's record gives 1994. The bootstrap-t (§14.5) and percentile intervals.
24. Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological
    Measurement* 20(1), 37–46. [doi:10.1177/001316446002000104](https://doi.org/10.1177/001316446002000104).

## Pre-registration and self-driving labs

25. Nosek, B. A., Ebersole, C. R., DeHaven, A. C. and Mellor, D. T. (2018). The preregistration
    revolution. *Proceedings of the National Academy of Sciences* 115(11), 2600–2606.
    [doi:10.1073/pnas.1708274114](https://doi.org/10.1073/pnas.1708274114).
26. MacLeod, B. P., Parlane, F. G. L., Morrissey, T. D., Häse, F., Roch, L. M., Dettelbach, K. E.,
    Moreira, R., Yunker, L. P. E., Rooney, M. B., Deeth, J. R., Lai, V., Ng, G. J., Situ, H.,
    Zhang, R. H., Elliott, M. S., Haley, T. H., Dvorak, D. J., Aspuru-Guzik, A., Hein, J. E. and
    Berlinguette, C. P. (2020). Self-driving laboratory for accelerated discovery of thin-film
    materials. *Science Advances* 6(20), eaaz8867.
    [doi:10.1126/sciadv.aaz8867](https://doi.org/10.1126/sciadv.aaz8867). The Ada platform. **Not
    yet checked:** whether this paper (or a later Ada paper) is the source of the "one run-ending
    failure per 40 samples" figure that the literature scan on #1 attributes to Ada (PROTOCOL.md
    §1).
27. Center for Open Science. OSF Preregistration template, version 4 (OSF Registries schema
    `697b72f611a8e98484c6139b`, read through `api.osf.io` on 2026-11-27), and
    [cos.io/osf-changes](https://www.cos.io/osf-changes) on the end of new OSF projects. No DOI.

## Design sources in the lab's repositories

28. [byu-vcl issue 266](https://github.com/vertical-cloud-lab/byu-vcl/issues/266) and
    [byu-vcl PR 272](https://github.com/vertical-cloud-lab/byu-vcl/pull/272): the dock, carrier,
    finger inserts, offset plates, the error budget and the capture ranges.
29. [robot-arms PR 23](https://github.com/vertical-cloud-lab/robot-arms/pull/23): the hazard
    analysis, SOP and checklist for the cell (draft).
30. [robot-arms #1](https://github.com/vertical-cloud-lab/robot-arms/issues/1): the literature
    scan behind the Ada figure and the LabRobFail check.
