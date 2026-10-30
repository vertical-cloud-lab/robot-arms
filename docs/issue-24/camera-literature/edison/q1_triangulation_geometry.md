# Edison job-futurehouse-paperqa3-high — q1_triangulation_geometry

- task id: `608d6d35-9a47-4855-bf32-832049726449`
- submitted: 2026-10-21T20:58:07Z

## Query

Setup: a tabletop 6-DOF robot arm (AgileX PiPER, about 0.63 m reach, fingertips reach about 0.76 m at table height) on a 1.29 x 1.36 m table against a wall. We want fixed RGB cameras (Raspberry Pi Camera Module 3 Wide, 102 x 67 deg field of view, 4608 x 2592 px) that (a) triangulate the gripper fingertips to check the arm's joint-angle kinematics (detect drift of a few mm), (b) show whether the workspace is clear, and (c) may later feed learned visuomotor policies. Current proposal: one camera about 1.2 m above the table looking straight down, one about 0.8 m from the arm base past the table end the arm faces at joint 1 = 0, about 0.42 m up and tilted 19 deg down, and a third low camera on the room-side table edge looking toward the wall. What do the close-range photogrammetry and multi-view computer vision literatures say about: (1) the optimal intersection (convergence) angle between camera rays for minimizing 3D triangulation error, and how fast the error grows when the angle falls below about 30-60 deg or rises above about 120 deg; (2) whether one near-vertical (nadir) camera plus two low oblique side cameras is a strong network for 3D point accuracy, compared with, for example, three cameras all elevated 30-45 deg and spread about 120 deg apart in azimuth; (3) how baseline, camera-to-target distance and pixel resolution set the depth error; and (4) how self-occlusion by the arm should change the number and spread of cameras (e.g. optimal camera placement for motion capture with occlusion). Give quantitative rules of thumb with citations.

## Answer

Question: Setup: a tabletop 6-DOF robot arm (AgileX PiPER, about 0.63 m reach, fingertips reach about 0.76 m at table height) on a 1.29 x 1.36 m table against a wall. We want fixed RGB cameras (Raspberry Pi Camera Module 3 Wide, 102 x 67 deg field of view, 4608 x 2592 px) that (a) triangulate the gripper fingertips to check the arm's joint-angle kinematics (detect drift of a few mm), (b) show whether the workspace is clear, and (c) may later feed learned visuomotor policies. Current proposal: one camera about 1.2 m above the table looking straight down, one about 0.8 m from the arm base past the table end the arm faces at joint 1 = 0, about 0.42 m up and tilted 19 deg down, and a third low camera on the room-side table edge looking toward the wall. What do the close-range photogrammetry and multi-view computer vision literatures say about: (1) the optimal intersection (convergence) angle between camera rays for minimizing 3D triangulation error, and how fast the error grows when the angle falls below about 30-60 deg or rises above about 120 deg; (2) whether one near-vertical (nadir) camera plus two low oblique side cameras is a strong network for 3D point accuracy, compared with, for example, three cameras all elevated 30-45 deg and spread about 120 deg apart in azimuth; (3) how baseline, camera-to-target distance and pixel resolution set the depth error; and (4) how self-occlusion by the arm should change the number and spread of cameras (e.g. optimal camera placement for motion capture with occlusion). Give quantitative rules of thumb with citations.

## Camera Placement for Triangulating a Tabletop Robot Arm: Quantitative Guidance from Photogrammetry and Multi-View Vision

### 1. Optimal Convergence (Intersection) Angle for 3D Triangulation

The convergence angle θ—the angle between two camera rays at the target point—is the single most important geometric parameter for triangulation accuracy. Classical photogrammetric analysis and empirical studies converge on an optimum near **90°**, with a broad practical sweet spot of roughly **60–120°**.

**Geometric basis.** In the stereo depth relation, the depth component of the reconstructed point depends on the reciprocal of the sine of the half-convergence angle. Weinshall (1990) showed that reconstructed depth is proportional to a disparity term divided by 2 sin(α), where the total convergence angle is 2α, establishing an explicit reciprocal-sine dependence (weinshall1990qualitativedepthfrom pages 3-6). This means that at very small intersection angles, depth uncertainty diverges approximately as 1/sin(θ/2), while at 90° the geometric contribution to depth error is minimized.

**Empirical confirmation.** Di et al. (2016), analyzing multi-image triangulation of lunar images, found that overall positional error reached its minimum near a convergence angle of approximately **60°**, while height (depth) error reached its minimum near **90°** (di2016geopositioningprecisionanalysis pages 4-5). When image-matching errors were included, the optimal turning points shifted toward somewhat smaller angles because larger convergence angles degrade image correlation and matching precision (di2016geopositioningprecisionanalysis pages 4-5). Li et al. (2014), studying rover localization with the ExoMars PanCam, found optimal convergence angles of **99–100°** for 6-landmark configurations, **100–108°** for 9–12 landmarks, and a recommended operational band of **70–90°** (li2014esaexomarsprelaunch pages 4-5). Olague and Mohr (2002) found an optimal convergence angle around **45°** in their multi-camera setup, corresponding to an approximately 90° inter-camera separation, with their image-error model showing that target-localization uncertainty rises sharply as the incidence angle approaches 80° due to foreshortening (olague2002optimalcameraplacement pages 9-12, olague2002optimalcameraplacement pages 5-6).

**Error growth outside the sweet spot.** At angles below ~30°, rays become nearly parallel, the system is poorly conditioned, and depth error increases rapidly—approximately inversely with the sine of the convergence angle (di2016geopositioningprecisionanalysis pages 3-4, recker2013statisticalangularerrorbased pages 3-4). At very small angles (5–15°), Nesbit and Hugenholtz (2019) observed systematic bowl-shaped deformation, substantially lower precision, and larger offsets from reference data (nesbit2019enhancinguavsfm3d pages 16-18, nesbit20203dgeologicmapping pages 119-124). Above ~120°, the geometric benefit plateaus while image correspondence degrades due to extreme foreshortening and appearance distortion, causing a net increase in reconstruction error (di2016geopositioningprecisionanalysis pages 4-5, olague2002optimalcameraplacement pages 5-6).

### 2. Nadir + Oblique vs. All-Oblique Camera Networks

Fraser's (1984) seminal simulations of a 27-point target array compared six four-camera imaging configurations under identical conditions (image scale 1:40, σ_image = 2.3 μm, inner-constraints datum). The results are summarized below:

| Configuration | Convergence angle θ | q-factor | Mean σ_c (mm) | σ_XY (mm) | σ_Z (mm) | Δσ_XY (mm) | Δσ_Z (mm) |
|---|---:|---:|---:|---:|---:|---:|---:|
| “Normal,” stations 9–12 | — | 0.7 | 0.09 | 0.07 | 0.12 | 0.03 | 0.09 |
| “Normal,” stations 5–8 | — | 1.0 | 0.12 | 0.08 | 0.17 | 0.03 | 0.12 |
| “Normal” + convergent, stations 2, 4, 5, 7 | 120° for convergent component | 0.6 | 0.07 | 0.07 | 0.09 | 0.01 | 0.05 |
| Convergent | 60° | 0.8 | 0.09 | 0.07 | 0.13 | 0.02 | 0.09 |
| Convergent | 120° | 0.6 | 0.07 | 0.07 | 0.07 | 0.01 | 0.03 |
| Convergent | 180° | 0.6 | 0.07 | 0.08 | 0.06 | 0.01 | 0.01 |
| **Common simulation conditions** (fraser1984networkdesignconsiderations pages 5-6, fraser1984networkdesignconsiderations pages 6-7) | **Inner-constraints datum** | **Image scale 1:40** | **σ_image = 2.3 μm** | — | — | — | — |


*Table: Fraser’s 1984 four-image simulations compare normal, mixed, and convergent networks under common scale, image-precision, and datum assumptions. The 120° convergent network gives isotropic XY/Z precision, while 180° gives the most homogeneous coordinate precision.*

Key findings from this comparison include:

- **Convergent θ = 120°** produced the most isotropic precision, with σ_XY = σ_Z = 0.07 mm and very small precision ranges (Δσ_XY = 0.01 mm, Δσ_Z = 0.03 mm), making it Fraser's recommended design for most 3D measurement tasks (fraser1984networkdesignconsiderations pages 6-7).
- **Convergent θ = 180°** gave the most homogeneous distribution (Δσ_Z = 0.01 mm), though σ_XY was slightly larger than σ_Z (fraser1984networkdesignconsiderations pages 6-7).
- **Normal + convergent** (a mixed geometry analogous to the user's proposed nadir-plus-oblique layout) performed nearly as well as the all-convergent networks (q = 0.6, σ_Z reduced to 0.09 mm), demonstrating that adding even two convergent views to a nadir-like configuration substantially improves Z-precision (fraser1984networkdesignconsiderations pages 5-6, fraser1984networkdesignconsiderations pages 6-7).
- **Pure "normal" (near-parallel axis) networks** showed the largest Z-error and the poorest homogeneity, with σ_Z roughly 1.5–2.5× larger than σ_XY (fraser1984networkdesignconsiderations pages 5-6).

In UAV photogrammetry, Nesbit and Hugenholtz (2019) confirmed that supplementing nadir images with oblique images at **20–35°** tilt improved accuracy and precision by nearly **50%** relative to nadir-only blocks (nesbit2019enhancinguavsfm3d pages 1-3). Combination datasets consistently reduced systematic dome deformation, generated more tie points, and produced lower standard deviations than either nadir-only or single-oblique datasets (nesbit20203dgeologicmapping pages 119-124, nesbit2019enhancinguavsfm3d pages 16-18). The precision-to-viewing-distance ratio improved from approximately 1:1000 for nadir-only to about 1:1500 for combination datasets (nesbit2019enhancinguavsfm3d pages 16-18).

**Implication for the proposed setup.** A one-overhead plus two-oblique arrangement is a variant of the "normal + convergent" geometry that Fraser showed performs well (q = 0.6). However, the overhead camera provides good XY but poor Z resolution for table-plane-parallel targets. The two oblique cameras provide the convergent rays needed for Z. For near-isotropic 3D accuracy, the three-camera all-oblique alternative (cameras at ~30–45° elevation, spread ~120° in azimuth) would produce more uniform error ellipsoids, consistent with Fraser's finding that the convergent θ = 120° network was the best general-purpose design (fraser1984networkdesignconsiderations pages 6-7).

### 3. Depth Error as a Function of Baseline, Distance, and Pixel Resolution

The fundamental relationship for stereo triangulation depth uncertainty is well established across the literature. For a rectified stereo pair with baseline B, focal length f (in pixels f_px = f_phys/p, where p is pixel pitch), and target at depth Z, depth is given by Z = f_px · B / d, where d is disparity in pixels. Propagating a disparity measurement error σ_d (typically ~0.5–1.0 pixels for sub-pixel matching) yields:

**σ_Z ≈ Z² · σ_d / (f_px · B)**

Equivalently, in terms of the physical focal length f_phys and pixel pitch p:

**σ_Z ≈ Z² · p · σ_d / (f_phys · B)**

This relationship was derived and confirmed by multiple sources (rumpler2011multiviewstereoredundancy pages 1-3, llorca2010erroranalysisin pages 8-13, llorca2010erroranalysisin pages 1-4). The key dependencies are:
- Depth error grows **quadratically** with camera-to-target distance Z.
- Depth error decreases **linearly** with baseline B.
- Depth error decreases **linearly** with focal length in pixels f_px (equivalently, with physical focal length f_phys for fixed pixel pitch).
- Larger pixels (larger p) increase depth error for a given physical focal length (lin2021modelingandanalysis pages 3-6, lin2021modelingandanalysis pages 8-11).

Lin et al. (2021) confirmed these relationships through a geometric pixel-quantization cone model, showing that increasing baseline or focal length narrows the uncertainty volume, while increasing pixel size or target distance enlarges it (lin2021modelingandanalysis pages 3-6, lin2021modelingandanalysis pages 8-11). Llorca et al. (2010) additionally noted that larger baseline and focal length increase the disparity search space and the near-field blind zone, creating design tradeoffs in practical systems (llorca2010erroranalysisin pages 8-13).

**Numerical example for the proposed setup.** With the Raspberry Pi Camera Module 3 Wide (f ≈ 2.75 mm, sensor 6.45 × 3.63 mm, 4608 × 2592 pixels → pixel pitch p ≈ 1.4 μm, f_px ≈ 1964 pixels), a baseline of ~1.0 m, and a maximum gripper distance of ~1.5 m from the closer cameras: σ_Z ≈ (1.5)² × 1 / (1964 × 1.0) ≈ 1.1 mm per pixel of disparity error. With sub-pixel matching (σ_d ≈ 0.3 px), this yields σ_Z ≈ 0.3 mm, which is within the few-mm drift detection requirement.

### 4. Self-Occlusion by the Arm and Camera Count/Spread

Self-occlusion by the robot arm's own links is the primary driver for requiring multiple cameras at different viewpoints. The literature on multi-camera motion capture provides quantitative guidance:

**Angular baseline.** Starck et al. (2009), in their comprehensive study of multi-camera 3D production studios, found that an angular baseline of approximately **25°** between neighboring camera views was optimal for stereo matching, balancing correspondence reliability against depth ambiguity. In a planar ring, this corresponds to roughly 14 cameras for 360° coverage (starck2009themultiplecamera3d pages 26-30, starck2009themultiplecamera3d pages 18-20).

**Minimum cameras for stable coverage.** For full-body surface reconstruction, angular-coverage stability was reached at approximately **16 cameras**, after which additional cameras produced diminishing returns in visibility improvement. However, achieving reconstruction error below 50 mm in their experiments required at least 42 cameras (starck2009themultiplecamera3d pages 16-18, starck2009themultiplecamera3d pages 12-16). These numbers apply to complete surface reconstruction of a complex human body and represent an upper bound for the simpler problem of tracking discrete gripper fingertip markers.

**Non-planar arrangement is critical.** Cameras should not all be placed in a single plane, as this creates systematic blind spots (starck2009themultiplecamera3d pages 26-30). Including cameras at different elevations—including overhead views—reduces phantom volumes from self-occlusion, particularly for an articulated arm that can fold back on itself (starck2009themultiplecamera3d pages 12-16, starck2009themultiplecamera3d pages 18-20).

**Active viewpoint selection.** Kiciroglu et al. (2020) demonstrated that optimizing camera viewpoints based on predicted pose uncertainty can substantially improve 3D pose estimation accuracy, suggesting that cameras should be positioned where they provide the most information given expected arm configurations, rather than in a generic symmetric arrangement (kiciroglu2020activemocapoptimizedviewpoint pages 1-2).

**Practical guidance for a tabletop arm.** For the specific task of triangulating discrete fingertip features (not full surface reconstruction), the occlusion problem is substantially simpler than full-body capture. Fraser (1984) recommended a minimum of **three intersecting rays** (not in the same epipolar plane) at every target point (fraser1984networkdesignconsiderations pages 6-7, fraser1984networkdesignconsiderations pages 7-9). With the arm's ~0.63 m reach on a 1.29 × 1.36 m table, the arm subtends a relatively small solid angle, meaning three well-placed cameras with the wide 102° × 67° field of view should maintain at least two-camera visibility of the fingertips throughout most of the workspace. A fourth camera would provide redundancy for configurations where one camera's view is blocked by the arm's body or by the gripper approaching the camera.

Luhmann (2010) reported that multi-camera photogrammetric probing systems using 2–4 digital video cameras achieve typical accuracy of 0.1 mm over distances of 2–5 m, with the imaging rays intersecting at large convergence angles to yield homogeneous accuracy in X, Y, and Z (luhmann2010closerangephotogrammetry pages 6-8). This supports the feasibility of achieving sub-millimeter accuracy with a small number of strategically placed cameras.

### Summary of Key Quantitative Rules of Thumb

| Topic | Rule of Thumb / Formula | Quantitative Value | Key Source |
|---|---|---:|---|
| Preferred ray-intersection angle | For isolated-point triangulation with comparable angular noise, aim near a right-angle intersection; **60–120°** is a useful practical band. Angle definitions vary across papers, so compare the actual angle between rays at the target. | Ideal ≈ **90°**; practical ≈ **60–120°** | Simulations found minimum height error near 90° and minimum overall position error near 60°; strongly convergent networks produced homogeneous 3D precision. (di2016geopositioningprecisionanalysis pages 4-5, fraser1984networkdesignconsiderations pages 6-7) |
| Rectified-stereo depth uncertainty | `Z = f_px B / d`, hence `σ_Z ≈ Z² σ_d / (f_px B)`. Equivalently, `σ_Z ≈ Z² p σ_d / (f_phys B)`, where `p` is pixel pitch and `σ_d` is in pixels. | Error grows as **distance²** and falls linearly with **baseline** and **focal length in pixels**. | (rumpler2011multiviewstereoredundancy pages 1-3, llorca2010erroranalysisin pages 8-13) |
| Fraser network comparison | Symmetric convergent imaging makes coordinate precision more isotropic than normal or near-parallel imaging; mixed normal-plus-convergent geometry is also strong. | Mean accuracy factor `q`: **0.6** at 120° convergence versus **0.7–1.0** for the two normal networks; 120° gave `σ_XY = σ_Z = 0.07 mm` in the simulation. | (fraser1984networkdesignconsiderations pages 5-6, fraser1984networkdesignconsiderations pages 6-7) |
| Moderate oblique imagery | Supplementing nadir coverage with oblique images increases parallax, reduces systematic deformation, and fills visibility gaps. | Oblique tilt **20–35° from nadir**; nearly **50%** improvement in accuracy and precision over nadir-only blocks in the studied high-relief scene. | (nesbit2019enhancinguavsfm3d pages 1-3) |
| Occlusion-resistant dense capture | For full-body surface reconstruction, distribute cameras non-coplanarly around the subject; neighboring views should retain enough appearance similarity for matching. These counts are not a minimum for fingertip triangulation. | Neighboring angular baseline ≈ **25°**; visibility coverage stabilized near **16 cameras** in the reported studio experiment. | (starck2009themultiplecamera3d pages 26-30, starck2009themultiplecamera3d pages 16-18) |
| Li et al. convergence optimum | Error minima occurred over a range rather than at one universal angle; well-distributed tie points changed the optimum. | With 6 landmarks, optimum ≈ **99–100°**; with 9–12, approximately **100–108°** in two tested camera systems; operational band cited as **70–90°**. | (li2014esaexomarsprelaunch pages 4-5) |
| Benefit of additional cameras | Once geometry is strong, precision improves approximately with the square root of observation count: `σ_XYZ ∝ 1 / √m`. Geometry matters more than merely adding similar views. | Moving from **2 to 3** cameras gives a substantial gain; **3 to 4** yields about **20%** lower standard error under the approximation. | (fraser1984networkdesignconsiderations pages 6-7, fraser1984networkdesignconsiderations pages 7-9) |
| Excessively wide view differences | Larger intersection angles improve geometry only until correspondence and target-localization errors rise from foreshortening and appearance distortion. Thus, the geometric 90° preference is not an instruction to maximize angle indefinitely. | Di et al.: height-error curve minimum near **90°**, then increases; Olague–Mohr’s target-localization model rose sharply as incidence approached **80°**. | (olague2002optimalcameraplacement pages 5-6, di2016geopositioningprecisionanalysis pages 4-5) |


*Table: Key geometric and empirical rules for designing a multi-camera triangulation network, including convergence angle, depth uncertainty, oblique coverage, camera count, and occlusion tradeoffs.*

### Recommendations for the Proposed Setup

Based on the literature, the proposed three-camera arrangement (one overhead at 1.2 m, one front-oblique at ~0.42 m height tilted 19° down, one low side camera) provides a reasonable "normal + convergent" geometry. However, several improvements are suggested:

1. **Increase convergence angles.** The front camera at 19° tilt produces a very shallow convergence angle with the overhead camera (~71° from vertical vs. 0° overhead = only ~19° convergence). Raising its tilt or elevation would improve the ray-intersection geometry toward the 60–90° optimal range (di2016geopositioningprecisionanalysis pages 4-5, fraser1984networkdesignconsiderations pages 6-7).

2. **Spread cameras in azimuth.** The literature strongly favors cameras distributed ~120° apart in azimuth rather than clustered on one side, to produce isotropic XY precision and maintain visibility during arm self-occlusion (fraser1984networkdesignconsiderations pages 6-7, starck2009themultiplecamera3d pages 26-30).

3. **Consider a fourth camera.** Fraser showed that going from 3 to 4 cameras improves precision by ~20% under the √m rule (fraser1984networkdesignconsiderations pages 7-9). More importantly, a fourth camera provides critical redundancy when one view is occluded by the arm.

4. **Elevate all cameras to ~30–45°.** An all-oblique arrangement with three cameras at 30–45° elevation and 120° azimuth spacing would approach Fraser's θ = 120° convergent network, which gave the most isotropic and homogeneous precision (fraser1984networkdesignconsiderations pages 6-7). This configuration also provides better workspace-clearance views than a single nadir camera.

References

1. (weinshall1990qualitativedepthfrom pages 3-6): Daphna Weinshall. Qualitative depth from stereo, with applications. Comput. Vis. Graph. Image Process., 49:222-241, Feb 1990. URL: https://doi.org/10.1016/0734-189x(90)90138-l, doi:10.1016/0734-189x(90)90138-l. This article has 53 citations.

2. (di2016geopositioningprecisionanalysis pages 4-5): K. Di, Bin Xu, Bin Liu, M. Jia, and Z. S. Liu. Geopositioning precision analysis of multiple image triangulation using lro nac lunar images. ISPRS - International Archives of the Photogrammetry, Remote Sensing and Spatial Information Sciences, pages 369-374, Jun 2016. URL: https://doi.org/10.5194/isprs-archives-xli-b4-369-2016, doi:10.5194/isprs-archives-xli-b4-369-2016. This article has 9 citations.

3. (li2014esaexomarsprelaunch pages 4-5): D. Li, Rongxing Li, and A. Yilmaz. Esa exomars: pre-launch pancam geometric modeling and accuracy assessment. ISPRS - International Archives of the Photogrammetry, Remote Sensing and Spatial Information Sciences, pages 177-182, Aug 2014. URL: https://doi.org/10.5194/isprsarchives-xl-3-177-2014, doi:10.5194/isprsarchives-xl-3-177-2014. This article has 2 citations.

4. (olague2002optimalcameraplacement pages 9-12): Gustavo Olague and Roger Mohr. Optimal camera placement for accurate reconstruction. Pattern Recognit., 35:927-944, Apr 2002. URL: https://doi.org/10.1016/s0031-3203(01)00076-0, doi:10.1016/s0031-3203(01)00076-0. This article has 267 citations.

5. (olague2002optimalcameraplacement pages 5-6): Gustavo Olague and Roger Mohr. Optimal camera placement for accurate reconstruction. Pattern Recognit., 35:927-944, Apr 2002. URL: https://doi.org/10.1016/s0031-3203(01)00076-0, doi:10.1016/s0031-3203(01)00076-0. This article has 267 citations.

6. (di2016geopositioningprecisionanalysis pages 3-4): K. Di, Bin Xu, Bin Liu, M. Jia, and Z. S. Liu. Geopositioning precision analysis of multiple image triangulation using lro nac lunar images. ISPRS - International Archives of the Photogrammetry, Remote Sensing and Spatial Information Sciences, pages 369-374, Jun 2016. URL: https://doi.org/10.5194/isprs-archives-xli-b4-369-2016, doi:10.5194/isprs-archives-xli-b4-369-2016. This article has 9 citations.

7. (recker2013statisticalangularerrorbased pages 3-4): Shawn Recker, Mauricio Hess-Flores, and Kenneth I. Joy. Statistical angular error-based triangulation for efficient and accurate multi-view scene reconstruction. 2013 IEEE Workshop on Applications of Computer Vision (WACV), pages 68-75, Jan 2013. URL: https://doi.org/10.1109/wacv.2013.6475001, doi:10.1109/wacv.2013.6475001. This article has 28 citations.

8. (nesbit2019enhancinguavsfm3d pages 16-18): Paul Ryan Nesbit and Christopher H. Hugenholtz. Enhancing uav-sfm 3d model accuracy in high-relief landscapes by incorporating oblique images. Remote. Sens., 11:239, Jan 2019. URL: https://doi.org/10.3390/rs11030239, doi:10.3390/rs11030239. This article has 299 citations.

9. (nesbit20203dgeologicmapping pages 119-124): Paul Ryan Nesbit. 3d geologic mapping and characterization using digital outcrop models generated from uninhabited aerial vehicles and structure-from-motion photogrammetry. ArXiv, Jul 2020. URL: https://doi.org/10.11575/prism/38032, doi:10.11575/prism/38032. This article has 1 citations.

10. (fraser1984networkdesignconsiderations pages 5-6): CS Fraser. Network design considerations for non-topographic photogrammetry. Unknown journal, 1984.

11. (fraser1984networkdesignconsiderations pages 6-7): CS Fraser. Network design considerations for non-topographic photogrammetry. Unknown journal, 1984.

12. (nesbit2019enhancinguavsfm3d pages 1-3): Paul Ryan Nesbit and Christopher H. Hugenholtz. Enhancing uav-sfm 3d model accuracy in high-relief landscapes by incorporating oblique images. Remote. Sens., 11:239, Jan 2019. URL: https://doi.org/10.3390/rs11030239, doi:10.3390/rs11030239. This article has 299 citations.

13. (rumpler2011multiviewstereoredundancy pages 1-3): M Rumpler, A Irschara, and H Bischof. Multi-view stereo: redundancy benefits for 3d reconstruction. Unknown journal, 2011.

14. (llorca2010erroranalysisin pages 8-13): David F. Llorca, Miguel A. Sotelo, Ignacio Parra, Manuel Ocaña, and Luis M. Bergasa. Error analysis in a stereo vision-based pedestrian detection sensor for collision avoidance applications. Sensors (Basel, Switzerland), 10:3741-3758, Apr 2010. URL: https://doi.org/10.3390/s100403741, doi:10.3390/s100403741. This article has 58 citations.

15. (llorca2010erroranalysisin pages 1-4): David F. Llorca, Miguel A. Sotelo, Ignacio Parra, Manuel Ocaña, and Luis M. Bergasa. Error analysis in a stereo vision-based pedestrian detection sensor for collision avoidance applications. Sensors (Basel, Switzerland), 10:3741-3758, Apr 2010. URL: https://doi.org/10.3390/s100403741, doi:10.3390/s100403741. This article has 58 citations.

16. (lin2021modelingandanalysis pages 3-6): Danlan Lin, Zhenwei Wang, Hongsheng Shi, and Hong Chen. Modeling and analysis of pixel quantization error of binocular vision system with unequal focal length. Journal of Physics: Conference Series, 1738:012033, Jan 2021. URL: https://doi.org/10.1088/1742-6596/1738/1/012033, doi:10.1088/1742-6596/1738/1/012033. This article has 7 citations.

17. (lin2021modelingandanalysis pages 8-11): Danlan Lin, Zhenwei Wang, Hongsheng Shi, and Hong Chen. Modeling and analysis of pixel quantization error of binocular vision system with unequal focal length. Journal of Physics: Conference Series, 1738:012033, Jan 2021. URL: https://doi.org/10.1088/1742-6596/1738/1/012033, doi:10.1088/1742-6596/1738/1/012033. This article has 7 citations.

18. (starck2009themultiplecamera3d pages 26-30): J. Starck, A. Maki, S. Nobuhara, A. Hilton, and T. Matsuyama. The multiple-camera 3-d production studio. IEEE Transactions on Circuits and Systems for Video Technology, 19:856-869, Jun 2009. URL: https://doi.org/10.1109/tcsvt.2009.2017406, doi:10.1109/tcsvt.2009.2017406. This article has 74 citations and is from a domain leading peer-reviewed journal.

19. (starck2009themultiplecamera3d pages 18-20): J. Starck, A. Maki, S. Nobuhara, A. Hilton, and T. Matsuyama. The multiple-camera 3-d production studio. IEEE Transactions on Circuits and Systems for Video Technology, 19:856-869, Jun 2009. URL: https://doi.org/10.1109/tcsvt.2009.2017406, doi:10.1109/tcsvt.2009.2017406. This article has 74 citations and is from a domain leading peer-reviewed journal.

20. (starck2009themultiplecamera3d pages 16-18): J. Starck, A. Maki, S. Nobuhara, A. Hilton, and T. Matsuyama. The multiple-camera 3-d production studio. IEEE Transactions on Circuits and Systems for Video Technology, 19:856-869, Jun 2009. URL: https://doi.org/10.1109/tcsvt.2009.2017406, doi:10.1109/tcsvt.2009.2017406. This article has 74 citations and is from a domain leading peer-reviewed journal.

21. (starck2009themultiplecamera3d pages 12-16): J. Starck, A. Maki, S. Nobuhara, A. Hilton, and T. Matsuyama. The multiple-camera 3-d production studio. IEEE Transactions on Circuits and Systems for Video Technology, 19:856-869, Jun 2009. URL: https://doi.org/10.1109/tcsvt.2009.2017406, doi:10.1109/tcsvt.2009.2017406. This article has 74 citations and is from a domain leading peer-reviewed journal.

22. (kiciroglu2020activemocapoptimizedviewpoint pages 1-2): Sena Kiciroglu, Helge Rhodin, Sudipta N. Sinha, Mathieu Salzmann, and Pascal Fua. Activemocap: optimized viewpoint selection for active human motion capture. 2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), pages 100-109, Jun 2020. URL: https://doi.org/10.1109/cvpr42600.2020.00018, doi:10.1109/cvpr42600.2020.00018. This article has 66 citations.

23. (fraser1984networkdesignconsiderations pages 7-9): CS Fraser. Network design considerations for non-topographic photogrammetry. Unknown journal, 1984.

24. (luhmann2010closerangephotogrammetry pages 6-8): Thomas Luhmann. Close range photogrammetry for industrial applications. Isprs Journal of Photogrammetry and Remote Sensing, 65:558-569, Nov 2010. URL: https://doi.org/10.1016/j.isprsjprs.2010.06.003, doi:10.1016/j.isprsjprs.2010.06.003. This article has 494 citations and is from a domain leading peer-reviewed journal.
