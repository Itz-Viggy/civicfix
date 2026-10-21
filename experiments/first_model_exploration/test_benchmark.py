"""Deterministic correctness checks; synthetic fixtures are never model evidence."""
from copy import deepcopy
import json
import tempfile
from pathlib import Path
import unittest

import pandas as pd

from .benchmark import CATEGORIES, HERE, classify_scores, evaluate, validate_split, write_new, assert_one_change


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.truth = pd.DataFrame({"image_id": ["a", "b", "c"],
                                   "issue_type": [CATEGORIES[0], CATEGORIES[0], CATEGORIES[1]]})
        self.rows = [dict(image_id="a", status="success", predicted_category=CATEGORIES[0], simulated=False, latency_seconds=1.),
                     dict(image_id="b", status="error", latency_seconds=2.),
                     dict(image_id="c", status="success", predicted_category=CATEGORIES[0], simulated=False, latency_seconds=3.)]

    def test_failed_attempt_is_not_dropped(self):
        result = evaluate(self.rows, self.truth)
        self.assertEqual((result["correct"], result["attempted_n"], result["failures"]), (1, 3, 1))
        self.assertEqual(result["accuracy"], 1/3)
        self.assertEqual(result["confusion_matrix"][0][5], 1)
        self.assertEqual(result["per_class"][0]["precision"], .5)
        self.assertEqual(result["per_class"][0]["recall"], .5)
        self.assertEqual(result["macro_f1"], .1)

    def test_coverage_and_simulation_rejected(self):
        for rows in [self.rows[:2], [self.rows[0]]*3,
                     [{**self.rows[0], "simulated": True}, *self.rows[1:]]]:
            with self.assertRaises(ValueError):
                evaluate(rows, self.truth)


class SplitTests(unittest.TestCase):
    def setUp(self):
        self.manifest = pd.DataFrame(dict(image_id=["a", "b"], scene_id=["one", "two"], sha256=["x", "y"]))
        self.split = dict(status="verified", source_sha256="source", development_ids=["a"], training_ids=[], held_out_ids=["b"])

    def test_development_selection_preserves_holdout(self):
        self.assertEqual(validate_split(self.manifest, self.split).image_id.tolist(), ["a"])

    def test_missing_overlap_unknown_and_unverified_rejected(self):
        for change in [dict(status="blocked"), dict(held_out_ids=[]), dict(held_out_ids=["a", "b"]), dict(development_ids=["unknown"])]:
            with self.assertRaises(ValueError):
                validate_split(self.manifest, {**self.split, **change})

    def test_scene_or_identical_bytes_cannot_cross_split(self):
        for column in ["scene_id", "sha256"]:
            manifest=self.manifest.copy();manifest[column]="same"
            with self.assertRaises(ValueError):
                validate_split(manifest, self.split)


class ConfigurationTests(unittest.TestCase):
    def test_ties_and_invalid_scores(self):
        result=classify_scores([.2]*5)
        self.assertEqual(result["predicted_category"], CATEGORIES[0])
        self.assertEqual(result["top1_margin"], 0)
        for bad in [[.1]*4, [float("nan")]*5, [float("inf")]*5, [2.]*5]:
            with self.assertRaises(ValueError):classify_scores(bad)

    def test_first_results_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"config.json";write_new(p,{"first":True})
            with self.assertRaises(FileExistsError):write_new(p,{"first":False})
            self.assertTrue(json.loads(p.read_text())["first"])

    def test_one_change_guard_rejects_other_model_split_or_metric_changes(self):
        base=dict(model="ViT-B-32", development_ids=["a"], score_method="cosine", prompts={"v":1})
        revision={**base,"prompts":{"v":2}}
        assert_one_change(base,revision)
        for change in [dict(model="other"),dict(development_ids=["b"]),dict(score_method="softmax")]:
            with self.assertRaises(ValueError):assert_one_change(base,{**revision,**change})


if __name__ == "__main__":
    unittest.main()
