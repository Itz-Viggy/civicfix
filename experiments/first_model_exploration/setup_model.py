"""Explicit public-weight download only; never uploads images or provisions compute."""
from pathlib import Path
import json

from open_clip.pretrained import download_pretrained, get_pretrained_cfg

from .benchmark import ROOT, HERE, MODEL, TAG, sha256


def main():
    expected = json.loads((HERE / "model.json").read_text())
    cfg = get_pretrained_cfg(MODEL, TAG)
    if cfg["url"] != expected["source_url"]:
        raise RuntimeError("Pinned source differs from installed OpenCLIP registry")
    path = Path(download_pretrained(cfg, prefer_hf_hub=False,
                                   cache_dir=str(ROOT / ".runtime/models/clip")))
    if sha256(path) != expected["sha256"]:
        raise RuntimeError("Checkpoint hash mismatch")
    print("Verified public OpenAI ViT-B/32 checkpoint:", expected["sha256"])


if __name__ == "__main__":
    main()
