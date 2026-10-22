"""Versioned contracts, strict identity gates and failure-aware evaluation."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from statistics import mean, median
from typing import Protocol

from PIL import Image
from experiments.first_model_exploration.benchmark import digest, write_new
from scripts.dataset_tools import CATEGORIES, sha256

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROTOCOL = "openclip-vit-b32-openai-native-raw-cosine-v1"
FIELDS = {"category_suggestion", "visible_observations", "description", "outcome", "clarification_reasons"}


class DescriptionGenerator(Protocol):
    """Only sanitized pixels and a fixed prompt enter an interchangeable adapter."""

    metadata: dict

    def generate(self, image: Image.Image, prompt: str) -> str: ...


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def validate_payload(value):
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError("Generator must return exactly the five payload fields")
    if value["category_suggestion"] not in [None, *CATEGORIES]:
        raise ValueError("Unknown category")
    for key in ("visible_observations", "clarification_reasons"):
        if not isinstance(value[key], list) or any(not isinstance(x, str) or not x.strip() for x in value[key]):
            raise ValueError(f"Invalid {key}")
    if not isinstance(value["description"], str) or len(value["description"].split()) > 60:
        raise ValueError("Description must be a string of at most 60 words")
    if len(re.findall(r"[.!?](?:\s|$)", value["description"])) > 2:
        raise ValueError("Description must contain at most two sentences")
    if value["outcome"] not in ("supported", "unclear", "unsupported"):
        raise ValueError("Invalid outcome")
    if not value["description"].strip() and value["outcome"] == "supported":
        raise ValueError("An empty description cannot be supported")
    return value


def parse_payload(text):
    # Permit a single JSON Markdown fence, never repair or regenerate a result.
    text = text.strip()
    if text.startswith("```json\n") and text.endswith("\n```"):
        text = text[8:-4]
    return validate_payload(json.loads(text))


def exact_rows(rows, ids, run_id):
    actual = [r["image_id"] for r in rows]
    if len(actual) != len(set(actual)) or set(actual) != set(ids):
        raise ValueError("Missing, duplicate or foreign image IDs")
    if any(r["run_id"] != run_id for r in rows):
        raise ValueError("Foreign run identity")
    return {r["image_id"]: r for r in rows}


def percentile(values, q):
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * q
    lo = int(position)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def summarize(config, generations, scores, reviews):
    ids, run_id = config["image_ids"], config["run_id"]
    generated = exact_rows(generations, ids, run_id)
    scored = exact_rows(scores, ids, run_id)
    review_ids = [r["image_id"] for r in reviews]
    if len(set(review_ids)) != len(review_ids) or not set(review_ids) <= set(ids):
        raise ValueError("Duplicate or foreign review")
    from jsonschema import validate
    schemas = json.loads((HERE / "schemas.json").read_text())
    for row in generations:
        validate(row, schemas["generation"])
        if not math.isfinite(row["latency_seconds"]):
            raise ValueError("Invalid generation latency")
        if row["status"] == "success":
            validate_payload({k: row[k] for k in FIELDS})
    for row in scores:
        validate(row, schemas["score"])
        if row["clip_cosine"] is not None and not math.isfinite(row["clip_cosine"]):
            raise ValueError("Invalid cosine")
        expected = generated[row["image_id"]]
        if row["status"] == "success" and (expected["status"] != "success" or not expected["description"].strip()):
            raise ValueError("Cannot score a failed or abstaining generation")
    for row in reviews:
        validate(row, schemas["review"])
        if row["unsupported_claim_count"] != len(row["unsupported_claims"]):
            raise ValueError("Claim count differs from listed atomic claims")
        source = generated[row["image_id"]]
        if row["run_id"] != run_id or source["status"] != "success" or not source["description"].strip():
            raise ValueError("Review must reference an actual generated description")
        if row["generation_sha256"] != digest(source):
            raise ValueError("Review is not bound to this exact generation")
        if row["rubric_sha256"] != config["rubric_sha256"]:
            raise ValueError("Review rubric changed")
    values = [r["clip_cosine"] for r in scores if r["status"] == "success"]
    times = [r["latency_seconds"] for r in generations]
    zero = sum(r["unsupported_claim_count"] == 0 for r in reviews)
    success = sum(r["status"] == "success" for r in generations)
    abstentions = sum(r["status"] == "success" and not r["description"].strip() for r in generations)
    return dict(attempted=len(ids), generated=success-abstentions, generation_failures=len(ids)-success,
                abstentions=abstentions, reviewed=len(reviews), unreviewed_generated=success-abstentions-len(reviews),
                score_protocol=PROTOCOL, score_valid_n=len(values), score_failed_or_skipped_n=len(ids)-len(values),
                mean_clip_cosine=mean(values) if values else None, median_clip_cosine=median(values) if values else None,
                zero_unsupported_claims=zero, zero_unsupported_share=zero/len(reviews) if reviews else None,
                unsupported_claim_count=sum(r["unsupported_claim_count"] for r in reviews),
                mean_clarity=mean(r["clarity"] for r in reviews) if reviews else None,
                mean_specificity=mean(r["specificity"] for r in reviews) if reviews else None,
                missing_important_visible_fact_n=sum(r["missing_important_visible_fact"] for r in reviews),
                generation_latency_seconds=dict(mean=mean(times), p95=percentile(times, .95), median=median(times)),
                factuality_pass_definition="Zero unsupported assertions across the entire output, among reviewed only; CLIP is not a factuality test")


def assert_one_change(base, revision):
    operational = {"run_id", "prompt", "prompt_sha256", "prompt_version", "configuration_sha256", "model_load_seconds", "created_utc"}
    a = {k: v for k, v in base.items() if k not in operational}
    b = {k: v for k, v in revision.items() if k not in operational}
    if a != b:
        raise ValueError("Model, data, scorer, rubric or decoding changed")
    if revision["prompt"]["base"] != base["prompt"]["base"] or base["prompt"]["feature"] == revision["prompt"]["feature"]:
        raise ValueError("Exactly one prompt feature must change")


def paired(base_config, revised_config, base_rows, revised_rows, base_reviews, revised_reviews, base_scores, revised_scores):
    assert_one_change(base_config, revised_config)
    ids = base_config["image_ids"]
    a = exact_rows(base_rows, ids, base_config["run_id"])
    b = exact_rows(revised_rows, ids, revised_config["run_id"])
    ar = {r["image_id"]: r for r in base_reviews}
    br = {r["image_id"]: r for r in revised_reviews}
    ac = exact_rows(base_scores, ids, base_config["run_id"])
    bc = exact_rows(revised_scores, ids, revised_config["run_id"])
    rows = []
    for i in ids:
        row = dict(image_id=i, baseline_status=a[i]["status"], revised_status=b[i]["status"],
                   both_reviewed=i in ar and i in br, clip_cosine_delta=None, unsupported_claim_delta=None)
        if ac[i]["status"] == bc[i]["status"] == "success":
            row["clip_cosine_delta"] = bc[i]["clip_cosine"] - ac[i]["clip_cosine"]
        if row["both_reviewed"]:
            row.update(unsupported_claim_delta=br[i]["unsupported_claim_count"]-ar[i]["unsupported_claim_count"],
                       factuality_fix=ar[i]["unsupported_claim_count"] > 0 and br[i]["unsupported_claim_count"] == 0,
                       factuality_regression=ar[i]["unsupported_claim_count"] == 0 and br[i]["unsupported_claim_count"] > 0,
                       clarity_delta=br[i]["clarity"]-ar[i]["clarity"], specificity_delta=br[i]["specificity"]-ar[i]["specificity"],
                       missing_fact_delta=int(br[i]["missing_important_visible_fact"])-int(ar[i]["missing_important_visible_fact"]))
        rows.append(row)
    return rows
