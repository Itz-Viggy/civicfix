"""Real OpenCLIP inference with split gates, frozen runs and failure-aware metrics.

Only PIL RGB pixels and fixed taxonomy prompts enter the model. Ground truth is
joined after predictions are persisted. All raw run artifacts stay in .runtime/.
"""
from __future__ import annotations

import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import platform
import time

import numpy as np
import pandas as pd
from PIL import Image

from scripts.dataset_tools import CATEGORIES, REQUIRED, OPTIONAL, image_path, sha256

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MODEL = "ViT-B-32"
TAG = "openai"
SEED = 6216


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def write_new(path: Path, value):
    """Never replace a first result or a frozen configuration."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def validate_split(manifest: pd.DataFrame, split: dict):
    if split.get("status") != "verified" or not split.get("source_sha256"):
        raise ValueError("Section 6.5 split is not verified; inference is blocked")
    groups = [split.get(k, []) for k in ("development_ids", "training_ids", "held_out_ids")]
    flat = [i for group in groups for i in group]
    if len(flat) != len(set(flat)) or set(flat) != set(manifest.image_id):
        raise ValueError("Split must partition every manifest ID exactly once")
    if not groups[0]:
        raise ValueError("No designated development cases")
    # Check declared scene grouping and byte duplicates across the split.
    by_id = manifest.set_index("image_id")
    owner = {i: k for k, group in enumerate(groups) for i in group}
    for column in ("scene_id", "sha256"):
        for _, rows in by_id[by_id[column].ne("")].groupby(column):
            if len({owner[i] for i in rows.index}) != 1:
                raise ValueError(f"{column} crosses data partitions")
    return manifest.set_index("image_id", drop=False).loc[groups[0]].reset_index(drop=True)


def inspect_data():
    cfg = json.loads((ROOT / "data/dataset_config.json").read_text())
    if sha256(ROOT / "data/labels.csv") != cfg["manifest_sha256"]:
        raise ValueError("Pinned manifest changed")
    df = pd.read_csv(ROOT / "data/labels.csv", dtype=str, keep_default_na=False)
    if set(REQUIRED + OPTIONAL) - set(df.columns):
        raise ValueError("Missing manifest fields")
    missing = df.apply(lambda c: int(c.str.strip().eq("").sum())).to_dict()
    if any(missing[k] for k in REQUIRED) or not df.issue_type.isin(CATEGORIES).all():
        raise ValueError("Missing or invalid labels/provenance")
    if df.image_id.duplicated().any() or df.filename.duplicated().any():
        raise ValueError("Duplicate manifest identity")
    split = json.loads((HERE / "split.json").read_text())
    development = validate_split(df, split)
    # All manifest metadata may be inspected, but only development pixels decoded.
    images = []
    for row in development.itertuples(index=False):
        path = image_path(ROOT / "data", row.filename)
        if sha256(path) != row.sha256:
            raise ValueError(f"Image hash mismatch: {row.image_id}")
        with Image.open(path) as image:
            image.load()
            images.append(dict(image_id=row.image_id, width=image.width, height=image.height,
                               mode=image.mode, format=image.format, exif_fields=len(image.getexif())))
    summary = dict(dataset_version=cfg["dataset_version"], dataset_commit=cfg["dataset_commit"],
                   manifest_sha256=cfg["manifest_sha256"], pool_n=len(df), development_n=len(development),
                   counts=df.issue_type.value_counts().reindex(CATEGORIES, fill_value=0).to_dict(),
                   missing=missing, duplicate_bytes=int(df.sha256.duplicated().sum()),
                   inconsistent_labels=int((df.groupby("sha256").issue_type.nunique() > 1).sum()),
                   changes="Filled none; dropped none; original labels and unknown metadata unchanged.",
                   split=split, decoded_development_images=len(images))
    return df, development, pd.DataFrame(images), summary


def load_prompts(path: Path):
    value = json.loads(path.read_text())
    if list(value["prompts"]) != CATEGORIES:
        raise ValueError("Prompt category IDs/order do not match the fixed taxonomy")
    for texts in value["prompts"].values():
        if len(texts) != 3 or any(not isinstance(t, str) or not t.strip() for t in texts):
            raise ValueError("Three nonempty fixed descriptions required per category")
    return value


def classify_scores(scores):
    if len(scores) != len(CATEGORIES) or not all(math.isfinite(float(s)) and -1.00001 <= s <= 1.00001 for s in scores):
        raise ValueError("Expected five finite raw cosine scores")
    order = sorted(range(len(CATEGORIES)), key=lambda i: -float(scores[i]))
    return dict(predicted_category=CATEGORIES[order[0]],
                scores=dict(zip(CATEGORIES, map(float, scores))),
                top1_margin=float(scores[order[0]] - scores[order[1]]),
                mode="closed_set", score_kind="cosine_similarity", simulated=False)


class Runtime:
    """Explicit CPU float32 runtime. No remote or device fallback."""

    def __init__(self, checkpoint: Path, expected_hash: str, threads=4):
        import torch
        import open_clip

        started = time.perf_counter()
        if not checkpoint.is_file() or sha256(checkpoint) != expected_hash:
            raise ValueError("Missing checkpoint or checkpoint SHA-256 mismatch")
        torch.set_num_threads(threads)
        torch.manual_seed(SEED)
        torch.use_deterministic_algorithms(True)
        self.torch = torch
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            MODEL, pretrained=str(checkpoint), device="cpu", precision="fp32",
            force_quick_gelu=True, image_mean=(0.48145466, 0.4578275, 0.40821073),
            image_std=(0.26862954, 0.26130258, 0.27577711), image_interpolation="bicubic",
            image_resize_mode="shortest",
            # Original OpenAI release is TorchScript, not a plain state_dict.
            # Only this pinned, hash-verified public artifact is accepted above.
            weights_only=False)
        self.model.eval()
        self.tokenizer = open_clip.get_tokenizer(MODEL)
        bpe = Path(open_clip.__file__).parent / "bpe_simple_vocab_16e6.txt.gz"
        self.metadata = dict(model=MODEL, pretrained_tag=TAG, checkpoint_sha256=expected_hash,
                             device="cpu", precision="float32", batch_size=1, threads=threads,
                             activation="QuickGELU (OpenAI checkpoint native)",
                             seed=SEED, deterministic_algorithms=True, training_budget="none (pretrained inference)",
                             tokenizer=type(self.tokenizer).__name__, tokenizer_bpe_sha256=sha256(bpe),
                             context_length=self.model.context_length, preprocess=repr(self.preprocess),
                             platform=platform.system(), machine=platform.machine(), python=platform.python_version(),
                             packages={p: version(p) for p in ["torch", "torchvision", "open_clip_torch", "Pillow", "numpy", "pandas"]},
                             score_method="normalize each prompt; mean 3 per class; normalize prototype; normalized image dot prototype",
                             tie_break="first in declared category order", categories=CATEGORIES,
                             backend="local Mac CPU; no image upload", service_cost_usd=0,
                             service_cost_note="No API/compute service charge; electricity and owned hardware not priced")
        self.load_seconds = time.perf_counter() - started
        self.calls = 0

    def set_prompts(self, prompts):
        start = time.perf_counter()
        texts = [t for c in CATEGORIES for t in prompts["prompts"][c]]
        with self.torch.inference_mode():
            vectors = self.model.encode_text(self.tokenizer(texts)).float()
            vectors = self._normalize(vectors)
            self.prototypes = self._normalize(vectors.reshape(5, 3, -1).mean(dim=1))
        return time.perf_counter() - start

    def _normalize(self, vectors):
        norm = vectors.norm(dim=-1, keepdim=True)
        if not self.torch.isfinite(vectors).all() or (norm <= 0).any():
            raise ValueError("Invalid encoder embedding")
        return vectors / norm

    def classify(self, image: Image.Image):
        """Receives pixels only, never the filename, ID, label or source metadata."""
        tensor = self.preprocess(image.convert("RGB")).unsqueeze(0)
        with self.torch.inference_mode():
            feature = self._normalize(self.model.encode_image(tensor).float())
            values = (feature @ self.prototypes.T).squeeze(0).tolist()
        self.calls += 1
        return classify_scores(values), list(tensor.shape), list(feature.shape)


def evaluate(rows, truth: pd.DataFrame):
    """Failures count against accuracy and as FN in their true class; no fake label."""
    if len(rows) != len(truth) or len({r["image_id"] for r in rows}) != len(rows):
        raise ValueError("Coverage/identity mismatch")
    if {r["image_id"] for r in rows} != set(truth.image_id):
        raise ValueError("Prediction IDs differ from development IDs")
    labels = truth.set_index("image_id").issue_type.to_dict()
    matrix = np.zeros((5, 6), dtype=int)  # last column is an execution failure
    for row in rows:
        actual = CATEGORIES.index(labels[row["image_id"]])
        if row["status"] == "success":
            if row.get("simulated") is not False:
                raise ValueError("Simulated predictions cannot enter real evaluation")
            predicted = CATEGORIES.index(row["predicted_category"])
        else:
            predicted = 5
        matrix[actual, predicted] += 1
    per_class = []
    for i, category in enumerate(CATEGORIES):
        tp = int(matrix[i, i]); support = int(matrix[i].sum()); predicted = int(matrix[:, i].sum())
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class.append(dict(category=category, precision=precision, recall=recall, f1=f1, support=support, correct=tp))
    correct = int(np.trace(matrix[:, :5])); failures = int(matrix[:, 5].sum())
    times = [r["latency_seconds"] for r in rows]
    return dict(attempted_n=len(rows), successful_predictions=len(rows)-failures, failures=failures,
                correct=correct, accuracy=correct/len(rows), macro_f1=float(np.mean([r["f1"] for r in per_class])),
                per_class=per_class, confusion_matrix=matrix.tolist(), confusion_columns=CATEGORIES+["execution_failure"],
                latency_seconds=dict(mean=float(np.mean(times)), median=float(np.median(times)),
                                     p95=float(np.percentile(times,95)), maximum=float(max(times))),
                under_10_seconds=sum(t < 10 for t in times),
                failure_handling="All attempted cases in denominator; failure is FN for actual class, no FP in supported classes; zero-division metrics set to zero")


def run(runtime: Runtime, development: pd.DataFrame, split: dict, prompt_path: Path, run_dir: Path):
    """Freeze before inference; append/fsync first predictions before any scoring."""
    import os

    prompts = load_prompts(prompt_path)
    cfg = dict(**runtime.metadata, prompts=prompts, prompt_sha256=sha256(prompt_path),
               split_sha256=sha256(HERE / "split.json"), development_ids=development.image_id.tolist(),
               manifest_sha256=sha256(ROOT / "data/labels.csv"), dataset_version="v1",
               dataset_commit=json.loads((ROOT / "data/dataset_config.json").read_text())["dataset_commit"],
               timing="perf_counter from file open/decode/RGB through native preprocessing, encoder, scoring and CPU result; excludes persistence, labels, setup and text prototypes",
               model_load_seconds=runtime.load_seconds, first_call_in_process=runtime.calls == 0)
    # Gate again immediately before inference, including the exact split order.
    full = pd.read_csv(ROOT / "data/labels.csv", dtype=str, keep_default_na=False)
    designated = validate_split(full, split)
    if development.image_id.tolist() != designated.image_id.tolist():
        raise ValueError("Only the exact frozen development cases may run")
    cfg["configuration_sha256"] = digest(cfg)
    write_new(run_dir / "configuration.json", cfg)
    text_seconds = runtime.set_prompts(prompts)
    rows = []
    with (run_dir / "predictions.jsonl").open("x") as stream:
        for index, row in enumerate(development.itertuples(index=False)):
            start = time.perf_counter()
            result = dict(image_id=row.image_id, status="error", error_type=None)
            try:
                path = image_path(ROOT / "data", row.filename)
                with Image.open(path) as image:
                    image.load()
                    prediction, shape, feature_shape = runtime.classify(image)
                result.update(prediction, status="success", input_shape=shape, embedding_shape=feature_shape)
            except Exception as error:
                result["error_type"] = type(error).__name__
            result["latency_seconds"] = time.perf_counter() - start
            result["first_image_in_run"] = index == 0
            stream.write(json.dumps(result, allow_nan=False)+"\n"); stream.flush(); os.fsync(stream.fileno())
            rows.append(result)
    # No truth was passed to the runtime; evaluation happens after all rows persist.
    metrics = evaluate(rows, development)
    metrics.update(text_prototype_seconds=text_seconds, configuration_sha256=cfg["configuration_sha256"],
                   first_image_seconds=rows[0]["latency_seconds"], model_load_seconds=runtime.load_seconds)
    write_new(run_dir / "metrics.json", metrics)
    return cfg, rows, metrics


def assert_one_change(baseline: dict, revision: dict):
    """Timing/run identity may differ; only prompts may change semantic settings."""
    operational = {"prompts", "prompt_sha256", "configuration_sha256", "first_call_in_process", "model_load_seconds"}
    keys = (set(baseline) | set(revision)) - operational
    if any(baseline.get(k) != revision.get(k) for k in keys):
        raise ValueError("Comparison changed settings beyond prompts")
    if baseline["prompts"] == revision["prompts"]:
        raise ValueError("No targeted prompt change")
