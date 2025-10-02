import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd


MODULE_PATH = Path(__file__).resolve().parents[2] / "1.1.0_birha.py"



def _load_birha_module():
    spec = importlib.util.spec_from_file_location("birha_module_t8", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


BIRHA = _load_birha_module()
create_axiom = BIRHA.create_axiom
link_contribution = BIRHA.link_contribution
save_description = BIRHA.save_description
build_description_prompt = BIRHA.build_description_prompt
_normalize_verse_key = BIRHA._normalize_verse_key
AxiomDescStore = BIRHA.AxiomDescStore


class AxiomDescriptionsEngineTest(unittest.TestCase):
    COLUMNS = [
        "Verse", "Translation", "Translation Revision",
        "Word", "Selected Darpan Meaning", "Grammar / ??????", "Type", "Number / ???", "Gender / ????",
        "Framework?", "Explicit?",
    ]

    @staticmethod
    def _write_assessment(path: Path, rows: list[dict]) -> None:
        df = pd.DataFrame(rows, columns=AxiomDescriptionsEngineTest.COLUMNS)
        df.to_excel(path, index=False)

    def test_save_description_handles_revisions(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            store_path = tmp / "1.3.0_axioms.xlsx"

            axiom = create_axiom("Test Law", store_path=store_path)
            verse_key = "ang:050-001"

            first = save_description(
                axiom["axiom_id"],
                type="axiom_specific",
                text="Initial description",
                store_path=store_path,
            )
            self.assertEqual(first["revision"], 0)

            updated = save_description(
                axiom["axiom_id"],
                type="axiom_specific",
                text="Updated description",
                store_path=store_path,
            )
            self.assertEqual(updated["revision"], 1)

            verse_saved = save_description(
                axiom["axiom_id"],
                type="verse_specific",
                verse_key=verse_key,
                text="Verse description",
                store_path=store_path,
            )
            self.assertEqual(verse_saved["revision"], 0)

            # Re-saving same text should not increment revision
            verse_saved_again = save_description(
                axiom["axiom_id"],
                type="verse_specific",
                verse_key=verse_key,
                text="Verse description",
                store_path=store_path,
            )
            self.assertEqual(verse_saved_again["revision"], 0)

    def test_save_description_requires_normalizable_verse_key(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            store_path = tmp / "1.3.0_axioms.xlsx"
            axiom = create_axiom("Law", store_path=store_path)

            with self.assertRaises(ValueError):
                save_description(
                    axiom["axiom_id"],
                    type="verse_specific",
                    verse_key=None,
                    text="Missing key",
                    store_path=store_path,
                )

            with self.assertRaises(ValueError):
                save_description(
                    axiom["axiom_id"],
                    type="verse_specific",
                    verse_key="   ",
                    text="Blank key",
                    store_path=store_path,
                )

    def test_build_description_prompt_includes_context(self):
        with TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            store_path = tmp / "1.3.0_axioms.xlsx"
            assessment_path = tmp / "1.2.1 assessment_data.xlsx"

            verse_text = "??? ???"
            normalized = _normalize_verse_key(verse_text)

            self._write_assessment(
                assessment_path,
                [
                    {
                        "Verse": verse_text,
                        "Translation": "True in the primal beginning",
                        "Translation Revision": 2,
                        "Word": "???",
                        "Selected Darpan Meaning": "primal",
                        "Grammar / ??????": "Adverb",
                        "Type": "Adverb / ????? ??????",
                        "Number / ???": "NA",
                        "Gender / ????": "NA",
                        "Framework?": True,
                        "Explicit?": False,
                    }
                ],
            )

            axiom = create_axiom("Eternal Truth Law", store_path=store_path)
            link_contribution(
                axiom["axiom_id"],
                normalized,
                category="Primary",
                store_path=store_path,
            )

            save_description(
                axiom["axiom_id"],
                type="axiom_specific",
                text="Axiom wide description",
                store_path=store_path,
            )
            save_description(
                axiom["axiom_id"],
                type="verse_specific",
                verse_key=normalized,
                text="Verse specific detail",
                store_path=store_path,
            )

            prompt = build_description_prompt(
                axiom["axiom_id"],
                verse_key=normalized,
                assessment_path=assessment_path,
                store_path=store_path,
            )

            self.assertIn("Description Update for Axiom", prompt)
            self.assertIn("Axiom-Specific", prompt)
            self.assertIn("Verse-Specific", prompt)
            self.assertIn("True in the primal beginning", prompt)
            self.assertIn("Linked Verses", prompt)


if __name__ == "__main__":
    unittest.main()
