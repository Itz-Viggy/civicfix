"""Verify saved evidence and repository boundaries; does not call model services."""
import json
from pathlib import Path
import subprocess

import nbformat

from .benchmark import ROOT, HERE, CATEGORIES, assert_one_change, digest, inspect_data, sha256


def main():
    notebook=nbformat.read(HERE / "training_experiments.ipynb", as_version=4)
    nbformat.validate(notebook)
    code=[c for c in notebook.cells if c.cell_type == "code"]
    assert code and all(c.execution_count is not None and c.outputs for c in code)
    assert all(o.output_type != "error" for c in code for o in c.outputs)
    assert [c.execution_count for c in code] == list(range(1, len(code)+1))
    assert sum("image/png" in o.get("data", {}) for c in code for o in c.outputs) >= 2
    _, development, _, inspection = inspect_data()
    saved=json.loads((HERE / "results.json").read_text())
    baseline=saved["baseline"]; revision=saved["revision"]
    assert_one_change(baseline["configuration"], revision["configuration"])
    for run in [baseline,revision]:
        cfg=run["configuration"];metrics=run["metrics"]
        assert cfg["development_ids"] == development.image_id.tolist()
        assert cfg["manifest_sha256"] == inspection["manifest_sha256"]
        assert cfg["split_sha256"] == sha256(HERE / "split.json")
        assert digest({k:v for k,v in cfg.items() if k != "configuration_sha256"}) == cfg["configuration_sha256"]
        assert metrics["configuration_sha256"] == cfg["configuration_sha256"]
        assert metrics["attempted_n"] == len(development)
        assert metrics["successful_predictions"] + metrics["failures"] == len(development)
        assert sum(sum(r) for r in metrics["confusion_matrix"]) == len(development)
        assert metrics["accuracy"] == metrics["correct"] / len(development)
        assert [r["category"] for r in metrics["per_class"]] == CATEGORIES
        assert abs(metrics["macro_f1"] - sum(r["f1"] for r in metrics["per_class"])/5) < 1e-12
    assert saved["external_socket_attempts"] == 0
    assert subprocess.check_output(["git","ls-files","docs"],cwd=ROOT,text=True) == ""
    assert subprocess.run(["git","check-ignore","-q","docs/FIRST_MODEL_EXPLORATION_ASSIGNMENT.md"],cwd=ROOT).returncode == 0
    # Compare immutable dataset and original notebook/runtime against starting branch.
    immutable=["data", "playground.ipynb", "requirements.txt", "scripts", "config/inference.example.toml", "Dockerfile"]
    assert subprocess.check_output(["git","diff","--name-only","origin/codex/stage-0-foundation","--",*immutable],cwd=ROOT,text=True) == ""
    print(f"PASS: {len(code)} executed cells; two result plots; saved configurations/metrics; exact development IDs; no simulated evidence; private docs ignored/untracked; original data and architecture unchanged.")


if __name__ == "__main__":
    main()
