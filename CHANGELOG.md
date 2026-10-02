# Changelog

## 1.0.0 — 2026-10-03

First numbered release of the corrected export comparison.

- Render the supplied figure once at the target DPI on a white full-size canvas; share those pixels across all raster export APIs.
- Use Pillow's real encoder. Separate Matplotlib vector rendering from raster encoding and remove implicit 100-DPI scaling and tight cropping.
- Record actual dimensions, embedded DPI separately from calculated resolution, file sizes, elapsed time, pixel hashes, library versions, fonts and per-format failures in JSON and CSV.
- Continue after unavailable dependencies, unsupported formats or failed encoders; detect `cv2.imwrite(False)` and publish files only after validation.
- Isolate OpenCV encoding and raster inspection in timed subprocesses, recording native failures and the stage where they occurred.
- Preserve the existing single-method function names; add CLI output, format and DPI options plus focused regression tests.
