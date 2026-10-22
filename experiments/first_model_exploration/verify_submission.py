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
    classification = [c for c in code if c.metadata.get("civicfix_section") != "description"]
    descriptions = [c for c in code if c.metadata.get("civicfix_section") == "description"]
    assert len(classification) == 9 and len(descriptions) == 9
    counts = [c.execution_count for c in code]
    # The submitted copy preserves the original classifier session, then adds a
    # separately executed evidence-replay session. Full reruns use one sequence.
    assert counts == list(range(1,len(code)+1)) or (
        [c.execution_count for c in classification] == list(range(1,len(classification)+1)) and
        [c.execution_count for c in descriptions] == list(range(1,len(descriptions)+1)))
    assert {c.id for c in descriptions} == {
        "description-setup", "description-configuration", "description-rerun-helper",
        "description-baseline", "description-prompt-change", "description-revision",
        "description-results", "description-cases", "description-failures"}
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
    from experiments.description_evaluation.contracts import HERE as DESCRIPTION
    from experiments.description_evaluation.report import load_run
    description_results=json.loads((DESCRIPTION / "results.json").read_text())
    assert description_results["description_evaluation_complete"] is True
    for name in ("baseline", "revision"):
        run=load_run(DESCRIPTION / "evidence" / name)
        assert run[5] == description_results[name]
        assert run[0]["image_ids"] == json.loads((DESCRIPTION / "selection.json").read_text())["image_ids"]
    assert subprocess.check_output(["git","ls-files","docs"],cwd=ROOT,text=True) == ""
    assert subprocess.run(["git","check-ignore","-q","docs/FIRST_MODEL_EXPLORATION_ASSIGNMENT.md"],cwd=ROOT).returncode == 0
    # Compare immutable dataset and original notebook/runtime against starting branch.
    immutable=["data", "playground.ipynb", "requirements.txt", "scripts", "config/inference.example.toml", "Dockerfile"]
    assert subprocess.check_output(["git","diff","--name-only","origin/codex/stage-0-foundation","--",*immutable],cwd=ROOT,text=True) == ""
    print(f"PASS: one combined notebook, {len(code)} executed cells (9 CLIP + 9 description evidence replay); original CLIP plots and description examples; verified real configurations/results/reviews; private docs ignored/untracked; original data and architecture unchanged.")


if __name__ == "__main__":
    main()
