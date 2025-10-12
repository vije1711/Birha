import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd


MODULE_PATH = Path(__file__).resolve().parents[2] / "1.1.0_birha.py"


def _load_birha_module():
    spec = importlib.util.spec_from_file_location("birha_module_t7", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


BIRHA = _load_birha_module()
build_axiom_finalization_prompt = BIRHA.build_axiom_finalization_prompt
create_axiom = BIRHA.create_axiom
link_contribution = BIRHA.link_contribution
_normalize_verse_key = BIRHA._normalize_verse_key


class AxiomFinalizePromptTest(unittest.TestCase):
    COLUMNS = [
        "Verse", "Translation", "Translation Revision",
        "Word", "Selected Darpan Meaning", "Grammar / ??????", "Type", "Number / ???", "Gender / ????",
        "Framework?", "Explicit?",
    ]

    @staticmethod
    def _write_assessment(path: Path, rows: list[dict]) -> None:
        df = pd.DataFrame(rows, columns=AxiomFinalizePromptTest.COLUMNS)
        df.to_excel(path, index=False)

    def test_prompt_includes_context_and_contributions(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            assessment_path = tmp / "1.2.1 assessment_data.xlsx"
            store_path = tmp / "1.3.0_axioms.xlsx"

            verse_text = "??? ???? ???? ?????"
            normalized = _normalize_verse_key(verse_text)

            rows = [
                {
                    "Verse": verse_text,
                    "Translation": "The True Name is the Creative Being",
                    "Translation Revision": 3,
                    "Word": "???",
                    "Selected Darpan Meaning": "truth",
                    "Grammar / ??????": "Noun",
                    "Type": "Noun / ???",
                    "Number / ???": "Singular",
                    "Gender / ????": "Masculine",
                    "Framework?": True,
                    "Explicit?": True,
                },
                {
                    "Verse": verse_text,
                    "Translation": "The True Name is the Creative Being",
                    "Translation Revision": 3,
                    "Word": "?????",
                    "Selected Darpan Meaning": "being",
                    "Grammar / ??????": "Noun",
                    "Type": "Noun / ???",
                    "Number / ???": "Singular",
                    "Gender / ????": "Masculine",
                    "Framework?": True,
                    "Explicit?": True,
                },
            ]
            self._write_assessment(assessment_path, rows)

            axiom_primary = create_axiom("True Name Law", store_path=store_path)
            create_axiom("Meditation Law", store_path=store_path)

            link_contribution(
                axiom_primary["axiom_id"],
                normalized,
                category="Primary",
                notes="Aligns verse focus with primary law",
                store_path=store_path,
            )

            prompt = build_axiom_finalization_prompt(
                normalized,
                assessment_path=assessment_path,
                store_path=store_path,
                include_catalog_rows=5,
            )

            self.assertIn("Finalize Axiom(s) for Verse", prompt)
            self.assertIn("The True Name is the Creative Being", prompt)
            self.assertIn("Framework?: Yes", prompt)
            self.assertIn("Explicit?: Yes", prompt)
            self.assertIn("Existing Axiom Links", prompt)
            self.assertIn("True Name Law", prompt)
            self.assertIn("Guidance for Analyst", prompt)

    def test_prompt_handles_unlinked_verse(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            assessment_path = tmp / "1.2.1 assessment_data.xlsx"
            store_path = tmp / "1.3.0_axioms.xlsx"

            verse_text = "?????? ????"
            normalized = _normalize_verse_key(verse_text)

            rows = [
                {
                    "Verse": verse_text,
                    "Translation": "Dhanasari Mahalla",
                    "Translation Revision": 1,
                    "Word": "??????",
                    "Selected Darpan Meaning": "raag",
                    "Grammar / ??????": "Noun",
                    "Type": "Noun / ???",
                    "Number / ???": "Singular",
                    "Gender / ????": "Feminine",
                    "Framework?": True,
                    "Explicit?": False,
                },
            ]
            self._write_assessment(assessment_path, rows)

            prompt = build_axiom_finalization_prompt(
                normalized,
                assessment_path=assessment_path,
                store_path=store_path,
                include_catalog_rows=0,
            )

            self.assertIn("None linked yet", prompt)
            self.assertIn("Explicit?: No", prompt)
            self.assertIn("Catalog is empty", prompt)


if __name__ == "__main__":
    unittest.main()
