import csv
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from comparison import METHODS, compare_exports
from export_graphics import save_with_pillow


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.output = Path(self.folder.name)
        self.figure, axes = plt.subplots(figsize=(2, 1.5), dpi=83, facecolor="none")
        axes.plot([0, 1], [1, 0], color="red")
        self.canvas = self.figure.canvas
        # Another current figure must not replace the figure supplied to an encoder.
        self.other = plt.figure(figsize=(5, 4), dpi=200)

    def tearDown(self):
        plt.close(self.figure)
        plt.close(self.other)
        self.folder.cleanup()

    def test_five_png_paths_share_exact_pixels_and_report_real_dpi(self):
        report = compare_exports(self.figure, self.output, 120, formats=("png",))
        self.assertEqual({r["method"] for r in report["results"]}, set(METHODS))
        for result in report["results"]:
            self.assertEqual(result["status"], "ok", result)
            self.assertEqual(result["pixels"], [240, 180])
            self.assertEqual(result["input_pixel_sha256"], result["decoded_pixel_sha256"])
            self.assertGreater(result["bytes"], 0)
            self.assertGreaterEqual(result["seconds"], 0)
        opencv = next(r for r in report["results"] if r["method"] == "opencv")
        self.assertIsNone(opencv["dpi_metadata"])
        self.assertEqual(opencv["effective_dpi"], [120, 120])
        pillow = report["results"][0]
        self.assertAlmostEqual(pillow["dpi_metadata"][0], 120, delta=0.1)
        self.assertEqual(self.figure.dpi, 83)
        self.assertIs(self.figure.canvas, self.canvas)
        self.assertEqual(self.figure.get_facecolor()[3], 0)
        saved = json.loads((self.output / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["canvas"]["pixels"], [240, 180])
        self.assertTrue(saved["environment"]["font_files_sha256"])
        with (self.output / "results.csv").open(encoding="utf-8", newline="") as stream:
            self.assertEqual(len(list(csv.DictReader(stream))), 5)

    def test_pillow_does_not_call_figure_savefig(self):
        with patch.object(self.figure, "savefig", side_effect=AssertionError("wrong encoder")):
            report = save_with_pillow(self.figure, self.output, 120, formats=("png",))
        self.assertEqual(report["results"][0]["status"], "ok")

    def test_svg_keeps_full_physical_canvas_and_unsupported_formats_do_not_abort(self):
        with matplotlib.rc_context({"savefig.bbox": "tight"}):
            report = compare_exports(self.figure, self.output, 120, formats=("unknown", "svg", "png"), methods=("matplotlib", "pillow"))
        svg = next(r for r in report["results"] if r["format"] == "svg" and r["method"] == "matplotlib")
        self.assertEqual(svg["status"], "ok")
        self.assertEqual(svg["kind"], "vector")
        self.assertIsNone(svg["pixels"])
        root = ElementTree.parse(self.output / svg["path"]).getroot()
        self.assertEqual((root.attrib["width"], root.attrib["height"]), ("144pt", "108pt"))
        self.assertTrue(all(r["status"] == "unsupported" for r in report["results"] if r["format"] == "unknown"))
        self.assertTrue(all(r["status"] == "ok" for r in report["results"] if r["format"] == "png"))
        self.assertEqual(self.figure.dpi, 83)

    def test_opencv_false_preserves_previous_file_and_other_encoders_continue(self):
        previous = self.output / "method_2_opencv" / "sample_image.png"
        previous.parent.mkdir()
        previous.write_bytes(b"previous successful run")
        original = subprocess.run
        def fail_encoder(command, **kwargs):
            if Path(command[1]).name == "opencv_worker.py":
                return subprocess.CompletedProcess(command, 1, "", "cv2.imwrite returned False")
            return original(command, **kwargs)
        with patch("comparison.subprocess.run", side_effect=fail_encoder):
            report = compare_exports(self.figure, self.output, 120, formats=("png",), methods=("opencv", "pillow"))
        failed, passed = report["results"]
        self.assertEqual(failed["status"], "error")
        self.assertIn("returned False", failed["error"])
        self.assertIsNone(failed["path"])
        self.assertEqual(passed["status"], "ok")
        self.assertEqual(previous.read_bytes(), b"previous successful run")
        self.assertEqual(list(previous.parent.iterdir()), [previous])

    def test_native_decoder_exit_is_reported_and_next_format_runs(self):
        original = subprocess.run
        def fail_tiff_decoder(command, **kwargs):
            if Path(command[1]).name == "inspect_raster.py" and command[-1] == "tiff":
                return subprocess.CompletedProcess(command, 1, "", "decoder stopped")
            return original(command, **kwargs)
        with patch("comparison.subprocess.run", side_effect=fail_tiff_decoder):
            report = compare_exports(self.figure, self.output, 120, formats=("tiff", "png"), methods=("pillow",))
        self.assertEqual(report["results"][0]["failure_stage"], "inspect")
        self.assertEqual(report["results"][0]["status"], "error")
        self.assertEqual(report["results"][1]["status"], "ok")

    def test_worker_rejects_opencv_false(self):
        import numpy as np
        from opencv_worker import encode
        payload = self.output / "input.npy"
        np.save(payload, np.zeros((4, 4, 3), dtype=np.uint8))
        with patch("cv2.imwrite", return_value=False), self.assertRaisesRegex(OSError, "returned False"):
            encode(str(payload), str(self.output / "failed.png"))

    def test_grayscale_pgm_closes_memory_map_before_publishing(self):
        report = compare_exports(self.figure, self.output, 120, formats=("pgm",), methods=("pillow",))
        result = report["results"][0]
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result["input_pixel_sha256"], result["decoded_pixel_sha256"])
        self.assertEqual(result["warnings"], [])

    def test_missing_optional_dependency_is_reported_without_losing_other_results(self):
        import comparison
        original = comparison._raster_writer
        def missing_cv2(method):
            if method == "opencv":
                raise ImportError("fixture missing dependency")
            return original(method)
        with patch("comparison._raster_writer", side_effect=missing_cv2):
            report = compare_exports(self.figure, self.output, 120, formats=("png",), methods=("opencv", "pillow"))
        self.assertEqual(report["results"][0]["status"], "unavailable")
        self.assertEqual(report["results"][1]["status"], "ok")


if __name__ == "__main__":
    unittest.main()
