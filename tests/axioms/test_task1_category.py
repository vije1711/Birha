import importlib.util
import sys
import types

import pytest
from pathlib import Path

sys.modules.setdefault('pyperclip', types.SimpleNamespace(copy=lambda *args, **kwargs: None, paste=lambda: ''))
sys.modules.setdefault(
    'rapidfuzz',
    types.SimpleNamespace(
        fuzz=types.SimpleNamespace(ratio=lambda *args, **kwargs: 0, partial_ratio=lambda *args, **kwargs: 0, token_set_ratio=lambda *args, **kwargs: 0),
        process=types.SimpleNamespace(extract=lambda *args, **kwargs: [], extractOne=lambda *args, **kwargs: None),
    ),
)

MODULE_PATH = Path(__file__).resolve().parents[2] / "1.1.0_birha.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("birha_module_t1", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


BIRHA = _load_module()
derive_axiom_category = BIRHA.derive_axiom_category


@pytest.mark.parametrize(
    ("framework", "explicit", "expected"),
    [
        (True, True, "Primary"),
        (True, False, "Secondary"),
        (False, True, "None"),
        (False, False, "None"),
    ],
)
def test_derive_axiom_category(framework, explicit, expected):
    assert derive_axiom_category(framework, explicit) == expected
