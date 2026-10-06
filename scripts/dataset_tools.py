"""Immutable CivicFix retrieval and metadata checks; no model inference."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from PIL import Image
import requests

CATEGORIES = ["pothole", "broken_streetlight", "damaged_sign", "leaking_hydrant", "illegal_dumping"]
REQUIRED = ["image_id", "filename", "issue_type", "source_name", "source_url", "download_url",
            "source_version", "author", "license", "license_url", "retrieved_at", "label_basis",
            "review_status", "sha256", "notes"]
OPTIONAL = ["location", "capture_date", "lighting", "weather", "scene_id"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image_path(root: Path, filename: str) -> Path:
    """Reject traversal, absolute paths, backslashes and symlink escapes."""
    p = PurePosixPath(filename)
    if not re.fullmatch(r"images/commons-[a-f0-9]{10}\.jpg", filename):
        raise ValueError("Invalid dataset image path")
    result = root.joinpath(*p.parts)
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError("Image path escapes dataset directory")
    return result


def _credential() -> str | None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(["gh", "auth", "token", "--hostname", "github.com"],
                                capture_output=True, text=True, timeout=10, check=True)
        return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.SubprocessError):
        return None


def _remote_bytes(repository: str, commit: str, path: str, token: str | None) -> bytes:
    headers = {"Accept": "application/vnd.github.raw+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = "Bearer " + token
    url = f"https://api.github.com/repos/{repository}/contents/{path}"
    for attempt in range(3):
        try:
            # GitHub API receives credentials; never forward them to image/source hosts.
            response = requests.get(url, params={"ref": commit}, headers=headers,
                                    timeout=(10, 45), allow_redirects=False)
            if response.status_code in (401, 403, 404):
                raise RuntimeError(f"GitHub returned {response.status_code}; check repository access and version")
            if response.status_code == 200:
                return response.content
            if response.status_code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f"GitHub retrieval failed: HTTP {response.status_code}")
        except requests.RequestException:
            pass  # Do not echo requests or credential-bearing headers.
        if attempt < 2:
            time.sleep(2 ** attempt)
    raise RuntimeError("GitHub download failed after three bounded attempts")


def read_manifest(root: Path) -> pd.DataFrame:
    return pd.read_csv(root / "labels.csv", dtype=str, keep_default_na=False)


def retrieve_dataset(config_path: Path, destination: Path, mode: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Download/copy a pinned manifest and its images into an empty directory."""
    config_path, destination = Path(config_path), Path(destination)
    cfg = json.loads(config_path.read_text())
    mode = mode or os.environ.get("CIVICFIX_DATA_MODE", cfg["storage_mode"])
    if mode not in ("github", "local"):
        raise ValueError("CIVICFIX_DATA_MODE must be github or local")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", cfg["repository"]):
        raise ValueError("Invalid repository identifier")
    if not re.fullmatch(r"[a-f0-9]{40}", cfg["dataset_commit"]):
        raise ValueError("Dataset commit must be an immutable full SHA")
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Retrieval requires an empty directory; do not reuse unvalidated cache")
    destination.mkdir(parents=True, exist_ok=True)
    token = _credential() if mode == "github" else None
    if mode == "github" and cfg["private"] and not token:
        raise RuntimeError("Private dataset needs gh auth login or GITHUB_TOKEN with read access")
    manifest = destination / "labels.csv"
    if mode == "local":
        shutil.copyfile(config_path.parent / "labels.csv", manifest)
    else:
        manifest.write_bytes(_remote_bytes(cfg["repository"], cfg["dataset_commit"], "data/labels.csv", token))
    if sha256(manifest) != cfg["manifest_sha256"]:
        raise ValueError("Manifest SHA-256 mismatch")
    df = read_manifest(destination)
    if set(REQUIRED) - set(df.columns) or df.empty:
        raise ValueError("Manifest missing required columns or has no real images")
    if df["image_id"].duplicated().any() or df["filename"].duplicated().any():
        raise ValueError("Manifest IDs and paths must be unique")
    if not df["issue_type"].isin(CATEGORIES).all():
        raise ValueError("Manifest has unsupported category")
    if not df[REQUIRED].apply(lambda c: c.str.strip().ne("")).all().all():
        raise ValueError("Manifest has missing required values")
    if not df["image_id"].str.fullmatch(r"commons-[a-f0-9]{10}").all():
        raise ValueError("Invalid image ID")
    for filename in df["filename"]:
        image_path(destination, filename)
    if not df["sha256"].str.fullmatch(r"[a-f0-9]{64}").all():
        raise ValueError("Invalid image hash")

    def get_image(row):
        target = image_path(destination, row.filename)
        target.parent.mkdir(parents=True, exist_ok=True)
        if mode == "local":
            shutil.copyfile(image_path(config_path.parent, row.filename), target)
        else:
            target.write_bytes(_remote_bytes(cfg["repository"], cfg["dataset_commit"], "data/" + row.filename, token))
        if sha256(target) != row.sha256:
            raise ValueError(f"Image SHA-256 mismatch: {row.image_id}")
        with Image.open(target) as im:
            im.verify()

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(get_image, df.itertuples(index=False)))
    return df, {"mode": mode, "dataset_name": cfg["dataset_name"], "dataset_version": cfg["dataset_version"],
                "dataset_commit": cfg["dataset_commit"], "validated_images": len(df),
                "manifest_sha256": sha256(manifest)}


def inspect_images(df: pd.DataFrame, root: Path) -> pd.DataFrame:
    records = []
    for row in df.itertuples(index=False):
        path = image_path(root, row.filename)
        with Image.open(path) as im:
            im.load()
            records.append({"image_id": row.image_id, "width": im.width, "height": im.height,
                            "format": im.format, "mode": im.mode, "bytes": path.stat().st_size,
                            "exif_fields": len(im.getexif()), "has_gps": 34853 in im.getexif(),
                            "hash_matches": sha256(path) == row.sha256})
    return pd.DataFrame(records)


def average_hash(path: Path) -> int:
    """Simple near-duplicate screening, not learned features or proof of absence."""
    with Image.open(path) as im:
        values = list(im.convert("L").resize((8, 8), Image.Resampling.LANCZOS).get_flattened_data())
    mean = sum(values) / len(values)
    return sum((value >= mean) << i for i, value in enumerate(values))


def near_duplicate_pairs(df: pd.DataFrame, root: Path, threshold: int = 6) -> pd.DataFrame:
    rows = list(df.itertuples(index=False))
    hashes = [average_hash(image_path(root, row.filename)) for row in rows]
    pairs = []
    for i, left in enumerate(rows):
        for j in range(i + 1, len(rows)):
            distance = (hashes[i] ^ hashes[j]).bit_count()
            if distance <= threshold:
                pairs.append({"left_id": left.image_id, "right_id": rows[j].image_id,
                              "distance": distance, "same_label": left.issue_type == rows[j].issue_type})
    return pd.DataFrame(pairs, columns=["left_id", "right_id", "distance", "same_label"])
