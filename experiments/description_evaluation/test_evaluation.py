"""Synthetic harness tests; none of these fixtures count as model evidence."""
from copy import deepcopy
import json
import tempfile
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from .contracts import (HERE, PROTOCOL, assert_one_change, digest, exact_rows, paired,
                        parse_payload, sha256, summarize, write_new)
from .run import validate_selection


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.payload = dict(category_suggestion=None, visible_observations=["Water is visible"],
                            description="Water is visible near a pavement opening.", outcome="unclear",
                            clarification_reasons=["Source of water cannot be confirmed"])
        self.cfg = dict(run_id="fixture", image_ids=["a", "b"], rubric_sha256=sha256(HERE / "rubric.json"))
        self.a = dict(self.payload, image_id="a", run_id="fixture", status="success", error_status=None,
                      latency_seconds=1., first_image_in_process=True, identity_sha256="a"*64,
                      generation_tokens=40, prompt_tokens=100, peak_memory_gb=3.)
        self.b = dict(self.a, image_id="b", status="error", error_status="RuntimeError", description="",
                      visible_observations=[], latency_seconds=3., first_image_in_process=False)
        self.scores = [dict(image_id="a", run_id="fixture", clip_cosine=.2, score_protocol=PROTOCOL,
                            status="success", error_status=None, token_occupancy=12),
                       dict(image_id="b", run_id="fixture", clip_cosine=None, score_protocol=PROTOCOL,
                            status="skipped", error_status="generation_error_or_abstention", token_occupancy=None)]
        self.review = dict(image_id="a", run_id="fixture", generation_sha256=digest(self.a),
                           rubric_sha256=self.cfg["rubric_sha256"], unsupported_claim_count=0, unsupported_claims=[],
                           clarity=2, specificity=2, missing_important_visible_fact=False, notes="Fixture only",
                           reviewer=dict(identity="test", type="agent_visual", method="synthetic fixture", reviewed_utc="fixture"))

    def test_schemas_and_frozen_selection(self):
        for schema in json.loads((HERE / "schemas.json").read_text()).values():
            Draft202012Validator.check_schema(schema)
        selection = validate_selection()
        self.assertEqual(len(selection["image_ids"]), 20)

    def test_payload_contract_no_silent_repairs(self):
        self.assertEqual(parse_payload(json.dumps(self.payload)), self.payload)
        self.assertEqual(parse_payload("```json\n"+json.dumps(self.payload)+"\n```"), self.payload)
        for value in [dict(self.payload, category_suggestion="other"), dict(self.payload, label="hint"),
                      dict(self.payload, visible_observations="water"), dict(self.payload, outcome="passing"),
                      dict(self.payload, description="One. Two. Three."),
                      dict(self.payload, description="word "*61),
                      dict(self.payload, description="", outcome="supported")]:
            with self.assertRaises(ValueError):
                parse_payload(json.dumps(value))
        with self.assertRaises(ValueError):
            parse_payload("Here is a repaired caption")

    def test_failures_remain_in_attempts_separate_from_factuality_and_scores(self):
        result = summarize(self.cfg, [self.a, self.b], self.scores, [self.review])
        self.assertEqual((result["attempted"], result["generated"], result["generation_failures"]), (2,1,1))
        self.assertEqual((result["zero_unsupported_claims"], result["reviewed"], result["score_valid_n"]), (1,1,1))
        self.assertEqual(result["mean_clip_cosine"], .2)
        self.assertEqual(result["generation_latency_seconds"]["mean"], 2.)
        self.assertAlmostEqual(result["generation_latency_seconds"]["p95"], 2.9)

    def test_abstention_is_not_a_factuality_pass(self):
        b = dict(self.b, status="success", error_status=None)
        result = summarize(self.cfg, [self.a, b], self.scores, [self.review])
        self.assertEqual((result["generated"], result["abstentions"], result["reviewed"]), (1,1,1))
        with self.assertRaises(ValueError):
            summarize(self.cfg, [self.a,b], self.scores, [dict(self.review, image_id="b", generation_sha256=digest(b))])

    def test_review_is_bound_to_output_and_rubric(self):
        for change in [dict(generation_sha256="b"*64), dict(rubric_sha256="b"*64), dict(run_id="foreign")]:
            with self.assertRaises(ValueError):
                summarize(self.cfg, [self.a,self.b], self.scores, [dict(self.review, **change)])

    def test_identity_coverage_and_invalid_scores_rejected(self):
        for rows in [[self.a], [self.a,self.a], [self.a,dict(self.b,run_id="other")]]:
            with self.assertRaises(ValueError):
                exact_rows(rows, self.cfg["image_ids"], "fixture")
        from jsonschema import ValidationError
        with self.assertRaises(ValidationError):
            summarize(self.cfg,[self.a,self.b],[dict(self.scores[0],clip_cosine=2),self.scores[1]],[])

    def test_immutable_first_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"configuration.json"
            write_new(p,{"first":True})
            with self.assertRaises(FileExistsError):
                write_new(p,{"first":False})

    def test_controlled_change(self):
        base=dict(self.cfg, settings={"model":"qwen","temperature":0}, prompt={"base":"fixed", "feature":""},
                  prompt_version="v1", score_protocol=PROTOCOL)
        new=dict(base, run_id="revision", prompt={"base":"fixed", "feature":"one feature"},prompt_version="v2")
        assert_one_change(base,new)
        for change in [dict(settings={"model":"other"}),dict(image_ids=["other"]),dict(score_protocol="official_clipscore"),
                       dict(prompt={"base":"changed", "feature":"also changed"})]:
            with self.assertRaises(ValueError):
                assert_one_change(base,dict(new,**change))

    def test_paired_regression_is_independent_of_similarity_and_failures_remain(self):
        base = dict(self.cfg, prompt={"base":"fixed", "feature":""})
        revised = dict(base, run_id="revised", prompt={"base":"fixed", "feature":"one self-check"})
        revised_rows = [dict(self.a,run_id="revised"), dict(self.a,image_id="b",run_id="revised")]
        revised_reviews = [dict(self.review,run_id="revised",unsupported_claim_count=1),
                           dict(self.review,image_id="b",run_id="revised")]
        revised_scores = [dict(self.scores[0],run_id="revised",clip_cosine=.9),
                          dict(self.scores[0],image_id="b",run_id="revised")]
        result = paired(base,revised,[self.a,self.b],revised_rows,[self.review],revised_reviews,self.scores,revised_scores)
        self.assertEqual(len(result),2)
        self.assertTrue(result[0]["factuality_regression"])
        self.assertAlmostEqual(result[0]["clip_cosine_delta"], .7)
        self.assertEqual(result[1]["baseline_status"],"error")
        self.assertFalse(result[1]["both_reviewed"])
        self.assertIsNone(result[1]["clip_cosine_delta"])


if __name__ == "__main__":
    unittest.main()
