"""Isolated OpenCV codec process: avoid shared native-library conflicts."""
import json
import sys
import time


def encode(input_path, output_path):
    import cv2
    import numpy as np
    pixels = np.load(input_path, allow_pickle=False)
    started = time.perf_counter()
    encoded = cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR) if pixels.ndim == 3 else pixels
    if not cv2.imwrite(output_path, encoded):
        raise OSError("cv2.imwrite returned False")
    return time.perf_counter() - started


if __name__ == "__main__":
    try:
        seconds = encode(sys.argv[1], sys.argv[2])
        print(json.dumps({"seconds": seconds}))
    except Exception as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
