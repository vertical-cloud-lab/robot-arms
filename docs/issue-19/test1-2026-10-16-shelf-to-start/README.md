# 2026-10-16 tests (issue #19, PR #20)

Run on the arm Pi from the home directory (copies of `scripts/`).

**Test 1, shelf back to the start** (`test1.log`, `test1_trace.csv`; the first try,
`attempt1_not_moving.log`, did not move because the arm was in STANDBY mode):

    ~/piper-venv/bin/python piper_pick_tape.py --go --until grasp --tape-r-mm 360 --plane-deg 130 \
        --pick-top-mm 60 --tilt-deg 20 --clear-mm 50 --place-r-mm 247 --place-deg 0 --carry-arc \
        --place-top-mm 0 --drop-mm 5 --speed 15 \
        --video ~/pick_tape_videos/test1.mjpeg --video-size 2304x1296 --video-fps 15 \
        --trace ~/pick_tape_videos/test1_trace.csv

Then, on a machine with numpy, scipy and opencv: `python fit_camera.py` (camera from this run),
`python ../../../scripts/make_iktable.py iktable.json` (joint table), `python plot_test1.py`.

**Test 2, camera-guided seek** (`../test2-2026-10-16-seek/`; run 4 picked the roll and stood it
back at the start, run 2 missed it because J1's reading was 7.9 deg high, run 3 refused to move):

    ~/piper-venv/bin/python piper_seek_tape.py --go --video ~/seek/run4/run4.mjpeg --trace ~/seek/run4/run4_trace.csv
    ~/piper-venv/bin/python piper_seek_tape.py --go --visit "450,114,180;250,-40,140" \
        --video ~/seek/check.mjpeg --trace ~/seek/check_trace.csv     # the J1 check run

Since 12bdf8b `piper_seek_tape.py` refuses to move when a joint's reading changes on enabling,
which runs 1 to 3 did (J1: -3.91 -> +3.98 deg, then +23.45 -> -0.39); see CLAUDE.md.
Raw videos stay on the Pi (`~/pick_tape_videos/test1.mjpeg`, `~/seek/run2/test2.mjpeg`,
`~/seek/run4/run4.mjpeg`, `~/seek/check.mjpeg`); `make_gif_test*.py` turn them into the GIFs
here, and `plot_test1.py` and `../test2-2026-10-16-seek/plot_test2_run4.py` make the figures.
