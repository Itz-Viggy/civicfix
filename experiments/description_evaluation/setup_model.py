"""Explicit public weight download. Run before offline inference, in Qwen venv."""
import json
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

from .contracts import HERE, ROOT, write_new
from scripts.dataset_tools import sha256


def main():
    cfg = json.loads((HERE / "settings.json").read_text())
    info = HfApi().model_info(cfg["artifact_id"], revision=cfg["artifact_revision"], files_metadata=True)
    if info.sha != cfg["artifact_revision"] or info.gated:
        raise ValueError("Artifact must match the pinned public revision")
    path = Path(snapshot_download(cfg["artifact_id"], revision=info.sha,
                                 local_dir=ROOT / ".runtime/models/qwen3-vl-4b-4bit", ignore_patterns=[".gitattributes"]))
    files = {}
    for item in info.siblings:
        if item.rfilename == ".gitattributes":
            continue
        value = sha256(path / item.rfilename)
        if item.lfs and value != item.lfs.sha256:
            raise ValueError("Hub LFS checksum mismatch")
        files[item.rfilename] = value
    manifest = dict(artifact_id=cfg["artifact_id"], revision=info.sha, files=files,
                    license="Apache-2.0 per pinned model card; community conversion of Qwen3-VL-4B-Instruct",
                    source="https://huggingface.co/"+cfg["artifact_id"]+"/tree/"+info.sha,
                    lfs_verification="All LFS file hashes checked against Hub metadata")
    destination = HERE / "qwen_artifact.json"
    if destination.exists():
        if json.loads(destination.read_text()) != manifest:
            raise ValueError("Artifact manifest changed")
    else:
        write_new(destination, manifest)
    print("Verified pinned public model artifact")


if __name__ == "__main__":
    main()
