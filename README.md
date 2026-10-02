# Python Image Export Comparison

> Compare Python image export paths, file formats, and resolution metadata.

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-f59e0b?style=flat" alt="License: GPL-3.0"></a>
  <img src="https://img.shields.io/badge/Python-3-3776ab?style=flat&amp;logo=python&amp;logoColor=white" alt="Python: 3">
</p>

<p>
  <a href="#getting-started">Get started</a> · <a href="LICENSE">License</a>
</p>

Version **1.0.0** compares image export APIs using a shared raster canvas and a separate vector-rendering path. Download the source and a measured sample run from [Releases](https://github.com/yuzhounh/python-image-export-comparison/releases/latest).

## Description

This script demonstrates how to save images using different Python libraries:
1. Pillow's `Image.save` encoder
2. OpenCV (cv2)
3. Matplotlib
4. scikit-image
5. imageio v3

The supplied Figure is rendered once with Agg at the requested DPI, on a white background, without resizing or tight cropping. All raster paths receive the same RGB pixels; PGM uses one shared grayscale conversion. The default 8 × 6 inch figure at 300 DPI produces 2400 × 1800 pixels. A different current pyplot figure cannot replace the supplied figure.

PDF, SVG, SVGZ, EPS, PS and PGF use Matplotlib's full-size `Figure.savefig` path and are classified separately as vector output. Their timings include rendering; raster timings cover encoding only, with the common raster-render time recorded separately. Embedded images or rasterized artists can still occur in vector documents.

## Prerequisites and Execution

Run from the repository directory. Pillow now calls its own encoder. These are **API paths, not five independent codecs**: [Matplotlib's raster imsave](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.imsave.html) uses Pillow, imageio is explicitly configured with its [Pillow plugin](https://imageio.readthedocs.io/en/stable/_autosummary/imageio.plugins.pillow.html), and scikit-image uses its imageio plugin. The report names these paths and records the installed versions.

Format support depends on installed libraries and tools. A failed export is recorded and later exports continue; OpenCV returning `False` is a failure. Missing optional dependencies are reported per method. Files are staged and inspected before replacing an output; a failed attempt does not overwrite a previous successful file. Use a new output directory for each run and rely on successful entries in the report, since older files may remain in a reused directory.

OpenCV encoding and raster inspection run in separate processes with 60-second timeouts, so a native crash in either step is recorded without ending the comparison. Successful OpenCV times exclude process startup and pixel transfer; failed worker timings explicitly include that overhead. `failure_stage` distinguishes encoding, inspection and publication failures. Other encoders run in the main process.

## Getting Started

### Dependencies

* Python 3.10+
* numpy
* matplotlib
* Pillow
* OpenCV
* scikit-image
* imageio

Install the required packages using:
```
python -m pip install -r requirements.txt
```

### Executing program

* Run the main script:
```
python main.py
python main.py --formats png svg unknown --dpi 120 --output saved_images/smoke
python main.py --version
python -m unittest -v test_comparison
```


## Output

The script will create a `saved_images` directory with subdirectories for each method:

1. `method_1_pillow`
2. `method_2_opencv`
3. `method_3_matplotlib`
4. `method_4_skimage`
5. `method_5_imageio`

Each subdirectory contains successful image exports. `results.json` includes canvas dimensions, common render time, Python/library versions and font-file hashes. `results.csv` contains the per-export measurements: method/backend, raster or vector, status, file size, encoding time, actual decoded pixel dimensions, color mode, warnings and failure reason.

`dpi_metadata` is read from the file; `null` means no DPI metadata was found. `effective_dpi` is calculated as decoded pixels divided by figure inches and is explicitly a different measurement. OpenCV, scikit-image and imageio do not receive a DPI metadata option here. Pillow and Matplotlib do; format support still varies. A missing DPI tag does not imply missing pixels. Vector files have no single pixel size or intrinsic DPI, so these fields are null.

Input and decoded pixel SHA-256 values allow exact comparisons for lossless images. JPEG/WebP defaults, GIF palette conversion and other format settings may differ between APIs. A single run's time or file size is not a controlled codec benchmark or proof of visual quality; no library is ranked as sharper. Library load time and output-file inspection are outside the encoding timer.

### Formats Attempted by the Current Source

- All five APIs attempt PNG, JPEG/JPG, TIFF/TIF, WebP, BMP, GIF, PPM and PGM from the shared pixels. Unsupported encoders are recorded rather than counted as successes.
- Matplotlib additionally attempts PDF, SVG/SVGZ, EPS, PS and PGF. PGF may require an installed TeX engine; an unavailable engine produces a recorded error.
- Vector requests on raster APIs are marked unsupported; raster-in-PDF is not treated as vector output. Raw/RGBA byte streams are marked unsupported because they are not self-describing image files.
- Custom `--formats` selections are recorded for every method, including unknown formats. Exit status is 1 if no output succeeded; inspect the report for partial failures even when exit status is 0.

## Repository Structure

- [main.py](main.py): sample sine-wave figure and configurable CLI.
- [comparison.py](comparison.py): shared rendering, encoding and JSON/CSV measurements.
- [opencv_worker.py](opencv_worker.py) and [inspect_raster.py](inspect_raster.py): isolated encoding and decoding helpers.
- [export_graphics.py](export_graphics.py): original single-method names retained as convenience wrappers; each call writes its own report. Use `compare_exports` for one combined report.
- [test_comparison.py](test_comparison.py): pixel equivalence, supplied-figure isolation, vector dimensions, encoder failures and optional-dependency handling.
- [CHANGELOG.md](CHANGELOG.md): version history.
- `saved_images/`: generated output directory.

## Acknowledgments

* [Matplotlib](https://matplotlib.org/)
* [Pillow](https://python-pillow.org/)
* [OpenCV](https://opencv.org/)
* [scikit-image](https://scikit-image.org/)
* [imageio](https://imageio.readthedocs.io/)

## License

See the existing [GNU General Public License, version 3](LICENSE).

## Contact

Jing Wang: wangjing@xynu.edu.cn

Project Link: [https://github.com/yuzhounh/python-image-export-comparison](https://github.com/yuzhounh/python-image-export-comparison)
