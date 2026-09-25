"""Verify the numeric inputs used by supplement and figure generation."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def verify_inputs():
    paths = json.loads((ROOT / 'data/manifest.json').read_text())['files']
    for name, expected in paths.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Input checksum mismatch: {name}')
    for manifest in (ROOT / 'validation/native').glob('*/manifest.json'):
        for name, expected in json.loads(manifest.read_text()).items():
            if hashlib.sha256((manifest.parent / name).read_bytes()).hexdigest() != expected:
                raise ValueError(f'Native checksum mismatch: {manifest.parent / name}')
    return paths
