"""Regression checks for the retrieval integrity boundary, using the real manifest."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.dataset_tools import image_path, retrieve_dataset


class RetrievalIntegrity(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.scratch = tempfile.TemporaryDirectory()
        self.temp = Path(self.scratch.name)
        self.config = json.loads((self.root / "data/dataset_config.json").read_text())

    def tearDown(self):
        self.scratch.cleanup()

    def test_paths_reject_traversal(self):
        for value in ["../secret", "/images/photo.jpg", "images/../labels.csv", "images\\photo.jpg"]:
            with self.assertRaises(ValueError):
                image_path(self.temp, value)

    def test_reject_nonempty_cache(self):
        (self.temp / "old.txt").write_text("stale")
        with self.assertRaisesRegex(ValueError, "empty"):
            retrieve_dataset(self.root / "data/dataset_config.json", self.temp, mode="local")

    def _tampered_source(self, transform):
        source = self.temp / "source"
        source.mkdir()
        text = (self.root / "data/labels.csv").read_text()
        (source / "labels.csv").write_text(transform(text))
        config = source / "dataset_config.json"
        config.write_text(json.dumps(self.config))
        return config

    def test_manifest_corruption_fails(self):
        config = self._tampered_source(lambda text: text + "\n")
        with self.assertRaisesRegex(ValueError, "Manifest SHA-256 mismatch"):
            retrieve_dataset(config, self.temp / "run", mode="local")

    def test_bad_image_hash_fails(self):
        # Actual tracked image bytes are copied; expected checksum is deliberately wrong.
        import shutil
        source = self.temp / "source"
        shutil.copytree(self.root / "data", source)
        import pandas as pd
        df = pd.read_csv(source / "labels.csv", dtype=str, keep_default_na=False)
        df.loc[0, "sha256"] = "0" * 64
        df.to_csv(source / "labels.csv", index=False)
        self.config["manifest_sha256"] = hashlib.sha256((source / "labels.csv").read_bytes()).hexdigest()
        config = source / "dataset_config.json"
        config.write_text(json.dumps(self.config))
        with self.assertRaisesRegex(ValueError, "Image SHA-256 mismatch"):
            retrieve_dataset(config, self.temp / "run", mode="local")

    def test_private_access_missing_fails(self):
        from unittest.mock import patch
        with patch("scripts.dataset_tools._credential", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "read access"):
                retrieve_dataset(self.root / "data/dataset_config.json", self.temp / "run", mode="github")


if __name__ == "__main__":
    unittest.main()
