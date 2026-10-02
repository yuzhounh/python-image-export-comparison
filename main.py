import argparse
from collections import Counter
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from comparison import DEFAULT_FORMATS, compare_exports

def create_sample_image():
    """Create a sample image for testing."""
    x = np.linspace(0, 2 * np.pi, 100)
    y = np.sin(x)
    figure, axes = plt.subplots(figsize=(8, 6))
    axes.plot(x, y)
    axes.set(title="Sample Sine Wave", xlabel="x", ylabel="sin(x)")
    return figure

def main():
    parser = argparse.ArgumentParser(description="Compare export APIs with one shared raster canvas.")
    parser.add_argument("--output", type=Path, default=Path("saved_images"))
    parser.add_argument("--dpi", type=float, default=300)
    parser.add_argument("--formats", nargs="+", default=DEFAULT_FORMATS)
    parser.add_argument("--version", action="version", version=Path(__file__).with_name("VERSION").read_text().strip())
    args = parser.parse_args()
    figure = create_sample_image()
    try:
        report = compare_exports(figure, args.output, args.dpi, args.formats)
    finally:
        plt.close(figure)
    print(dict(Counter(result["status"] for result in report["results"])))
    print(f"Measurements: {args.output / 'results.json'} and results.csv")
    return 0 if any(result["status"] == "ok" for result in report["results"]) else 1

if __name__ == "__main__":
    raise SystemExit(main())
