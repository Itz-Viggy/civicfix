"""Sequential D1/D2 CLI. Never overwrites configurations or first outputs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import time

from PIL import Image

from experiments.first_model_exploration.benchmark import Runtime, inspect_data
from scripts.dataset_tools import image_path, sha256
from .contracts import HERE, ROOT, PROTOCOL, digest, exact_rows, parse_payload, read_jsonl, write_new


def deny_network():
    """Audit Python socket connections. Not an OS-wide network sandbox."""
    attempts = []

    def denied(*args, **kwargs):
        attempts.append("denied")
        raise RuntimeError("Network disabled for local inference")

    socket.socket.connect = denied
    socket.socket.connect_ex = denied
    socket.create_connection = denied
    return attempts


def validate_selection():
    selection = json.loads((HERE / "selection.json").read_text())
    _, development, _, _ = inspect_data()
    ids = selection["image_ids"]
    if not 10 <= len(ids) <= 20 or len(ids) != len(set(ids)) or not set(ids) <= set(development.image_id):
        raise ValueError("Only 10-20 unique development cases allowed")
    if sha256(ROOT / "data/labels.csv") != selection["manifest_sha256"]:
        raise ValueError("Manifest changed after subset freeze")
    if sha256(ROOT / "experiments/first_model_exploration/split.json") != selection["split_sha256"]:
        raise ValueError("Split changed after subset freeze")
    selected = {r["image_id"]:r for r in selection["images"]}
    if len(selected) != len(ids) or set(selected) != set(ids):
        raise ValueError("Selection records differ from frozen IDs")
    for row in selection["images"]:
        original = development.set_index("image_id").loc[row["image_id"]]
        if row["sha256"] != original.sha256 or row["filename"] != original.filename:
            raise ValueError("Selected image differs from original development image")
    return selection


def append(stream, value):
    stream.write(json.dumps(value, allow_nan=False) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def generate_run(run_dir, prompt_path, model_path):
    selection = validate_selection()
    settings = json.loads((HERE / "settings.json").read_text())
    prompt = json.loads(prompt_path.read_text())
    artifact = json.loads((HERE / "qwen_artifact.json").read_text())
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    attempts = deny_network()
    from .runtime import MLXGenerator
    runtime = MLXGenerator(model_path, settings, artifact)
    cfg = dict(run_id=run_dir.name, created_utc=datetime.now(timezone.utc).isoformat(),
               image_ids=selection["image_ids"], selection_sha256=sha256(HERE / "selection.json"),
               rubric_sha256=sha256(HERE / "rubric.json"), schemas_sha256=sha256(HERE / "schemas.json"),
               implementation_sha256={name:sha256(HERE / name) for name in
                                      ["run.py", "runtime.py", "contracts.py"]},
               settings=settings, runtime=runtime.metadata, prompt=prompt, prompt_version=prompt["version"],
               prompt_sha256=sha256(prompt_path), model_load_seconds=runtime.load_seconds,
               clip_contract=json.loads((ROOT / settings["clip_model_contract"]).read_text()), score_protocol=PROTOCOL,
               timing="Decode, sanitize, preprocess, synchronized generation, strict parse; excludes load/persistence; cold first image included",
               image_sanitization="Fresh PIL RGB pixel copy; no filename, EXIF, caption, label, coordinates or annotation passed",
               retries=0, simulated=False)
    cfg["configuration_sha256"] = digest(cfg)
    write_new(run_dir / "configuration.json", cfg)
    with (run_dir / "generations.jsonl").open("x") as stream, (run_dir / "raw.private.jsonl").open("x") as raw:
        for index, photo in enumerate(selection["images"]):
            started = time.perf_counter()
            row = dict(image_id=photo["image_id"], run_id=run_dir.name, category_suggestion=None,
                       visible_observations=[], description="", outcome="unclear", clarification_reasons=[],
                       status="error", error_status=None, first_image_in_process=index == 0,
                       identity_sha256=cfg["configuration_sha256"], generation_tokens=None, prompt_tokens=None,
                       peak_memory_gb=None)
            text = None
            try:
                path = image_path(ROOT / "data", photo["filename"])
                if sha256(path) != photo["sha256"]:
                    raise ValueError("Input image hash mismatch")
                with Image.open(path) as original:
                    original.load()
                    pixels = original.convert("RGB")
                    sanitized = Image.frombytes("RGB", pixels.size, pixels.tobytes())
                text = runtime.generate(sanitized, prompt["base"] + "\n" + prompt["feature"])
                row.update(runtime.last_metadata)
                row.update(parse_payload(text), status="success")
            except Exception as error:
                row["error_status"] = type(error).__name__
            row["latency_seconds"] = time.perf_counter() - started
            append(raw, dict(image_id=photo["image_id"], text=text))
            append(stream, row)
            print(json.dumps({k:row[k] for k in ["image_id", "status", "latency_seconds"]}), flush=True)
    write_new(run_dir / "network_audit.json", dict(denied_connection_attempts=len(attempts), scope="Python socket guard, not OS-wide"))


def score_run(run_dir):
    selection = validate_selection()
    cfg = json.loads((run_dir / "configuration.json").read_text())
    if cfg["selection_sha256"] != sha256(HERE / "selection.json"):
        raise ValueError("Run uses different selection")
    rows = read_jsonl(run_dir / "generations.jsonl")
    exact_rows(rows, cfg["image_ids"], cfg["run_id"])
    os.environ["HF_HUB_OFFLINE"] = "1"
    attempts = deny_network()
    model = cfg["clip_contract"]
    runtime = Runtime(ROOT / model["local_path"], model["sha256"])
    metadata = dict(runtime=runtime.metadata, score_protocol=PROTOCOL, text_prefix="",
                    formula="dot(L2(image embedding), L2(description embedding))",
                    clip_score=None, official_clipscore=False,
                    text="Generated description only; no captions, category or review notes; OpenCLIP 77-token native tokenizer",
                    truncation="Native tokenizer; token occupancy recorded, 77 occupied means possibly truncated",
                    images="Original stored development RGB image through existing native OpenAI transform",
                    configuration_sha256=cfg["configuration_sha256"])
    write_new(run_dir / "scorer_configuration.json", metadata)
    by_id = {r["image_id"]:r for r in selection["images"]}
    with (run_dir / "scores.jsonl").open("x") as stream:
        for row in rows:
            score = dict(image_id=row["image_id"], run_id=cfg["run_id"], clip_cosine=None,
                         score_protocol=PROTOCOL, status="skipped", error_status=None, token_occupancy=None)
            try:
                if row["status"] != "success" or not row["description"].strip():
                    score["error_status"] = "generation_error_or_abstention"
                else:
                    with Image.open(image_path(ROOT / "data", by_id[row["image_id"]]["filename"])) as image:
                        tensor = runtime.preprocess(image.convert("RGB")).unsqueeze(0)
                    tokens = runtime.tokenizer([row["description"]])
                    with runtime.torch.inference_mode():
                        visual = runtime._normalize(runtime.model.encode_image(tensor).float())
                        text = runtime._normalize(runtime.model.encode_text(tokens).float())
                        value = float((visual @ text.T).item())
                    if not -1 <= value <= 1:
                        raise ValueError("Invalid cosine")
                    score.update(clip_cosine=value, status="success", token_occupancy=int((tokens != 0).sum()))
            except Exception as error:
                score.update(status="error", error_status=type(error).__name__)
            append(stream, score)
    write_new(run_dir / "scorer_audit.json", dict(denied_connection_attempts=len(attempts)))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("stage", choices=["generate", "score"])
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--prompt", type=Path, default=HERE / "prompts/v1.json")
    parser.add_argument("--model-path", type=Path, default=ROOT / ".runtime/models/qwen3-vl-4b-4bit")
    args = parser.parse_args()
    if args.stage == "generate":
        generate_run(args.run_dir, args.prompt, args.model_path)
    else:
        score_run(args.run_dir)


if __name__ == "__main__":
    main()
