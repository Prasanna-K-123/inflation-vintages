"""Verify historical freezes through the exact preserved original builder.

The 26 October header parser is a disclosed post-freeze correction; the
original panel, fit, forecasts and old source hashes remain the evidence.
"""
import hashlib
import json
from pathlib import Path

REVISED_CODE_SHA256 = {'scripts/build_vintages.py': 'd24433ec0088fe6ec0836989ad422e8764615ba43bd5e43425cff2b96f4f5098', 'scripts/header_columns.py': '1c76303cf163c88fbd48585756984824be0c19009c3a6220a8cbb33d87ca746c', 'scripts/acquire_sources.py': 'd5468175a533f568a9d3ea4aa35aa19cbb1592a1dacafeef10ff02d5ff99e431'}


def verify_frozen_inputs(root, seal, *, skip=()):
    root = Path(root)
    revision = json.loads((root / 'reports/source_integrity_revision_20261026.json').read_text())
    if revision['revised_code_sha256'] != REVISED_CODE_SHA256:
        raise ValueError('Revision receipt does not identify the reviewed source code')
    for name, expected in REVISED_CODE_SHA256.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Unrecorded revised-method change: ' + name)
    checked = []
    for name, expected in seal['sha256'].items():
        if name in skip:
            continue
        path = root / name
        if name == 'scripts/build_vintages.py':
            path = root / 'reproducibility/original_build_vintages.py'
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Historical frozen input changed: ' + name)
        checked.append(name)
    return checked
