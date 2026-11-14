# Printed tag pages on the A1 mini, seen from mpzy's camera (2026-11-14)

Two printed pages lay on the A1 mini: the 25 mm page (IDs 30-53, page 6 of
`tag36h11_print_sheets.pdf`) partly under the 10 mm page (IDs 60-107, page 7). mpzy's
livestream was stopped, so nothing was restarted: nine full-resolution `rpicam-still` frames
(4608x2592) were taken from cam0 (Module 3 Wide, front) at 02:00-02:02 UTC. No people are in view.

| | 25 mm page | 10 mm page |
| --- | --- | --- |
| Tags read, full resolution | all 9 not covered by the other page, in 9 of 9 frames | 0 of 48, in every frame, even from a 2-3x upscaled crop |
| Distance, tilt | 0.94-1.02 m, 57-67° off the line of sight | the same place |
| Size in the frame | 23-27 px on the short side, 61-70 px on the long | about 10 px short side, about 1.2 px per cell |
| Frame-to-frame scatter | 0.07 mm across the line of sight, 0.3-0.9 mm along it, 0.1° normal | - |
| Neighbour spacing vs print | 10 of 12 pairs within 1.3 mm; 34-35 off by 4.7 mm (curled edge) | - |
| Orientation | tag 50 came out flipped (56° from the others) | - |
| At 2304x1296 / 1280x720 (stream) | 2-3 of 9 / none | - |

Intrinsics are nominal (f = 1964 px, no distortion), so absolute distances are only as good as
that. `analyze.py` reproduces `results.json` from the frames; only the first is committed.
