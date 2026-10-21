"""Execute this experiment in the current Python; save only after every cell passes."""
import os
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager


def main():
    root = Path(__file__).resolve().parents[2]
    path = Path(__file__).with_name("training_experiments.ipynb")
    notebook = nbformat.read(path, as_version=4)
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
    temp = path.with_suffix(".executed.tmp")
    nbformat.write(notebook, temp)
    os.replace(temp, path)
    print("Fresh kernel completed; actual outputs saved:", path.relative_to(root))


if __name__ == "__main__":
    main()
