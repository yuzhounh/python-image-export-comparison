"""Inspect in a clean process so native decoder failures cannot abort a run."""
import hashlib
import json
import sys
from PIL import Image


def inspect(path, grayscale=False):
    image = Image.open(path)
    try:
        image.load()
        dpi = image.info.get("dpi")
        return {"pixels": list(image.size), "color_mode": image.mode,
                "dpi_metadata": [float(value) for value in dpi] if dpi else None,
                "decoded_pixel_sha256": hashlib.sha256(image.convert("L" if grayscale else "RGB").tobytes()).hexdigest()}
    finally:
        image.close()  # Release mapped PGM/PPM data before the caller renames the file.


if __name__ == "__main__":
    try:
        print(json.dumps(inspect(sys.argv[1], sys.argv[2] == "pgm")))
    except Exception as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
