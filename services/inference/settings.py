"""Portable inference settings; defaults preserve the native Mac workflow."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def seconds(name, default):
    value = float(os.getenv(name, default))
    if not 0 < value <= 86400:
        raise ValueError(f'{name} must be positive and at most 86400')
    return value

def backend():
    value = os.getenv('CIVICFIX_QWEN_BACKEND', 'mlx')
    if value not in ('mlx', 'transformers'):
        raise ValueError('Unsupported CIVICFIX_QWEN_BACKEND')
    return value

def models():
    return Path(os.getenv('CIVICFIX_MODEL_DIR', str(ROOT / '.runtime/models')))
