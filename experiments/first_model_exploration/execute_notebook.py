"""Execute the combined notebook, or refresh only its saved-description section."""
import argparse
import os
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--descriptions-only", action="store_true",
                        help="Validate/display real saved Qwen runs; preserve CLIP cells and outputs")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    path = Path(__file__).with_name("training_experiments.ipynb")
    notebook = nbformat.read(path, as_version=4)
    original = notebook
    if args.descriptions_only:
        notebook = nbformat.v4.new_notebook(cells=[c for c in original.cells
            if c.metadata.get("civicfix_section") == "description"], metadata=original.metadata)
        if not notebook.cells:
            raise ValueError("Notebook has no description section")
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    manager = KernelManager(kernel_name="python3")
    manager.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
    try:
        NotebookClient(notebook, timeout=600, allow_errors=False, km=manager,
                       resources={"metadata": {"path": str(root)}}).execute()
    finally:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
    nbformat.validate(notebook)
    if args.descriptions_only:
        refreshed = {c.id:c for c in notebook.cells}
        original.cells = [refreshed.get(c.id,c) for c in original.cells]
        notebook = original
    temp = path.with_suffix(".executed.tmp")
    nbformat.write(notebook, temp)
    os.replace(temp, path)
    print("Fresh kernel completed; actual outputs saved:", path.relative_to(root))
    if args.descriptions_only:
        print("CLIP outputs preserved. Description cells validate/replay saved real inference evidence; no new Qwen inference.")


if __name__ == "__main__":
    main()
