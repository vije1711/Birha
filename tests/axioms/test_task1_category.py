"""Tests for Axioms T1 helpers so future save flows can plug them in before persistence."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, Callable

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "1.1.0_birha.py"
TARGET_FUNCTIONS = {"derive_axiom_category", "apply_framework_default"}


@pytest.fixture(scope="module")
def axioms_helpers() -> Dict[str, Callable]:
    """Extract additive helper functions from the Birha module via AST without side effects."""
    source = MODULE_PATH.read_text(encoding="cp1252")
    module_ast = ast.parse(source, filename=str(MODULE_PATH))

    helpers: Dict[str, Callable] = {}
    for node in module_ast.body:
        if isinstance(node, ast.FunctionDef) and node.name in TARGET_FUNCTIONS:
            stub_module = ast.Module(body=[node], type_ignores=[])
            ast.fix_missing_locations(stub_module)
            exec(compile(stub_module, str(MODULE_PATH), "exec"), helpers)

    missing = TARGET_FUNCTIONS.difference(helpers)
    assert not missing, f"Expected helpers missing from source: {sorted(missing)}"
    return helpers


@pytest.mark.parametrize(
    ("framework", "explicit", "expected"),
    [
        (True, True, "Primary"),
        (True, False, "Secondary"),
        (False, True, "None"),
        (False, False, "None"),
    ],
)
def test_derive_axiom_category_pairs(axioms_helpers, framework, explicit, expected):
    derive = axioms_helpers["derive_axiom_category"]
    assert derive(framework, explicit) == expected


def test_apply_framework_default_adds_flag_when_missing(axioms_helpers):
    apply_default = axioms_helpers["apply_framework_default"]
    source = {"Axiom": "Sehaj"}
    result = apply_default(source)

    assert result is not source
    assert result["Framework?"] is True
    assert "Framework?" not in source


def test_apply_framework_default_handles_none(axioms_helpers):
    apply_default = axioms_helpers["apply_framework_default"]
    source = {"Framework?": None}
    result = apply_default(source)

    assert result is not source
    assert result["Framework?"] is True
    assert source["Framework?"] is None


def test_apply_framework_default_handles_empty_string(axioms_helpers):
    apply_default = axioms_helpers["apply_framework_default"]
    source = {"Framework?": ""}
    result = apply_default(source)

    assert result is not source
    assert result["Framework?"] is True
    assert source["Framework?"] == ""


def test_apply_framework_default_preserves_true(axioms_helpers):
    apply_default = axioms_helpers["apply_framework_default"]
    source = {"Framework?": True}
    result = apply_default(source)

    assert result is not source
    assert result["Framework?"] is True
    assert source["Framework?"] is True


def test_apply_framework_default_preserves_false(axioms_helpers):
    apply_default = axioms_helpers["apply_framework_default"]
    source = {"Framework?": False}
    result = apply_default(source)

    assert result is not source
    assert result["Framework?"] is False
    assert source["Framework?"] is False
