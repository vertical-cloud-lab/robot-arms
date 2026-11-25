"""Save every new frame of one camera from AMP's robot server (api/frame/{cam}) as a JPEG.

python recorder.py URL CAMERA OUTDIR
"""

import sys
import time
import urllib.request
from pathlib import Path

url, cam, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
last, n = None, 0
while True:
    try:
        with urllib.request.urlopen(f"{url}/api/frame/{cam}", timeout=5) as r:  # noqa: S310
            seq = r.headers.get("X-Frame-Seq")
            data = r.read()
        if seq != last:
            (out / f"{n:05d}.jpg").write_bytes(data)
            last, n = seq, n + 1
    except Exception:  # noqa: BLE001
        time.sleep(0.5)
    time.sleep(0.04)
