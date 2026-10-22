"""D0: freeze development identities before any generator outputs are examined."""
import json

from experiments.first_model_exploration.benchmark import inspect_data, sha256, write_new
from scripts.dataset_tools import CATEGORIES
from .contracts import HERE, ROOT


def main():
    _, development, _, summary = inspect_data()
    quotas = dict(zip(CATEGORIES, [4, 4, 4, 3, 5]))
    chosen = []
    for category, count in quotas.items():
        chosen.extend(development[development.issue_type.eq(category)].sort_values("image_id").head(count).to_dict("records"))
    fields = ["image_id", "filename", "sha256", "issue_type", "source_url", "source_version", "author", "license", "license_url"]
    write_new(HERE / "selection.json", dict(
        version=1, selection_rule="Lexicographically first IDs within fixed category quotas; frozen before generation",
        quotas=quotas, image_ids=[r["image_id"] for r in chosen],
        images=[{k:r[k] for k in fields} for r in chosen],
        manifest_sha256=summary["manifest_sha256"], dataset_commit=summary["dataset_commit"],
        split_sha256=sha256(ROOT / "experiments/first_model_exploration/split.json"),
        limitation="20 already inspected development images; no held-out performance claim"))


if __name__ == "__main__":
    main()
