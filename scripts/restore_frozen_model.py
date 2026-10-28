"""Reconstruct the original model artifact from published coefficients; no fit."""
import hashlib
import json
from pathlib import Path
from method_integrity import verify_frozen_inputs

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    seal = json.loads((ROOT / 'reports/model_freeze.json').read_text())
    verify_frozen_inputs(ROOT, seal, skip=('artifacts/ar1.json',))
    model = json.loads((ROOT / 'reports/development.json').read_text())['model']
    raw = (json.dumps(model, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    if hashlib.sha256(raw).hexdigest() != seal['sha256']['artifacts/ar1.json']:
        raise ValueError('Published coefficients do not reconstruct the frozen artifact')
    target = ROOT / 'artifacts/ar1.json'
    if target.exists() and target.read_bytes() != raw:
        raise ValueError('Existing model differs; will not overwrite it')
    target.parent.mkdir(exist_ok=True)
    if not target.exists():
        target.write_bytes(raw)
    print('Original model artifact hash verified; no fitting or selection performed')
