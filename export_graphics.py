"""Backwards-compatible single-method entry points; use compare_exports for one full report."""
from comparison import DEFAULT_FORMATS, compare_exports


def save_with_pillow(image, base_path, dpi, formats=DEFAULT_FORMATS):
    return compare_exports(image, base_path, dpi, formats, methods=("pillow",))


def save_with_opencv(image, base_path, dpi, formats=DEFAULT_FORMATS):
    return compare_exports(image, base_path, dpi, formats, methods=("opencv",))


def save_with_matplotlib(figure, base_path, dpi, formats=DEFAULT_FORMATS):
    return compare_exports(figure, base_path, dpi, formats, methods=("matplotlib",))


def save_with_skimage(image, base_path, dpi, formats=DEFAULT_FORMATS):
    return compare_exports(image, base_path, dpi, formats, methods=("skimage",))


def save_with_imageio(image, base_path, dpi, formats=DEFAULT_FORMATS):
    return compare_exports(image, base_path, dpi, formats, methods=("imageio",))
