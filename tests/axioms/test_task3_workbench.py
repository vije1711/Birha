import importlib.util
import inspect
import os
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import tkinter as tk


MODULE_PATH = Path(__file__).resolve().parents[2] / "1.1.0_birha.py"
HEADLESS_DISPLAY = os.name != "nt" and "DISPLAY" not in os.environ


def _load_birha_module():
    spec = importlib.util.spec_from_file_location("birha_module_t3", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


BIRHA = _load_birha_module()
AxiomsWorkbench = BIRHA.AxiomsWorkbench
AxiomsStore = BIRHA.AxiomsStore
AxiomContribStore = BIRHA.AxiomContribStore
derive_axiom_category = BIRHA.derive_axiom_category
apply_framework_default = BIRHA.apply_framework_default


class AxiomsWorkbenchUITest(unittest.TestCase):
    @unittest.skipIf(HEADLESS_DISPLAY, "no display available")
    def test_headless_smoke(self):
        with TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "1.3.0_axioms.xlsx"
            axioms_store = AxiomsStore(store_path=store_path)
            contrib_store = AxiomContribStore(store_path=store_path)
            root = tk.Tk()
            root.withdraw()
            try:
                window = AxiomsWorkbench(
                    root,
                    axioms_store=axioms_store,
                    contrib_store=contrib_store,
                )
                root.update_idletasks()
                window.destroy()
            finally:
                root.destroy()

    def test_category_badge_mapping(self):
        mapping = {
            (True, True): "Category: Primary",
            (True, False): "Category: Secondary",
            (False, True): "Category: None",
            (False, False): "Category: None",
        }
        for (framework, explicit), expected in mapping.items():
            with self.subTest(framework=framework, explicit=explicit):
                category = derive_axiom_category(framework, explicit)
                badge = AxiomsWorkbench.format_category_badge(category)
                self.assertEqual(badge, expected)

    @unittest.skipIf(HEADLESS_DISPLAY, "no display available")
    def test_store_round_trip_linkage(self):
        with TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "1.3.0_axioms.xlsx"
            axioms_store = AxiomsStore(store_path=store_path)
            contrib_store = AxiomContribStore(store_path=store_path)
            created = axioms_store.create_axiom("Test Workbench Law")
            verse_key = "ang:001-001"
            root = tk.Tk()
            root.withdraw()
            try:
                window = AxiomsWorkbench(
                    root,
                    axioms_store=axioms_store,
                    contrib_store=contrib_store,
                    verse_key=verse_key,
                )
                window.search_axioms("Test Workbench Law")
                linked = window.link_axiom_to_current_verse(
                    created["axiom_id"],
                    category="Primary",
                )
                self.assertIsNotNone(linked)
                contributions = contrib_store.list_contributions(verse_key=verse_key)
                self.assertTrue(
                    any(item.get("axiom_id") == created["axiom_id"] for item in contributions)
                )
                window.destroy()
            finally:
                root.destroy()


    @unittest.skipIf(HEADLESS_DISPLAY, "no display available")
    def test_selection_returns_record(self):
        root = tk.Tk()
        root.withdraw()
        try:
            window = AxiomsWorkbench(root)
            try:
                sample = [{"axiom_id": "AX-TEST", "axiom_law": "Sample Law"}]
                window._populate_results(sample)
                window.results_list.selection_set(0)
                record = window._get_selected_record()
                self.assertEqual(record, sample[0])
            finally:
                window.destroy()
        finally:
            root.destroy()

    def test_existing_function_source_guard(self):
        expectations = {
            "derive_axiom_category": '''def derive_axiom_category(framework: bool, explicit: bool) -> str:
    """Return 'Primary', 'Secondary', or 'None' per contract mapping for later save-path use."""
    if framework and explicit:
        return "Primary"
    if framework and not explicit:
        return "Secondary"
    return "None"''',
            "apply_framework_default": '''def apply_framework_default(record: dict, key: str = "Framework?") -> dict:
    """Return a copy with the framework flag defaulted so GrammarApp save flows can call it before persisting."""
    updated = dict(record)
    if key not in updated or updated[key] is None or updated[key] == "":
        updated[key] = True
    return updated''',
        }
        for name, expected in expectations.items():
            with self.subTest(entry_point=name):
                func = getattr(BIRHA, name)
                source = inspect.getsource(func)
                self.assertEqual(
                    textwrap.dedent(source).strip(),
                    textwrap.dedent(expected).strip(),
                )


if __name__ == "__main__":
    unittest.main()
