"""Free local Qwen adapter, with explicit artifact verification and no fallback."""
from importlib.metadata import version
import json
from pathlib import Path
import platform
import time

from scripts.dataset_tools import sha256


class MLXGenerator:
    def __init__(self, path: Path, settings: dict, artifact_manifest: dict):
        import mlx.core as mx
        from mlx_vlm import load

        if platform.machine() != "arm64" or mx.default_device() != mx.gpu:
            raise RuntimeError("This configured runtime requires Apple Silicon Metal")
        for name, expected in artifact_manifest["files"].items():
            if sha256(path / name) != expected:
                raise ValueError(f"Qwen artifact hash mismatch: {name}")
        if artifact_manifest["revision"] != settings["artifact_revision"]:
            raise ValueError("Qwen revision differs from configuration")
        started = time.perf_counter()
        self.model, self.processor = load(str(path), trust_remote_code=False)
        self.config = json.loads((path / "config.json").read_text())
        self.settings = settings
        mx.synchronize()
        self.load_seconds = time.perf_counter() - started
        self.metadata = dict(
            adapter="local_mlx", device_info=mx.device_info(), python=platform.python_version(),
            platform=platform.platform(), packages={p:version(p) for p in
                ["mlx-vlm", "mlx", "mlx-metal", "mlx-lm", "transformers", "tokenizers", "Pillow", "numpy"]},
            artifact_manifest=artifact_manifest, network="Python socket connections denied during loading/inference",
            service_cost_usd=0, cost_note="Owned hardware and electricity not priced")

    def generate(self, image, prompt):
        import mlx.core as mx
        from mlx_vlm import generate
        from mlx_vlm.prompt_utils import apply_chat_template

        mx.random.seed(self.settings["seed"])
        formatted = apply_chat_template(self.processor, self.config, prompt, num_images=1)
        # Bound pixels explicitly: some Transformers processors ignore MLX's
        # resize_shape option. Preserve aspect ratio and do not upscale here.
        from PIL import Image
        pixels = image.copy()
        pixels.thumbnail((self.settings["generator_max_side"],)*2, Image.Resampling.BICUBIC)
        output = generate(self.model, self.processor, formatted, image=[pixels], verbose=False,
                          max_tokens=self.settings["max_tokens"], temperature=self.settings["temperature"])
        mx.synchronize()
        self.last_metadata = dict(generation_tokens=output.generation_tokens, prompt_tokens=output.prompt_tokens,
                                  peak_memory_gb=output.peak_memory)
        mx.clear_cache()
        return output.text
