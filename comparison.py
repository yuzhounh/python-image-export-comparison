"""Compare export APIs using one shared raster and a separate vector path."""
from __future__ import annotations

import csv
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import math
import platform
import subprocess
import sys
import tempfile
import time
import warnings
from pathlib import Path

import matplotlib as mpl
from matplotlib import font_manager
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.image import imsave
from matplotlib.text import Text
import numpy as np
from PIL import Image

METHODS = ("pillow", "opencv", "matplotlib", "skimage", "imageio")
VECTOR_FORMATS = {"pdf", "svg", "svgz", "eps", "ps", "pgf"}
RASTER_FORMATS = {"png", "jpeg", "jpg", "tif", "tiff", "webp", "bmp", "gif", "ppm", "pgm"}
DEFAULT_FORMATS = ("png", "jpeg", "jpg", "tif", "tiff", "webp", "bmp", "gif", "ppm", "pgm",
                   "pdf", "svg", "svgz", "eps", "ps", "pgf", "raw", "rgba")
ENGINES = {
    "pillow": "PIL.Image.save",
    "opencv": "cv2.imwrite",
    "matplotlib": "matplotlib.image.imsave (Pillow for raster formats)",
    "skimage": "skimage.io.imsave (imageio plugin)",
    "imageio": "imageio.v3.imwrite (Pillow plugin)",
}


def render_raster(figure, dpi):
    """Render the supplied figure, without gcf(), resampling or tight cropping."""
    if not math.isfinite(dpi) or dpi <= 0:
        raise ValueError("dpi must be finite and positive")
    original = figure.canvas, figure.dpi, figure.get_facecolor()
    started = time.perf_counter()
    try:
        figure.set_dpi(dpi)
        figure.set_facecolor("white")
        canvas = FigureCanvasAgg(figure)
        canvas.draw()
        rgba = Image.fromarray(np.asarray(canvas.buffer_rgba()).copy())
        rgb = np.asarray(Image.alpha_composite(Image.new("RGBA", rgba.size, "white"), rgba).convert("RGB")).copy()
    finally:
        figure.set_dpi(original[1])
        figure.set_facecolor(original[2])
        figure.set_canvas(original[0])
    rgb.setflags(write=False)
    return rgb, time.perf_counter() - started


def _raster_writer(method):
    # Load optional dependencies before timing an export, not at module import.
    if method == "pillow":
        def write(path, pixels, fmt, dpi):
            image_format = {"jpg": "JPEG", "tif": "TIFF", "pgm": "PPM"}.get(fmt, fmt.upper())
            Image.fromarray(pixels).save(path, format=image_format, dpi=(dpi, dpi))
        return write
    if method == "opencv":
        if importlib.util.find_spec("cv2") is None:
            raise ImportError("OpenCV is not installed")
        def write(path, pixels, fmt, dpi):
            payload = None
            try:
                with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".npy", delete=False) as stream:
                    payload = Path(stream.name)
                    np.save(stream, pixels, allow_pickle=False)
                completed = subprocess.run([sys.executable, str(Path(__file__).with_name("opencv_worker.py")),
                                            str(payload), str(path)], capture_output=True, text=True, timeout=60)
                if completed.returncode != 0:
                    raise OSError(f"OpenCV process exited {completed.returncode}: {completed.stderr.strip()}")
                return json.loads(completed.stdout)["seconds"]
            finally:
                if payload is not None:
                    payload.unlink(missing_ok=True)
        return write
    if method == "matplotlib":
        def write(path, pixels, fmt, dpi):
            # imsave applies a colormap to 2D data; PGM needs a genuine grayscale encoder.
            if fmt == "pgm":
                raise ValueError("Matplotlib imsave does not preserve a grayscale PGM array")
            imsave(path, pixels, format={"jpg": "jpeg", "tif": "tiff"}.get(fmt, fmt), dpi=dpi, origin="upper")
        return write
    if method == "skimage":
        io = importlib.import_module("skimage.io")
        return lambda path, pixels, fmt, dpi: io.imsave(str(path), pixels, plugin="imageio", check_contrast=False)
    iio = importlib.import_module("imageio.v3")
    return lambda path, pixels, fmt, dpi: iio.imwrite(path, pixels, plugin="pillow")


def environment(figure):
    versions = {}
    for name in ("numpy", "matplotlib", "PIL", "cv2", "skimage", "imageio"):
        try:
            if name == "cv2":
                versions[name] = {}
                for package in ("opencv-python-headless", "opencv-python", "opencv-contrib-python-headless", "opencv-contrib-python"):
                    try:
                        versions[name][package] = importlib.metadata.version(package)
                    except importlib.metadata.PackageNotFoundError:
                        pass
            else:
                versions[name] = importlib.import_module(name).__version__
        except Exception as error:
            versions[name] = f"unavailable: {type(error).__name__}: {error}"
    fonts = {}
    for text in figure.findobj(match=Text):
        if text.get_text():
            path = Path(font_manager.findfont(text.get_fontproperties()))
            fonts[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"python": platform.python_version(), "platform": platform.platform(),
            "libraries": versions, "font_files_sha256": fonts, "text_usetex": bool(mpl.rcParams["text.usetex"])}


def compare_exports(figure, base_path, dpi=300, formats=DEFAULT_FORMATS, methods=METHODS):
    """Return measurements and write JSON/CSV; individual failures do not abort the run."""
    methods, formats = tuple(methods), tuple(dict.fromkeys(fmt.lower().lstrip(".") for fmt in formats))
    if any(method not in METHODS for method in methods):
        raise ValueError("Unknown method")
    if any(not fmt.isalnum() for fmt in formats):
        raise ValueError("Formats must be simple file extensions")
    output = Path(base_path)
    output.mkdir(parents=True, exist_ok=True)
    rgb, render_seconds = render_raster(figure, float(dpi))
    gray = np.asarray(Image.fromarray(rgb).convert("L"))
    width, height = rgb.shape[1], rgb.shape[0]
    inches = [float(value) for value in figure.get_size_inches()]
    report = {"schema_version": 1, "canvas": {"inches": inches, "target_dpi": dpi,
              "pixels": [width, height], "background": "white", "render_seconds": render_seconds,
              "rgb_sha256": hashlib.sha256(rgb.tobytes()).hexdigest()},
              "environment": environment(figure), "results": []}
    for method in methods:
        folder = output / f"method_{METHODS.index(method) + 1}_{method}"
        folder.mkdir(exist_ok=True)
        try:
            writer, dependency_error = _raster_writer(method), None
        except Exception as error:
            writer, dependency_error = None, f"{type(error).__name__}: {error}"
        for fmt in formats:
            vector = fmt in VECTOR_FORMATS
            pixels = gray if fmt == "pgm" else rgb
            result = {"method": method, "format": fmt, "kind": "vector" if vector else "raster",
                      "engine": "Figure.savefig" if vector and method == "matplotlib" else ENGINES[method],
                      "status": "unsupported", "path": None, "bytes": None, "pixels": None,
                      "dpi_metadata": None, "effective_dpi": None, "color_mode": None,
                      "seconds": None, "timing_scope": "render_and_encode" if vector else "encode_only",
                      "input_pixel_sha256": None if vector else hashlib.sha256(pixels.tobytes()).hexdigest(),
                      "decoded_pixel_sha256": None, "warnings": [], "error": None, "failure_stage": None}
            report["results"].append(result)
            if vector and method != "matplotlib":
                result["error"] = "Vector comparison uses Figure.savefig; raster-in-PDF is not vector output"
                continue
            if fmt not in VECTOR_FORMATS | RASTER_FORMATS:
                result["error"] = "Unsupported image format (raw/rgba buffers are not self-describing images)"
                continue
            if dependency_error:
                result.update(status="unavailable", error=dependency_error)
                continue
            destination = folder / f"sample_image.{fmt}"
            # Publish only fully written and inspected files; retain any previous result on failure.
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=folder, suffix="." + fmt, delete=False) as stream:
                    temporary = Path(stream.name)
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    result["failure_stage"] = "encode"
                    started = time.perf_counter()
                    encoder_seconds = None
                    try:
                        if vector:
                            with mpl.rc_context({"savefig.bbox": None, "savefig.transparent": False}):
                                figure.savefig(temporary, format=fmt, dpi=dpi, bbox_inches=None,
                                               facecolor="white", transparent=False)
                        else:
                            encoder_seconds = writer(temporary, pixels, fmt, dpi)
                    finally:
                        result["seconds"] = encoder_seconds if encoder_seconds is not None else time.perf_counter() - started
                        if method == "opencv" and encoder_seconds is None:
                            result["timing_scope"] = "failed_worker_including_startup"
                        result["warnings"] = [str(item.message) for item in caught]
                if temporary.stat().st_size == 0:
                    raise OSError("Encoder produced an empty file")
                if not vector:
                    result["failure_stage"] = "inspect"
                    inspected = subprocess.run([sys.executable, str(Path(__file__).with_name("inspect_raster.py")),
                                                str(temporary), fmt], capture_output=True, text=True, timeout=60)
                    if inspected.returncode != 0:
                        raise OSError(f"Raster inspection process exited {inspected.returncode}: {inspected.stderr.strip()}")
                    result.update(json.loads(inspected.stdout))
                    result["effective_dpi"] = [result["pixels"][0] / inches[0], result["pixels"][1] / inches[1]]
                    if result["pixels"] != [width, height]:
                        raise ValueError(f"Encoder changed canvas dimensions to {result['pixels']}")
                result["bytes"] = temporary.stat().st_size
                result["failure_stage"] = "publish"
                temporary.replace(destination)
                result.update(status="ok", path=destination.relative_to(output).as_posix(), failure_stage=None)
            except Exception as error:
                result.update(status="error", error=f"{type(error).__name__}: {error}")
            finally:
                if temporary is not None:
                    try:
                        temporary.unlink(missing_ok=True)
                    except OSError as error:
                        result["warnings"].append(f"Temporary file cleanup failed: {error}")
    (output / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if report["results"]:
        with (output / "results.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=report["results"][0].keys())
            writer.writeheader()
            for result in report["results"]:
                writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, tuple, dict)) else value
                                 for key, value in result.items()})
    return report
