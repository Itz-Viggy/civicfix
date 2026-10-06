"""Execute every cell in a fresh kernel; atomically save only a successful run."""
from pathlib import Path
import os
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

root = Path(__file__).resolve().parents[1]
path = root / "playground.ipynb"
notebook = nbformat.read(path, as_version=4)
for cell in notebook.cells:
    if cell.cell_type == "code":
        cell.outputs = []
        cell.execution_count = None
# Use this environment's Python directly, independent of global kernelspecs.
manager = KernelManager(kernel_name="python3")
manager.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
client = NotebookClient(notebook, timeout=180, allow_errors=False, km=manager,
                        resources={"metadata": {"path": str(root)}})
try:
    client.execute()
finally:
    if manager.has_kernel:
        manager.shutdown_kernel(now=True)
nbformat.validate(notebook)
temp = path.with_suffix(".executed.tmp")
nbformat.write(notebook, temp)
os.replace(temp, path)
print("Notebook executed successfully; actual outputs saved in playground.ipynb")
