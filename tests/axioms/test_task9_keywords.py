import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


MODULE_PATH = Path(__file__).resolve().parents[2] / "1.1.0_birha.py"


def _load_birha_module():
    spec = importlib.util.spec_from_file_location("birha_module_t9", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


BIRHA = _load_birha_module()
merge_keywords = BIRHA.merge_keywords
delete_keyword = BIRHA.delete_keyword
build_keywords_prompt = BIRHA.build_keywords_prompt
_cross_axiom_keyword_density = BIRHA._cross_axiom_keyword_density
AxiomKeywordsStore = BIRHA.AxiomKeywordsStore


class KeywordManagerTask9Test(unittest.TestCase):
    def test_merge_keywords_adds_and_dedupes(self):
        with TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "1.3.0_axioms.xlsx"
            result = merge_keywords(
                "AX-TARGET",
                "LiteralSyn",
                ["Truth", "truth", "Sat", " Sat "],
                store_path=store_path,
            )
            self.assertEqual(len(result), 2)
            keywords = {entry["keyword"] for entry in result}
            self.assertEqual(keywords, {"Truth", "Sat"})

    def test_merge_keywords_filters_stopwords_and_short_tokens(self):
        with TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "1.3.0_axioms.xlsx"
            result = merge_keywords(
                "AX-FILTER",
                "SpiritualSyn",
                ["and", "of", "Om", "Ik", "Naam"],
                store_path=store_path,
            )
            keywords = {entry["keyword"] for entry in result}
            self.assertEqual(keywords, {"Naam"})

    def test_delete_keyword_removes_entry(self):
        with TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "1.3.0_axioms.xlsx"
            merge_keywords(
                "AX-DEL",
                "LiteralSyn",
                ["Naam"],
                store_path=store_path,
            )
            self.assertTrue(
                delete_keyword(
                    "AX-DEL",
                    "LiteralSyn",
                    "Naam",
                    store_path=store_path,
                )
            )
            store = AxiomKeywordsStore(store_path=store_path)
            remaining = store.list_keywords("AX-DEL", "LiteralSyn")
            self.assertFalse(remaining)
            self.assertFalse(
                delete_keyword(
                    "AX-DEL",
                    "LiteralSyn",
                    "Naam",
                    store_path=store_path,
                )
            )

    def test_build_keywords_prompt_includes_current_and_warnings(self):
        with TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "1.3.0_axioms.xlsx"
            target_axiom = "AX-WARN"
            merge_keywords(
                target_axiom,
                "LiteralSyn",
                ["Naam", "Satnam"],
                store_path=store_path,
            )
            store = AxiomKeywordsStore(store_path=store_path)
            for idx in range(5):
                store.add_keywords(
                    f"AX-OTHER-{idx}",
                    "LiteralSyn",
                    ["Naam"],
                )

            prompt = build_keywords_prompt(
                target_axiom,
                "LiteralSyn",
                store_path=store_path,
            )

            self.assertIn("## Current Keywords", prompt)
            self.assertIn("Naam", prompt)
            self.assertIn("## Warnings", prompt)
            self.assertIn("appears in 6 axioms", prompt)

    def test_cross_axiom_density_check(self):
        with TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "1.3.0_axioms.xlsx"
            store = AxiomKeywordsStore(store_path=store_path)
            keywords = ["Simran", " simran ", "Simran"]
            for idx, token in enumerate(keywords):
                store.add_keywords(
                    f"AX-DEN-{idx}",
                    "SpiritualSyn",
                    [token],
                )

            count = _cross_axiom_keyword_density(
                "Simran",
                store_path=store_path,
            )
            self.assertEqual(count, 3)


if __name__ == "__main__":
    unittest.main()
