# Python Image Export Comparison

> Compare Python image export paths, file formats, and resolution metadata.

<p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-f59e0b?style=flat" alt="License: GPL-3.0"></a>
  <img src="https://img.shields.io/badge/Python-3-3776ab?style=flat&amp;logo=python&amp;logoColor=white" alt="Python: 3">
</p>

<p>
  <a href="#getting-started">Get started</a> · <a href="LICENSE">License</a>
</p>

This project compares different methods and libraries for exporting images in various formats and resolutions in Python.

## Description

This script demonstrates how to save images using different Python libraries:
1. Matplotlib export followed by Pillow-based DPI inspection (the function is named `save_with_pillow`)
2. OpenCV (cv2)
3. Matplotlib
4. scikit-image
5. imageio v3

It creates a sample sine wave plot and saves it in multiple formats using each method, allowing for a comparison of the output quality, file size, and supported formats.

## Prerequisites and Execution

Run from the repository directory. The function named `save_with_pillow` actually calls Matplotlib's `Figure.savefig`, then uses Pillow to inspect DPI metadata; it is not an independent Pillow encoder comparison.

The configured format lists describe attempted exports. Backend support can vary, and an export exception may stop the run before later methods execute.

## Getting Started

### Dependencies

* Python 3.x
* numpy
* matplotlib
* Pillow
* OpenCV
* scikit-image
* imageio

Install the required packages using:
```
pip install numpy matplotlib pillow opencv-python scikit-image imageio
```

### Executing program

* Run the main script:
```
python main.py
```


## Output

The script will create a `saved_images` directory with subdirectories for each method:

1. `method_1_pillow`
2. `method_2_opencv`
3. `method_3_matplotlib`
4. `method_4_skimage`
5. `method_5_imageio`

Each subdirectory will contain the sample image saved in various formats supported by that method.

### Formats Attempted by the Current Source

- **`save_with_pillow` (Matplotlib export)**: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff, webp
- **OpenCV**: jpeg, jpg, png, tif, tiff, webp, bmp, ppm
- **Matplotlib**: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff, webp
- **scikit-image**: jpeg, jpg, png, tif, tiff, webp, bmp, gif, ppm, pgm
- **imageio**: jpeg, jpg, png, tif, tiff, webp, bmp, gif, ppm, pgm

## Repository Structure

- [main.py](main.py): sample sine-wave figure and calls to all five methods at 300 DPI.
- [export_graphics.py](export_graphics.py): exports and DPI inspection.
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
