"""Index and decode frames of a raw MJPEG stream (concatenated JPEGs) + its .pts file."""
import numpy as np, cv2

def index(path):
    data = np.fromfile(path, dtype=np.uint8)
    # SOI markers FF D8 FF
    idx = np.flatnonzero((data[:-2] == 0xFF) & (data[1:-1] == 0xD8) & (data[2:] == 0xFF))
    return data, idx

def frame(data, idx, k):
    end = idx[k + 1] if k + 1 < len(idx) else len(data)
    return cv2.imdecode(data[idx[k]:end], cv2.IMREAD_COLOR)

def pts(path):
    t = []
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#"):
            t.append(float(line) / 1000.0)
    return np.array(t)
