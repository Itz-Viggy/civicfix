"""D5: validate saved evidence and compute summaries and paired metrics."""
import argparse
import json
from pathlib import Path
from statistics import mean, median

from .contracts import HERE, assert_one_change, digest, paired, read_jsonl, sha256, summarize, write_new


def load_run(directory):
    cfg = json.loads((directory / "configuration.json").read_text())
    if cfg.get("simulated") is not False:
        raise ValueError("Simulated evidence cannot enter the experiment report")
    if digest({k:v for k,v in cfg.items() if k != "configuration_sha256"}) != cfg["configuration_sha256"]:
        raise ValueError("Configuration digest mismatch")
    if cfg["rubric_sha256"] != sha256(HERE / "rubric.json") or cfg["schemas_sha256"] != sha256(HERE / "schemas.json"):
        raise ValueError("Rubric/schema differs from frozen configuration")
    if any(sha256(HERE / name) != value for name,value in cfg["implementation_sha256"].items()):
        raise ValueError("Generator/scorer implementation differs from frozen run")
    generations = read_jsonl(directory / "generations.jsonl")
    if any(r["identity_sha256"] != cfg["configuration_sha256"] for r in generations):
        raise ValueError("Generation identity differs from configuration")
    scores = read_jsonl(directory / "scores.jsonl")
    reviews = read_jsonl(directory / "reviews.jsonl")
    scorer = json.loads((directory / "scorer_configuration.json").read_text())
    if scorer["configuration_sha256"] != cfg["configuration_sha256"]:
        raise ValueError("Scorer identity mismatch")
    metrics = summarize(cfg, generations, scores, reviews)
    return cfg, generations, scores, reviews, scorer, metrics


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("revision", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    a, b = load_run(args.baseline), load_run(args.revision)
    assert_one_change(a[0], b[0])
    # The scorer was loaded in a separate process; runtime identity must agree too.
    sa = {k:v for k,v in a[4].items() if k != "configuration_sha256"}
    sb = {k:v for k,v in b[4].items() if k != "configuration_sha256"}
    if sa != sb:
        raise ValueError("Scorer changed between runs")
    comparisons = paired(a[0], b[0], a[1], b[1], a[3], b[3], a[2], b[2])
    score_pairs = [r for r in comparisons if r["clip_cosine_delta"] is not None]
    review_pairs = [r for r in comparisons if r["both_reviewed"]]
    ar = {r["image_id"]:r for r in a[3]}
    br = {r["image_id"]:r for r in b[3]}
    paired_metrics = dict(
        cosine_pair_n=len(score_pairs), reviewed_pair_n=len(review_pairs), latency_pair_n=len(comparisons),
        mean_cosine_delta=mean(r["clip_cosine_delta"] for r in score_pairs) if score_pairs else None,
        median_cosine_delta=median(r["clip_cosine_delta"] for r in score_pairs) if score_pairs else None,
        baseline_zero_unsupported_on_pairs=sum(ar[r["image_id"]]["unsupported_claim_count"] == 0 for r in review_pairs),
        revision_zero_unsupported_on_pairs=sum(br[r["image_id"]]["unsupported_claim_count"] == 0 for r in review_pairs),
        mean_unsupported_claim_delta=mean(r["unsupported_claim_delta"] for r in review_pairs) if review_pairs else None,
        mean_clarity_delta=mean(r["clarity_delta"] for r in review_pairs) if review_pairs else None,
        mean_specificity_delta=mean(r["specificity_delta"] for r in review_pairs) if review_pairs else None,
        missing_fact_delta=sum(r["missing_fact_delta"] for r in review_pairs),
        mean_generation_latency_delta_seconds=b[5]["generation_latency_seconds"]["mean"]-a[5]["generation_latency_seconds"]["mean"])
    # A completed evaluation can expose failures. Do not require the generator
    # to succeed on every attempt or silently remove those attempts.
    complete = all(x[5]["reviewed"] >= 10 and x[5]["unreviewed_generated"] == 0 and
                   x[5]["score_valid_n"] > 0 for x in [a,b])
    result = dict(description_evaluation_complete=complete, development_only=True,
                  completion_definition="All attempts accounted for; at least 10 actual descriptions reviewed per run; all generated descriptions reviewed; real scores saved. Generation failures are retained, not factuality passes.",
                  baseline=a[5], revision=b[5], paired=comparisons,
                  paired_metrics=paired_metrics,
                  factuality_fixes=sum(r.get("factuality_fix",False) for r in comparisons),
                  factuality_regressions=sum(r.get("factuality_regression",False) for r in comparisons),
                  reviewed_pairs=sum(r["both_reviewed"] for r in comparisons),
                  baseline_configuration_sha256=a[0]["configuration_sha256"],
                  revision_configuration_sha256=b[0]["configuration_sha256"])
    write_new(args.output, result)
    print(json.dumps({k:v for k,v in result.items() if k != "paired"},indent=2))


if __name__ == "__main__":
    main()
