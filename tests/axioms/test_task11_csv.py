import importlib.util
import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

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
    spec = importlib.util.spec_from_file_location("birha_module_t11", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


BIRHA = _load_module()
export_axioms_csv = BIRHA.export_axioms_csv
import_axioms_csv = BIRHA.import_axioms_csv
AxiomsStore = BIRHA.AxiomsStore
create_axiom = BIRHA.create_axiom
link_contribution = BIRHA.link_contribution
save_description = BIRHA.save_description
merge_keywords = BIRHA.merge_keywords
AxiomWorkqueueStore = BIRHA.AxiomWorkqueueStore

EXPECTED_FILES = {
    "Axioms.csv",
    "AxiomContributions.csv",
    "AxiomDescriptions.csv",
    "AxiomKeywords.csv",
    "AxiomWorkqueue.csv",
}


class AxiomCsvBridgeTest(unittest.TestCase):
    @staticmethod
    def _init_store(tmp_dir: Path) -> Path:
        store_path = tmp_dir / "1.3.0_axioms.xlsx"
        AxiomsStore.ensure_store(store_path=store_path)
        return store_path

    def test_export_creates_all_csv_files(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            store_path = self._init_store(tmp_path)
            axiom = create_axiom("Law One", store_path=store_path)
            link_contribution(
                axiom["axiom_id"],
                "ang:001-0001",
                category="Primary",
                store_path=store_path,
            )

            export_dir = tmp_path / "export"
            exported = export_axioms_csv(export_dir, store_path=store_path)
            exported_names = {path.name for path in exported}
            self.assertEqual(exported_names, EXPECTED_FILES)

            for name in EXPECTED_FILES:
                csv_path = export_dir / name
                self.assertTrue(csv_path.exists())
                df = pd.read_csv(csv_path, dtype=object)
                expected_headers = list(AxiomsStore.SHEET_SCHEMAS[name[:-4]])
                self.assertEqual(list(df.columns), expected_headers)

    def test_import_rejects_invalid_headers(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            store_path = self._init_store(tmp_path)
            create_axiom("Law Two", store_path=store_path)
            export_dir = tmp_path / "export"
            export_axioms_csv(export_dir, store_path=store_path)

            axioms_path = export_dir / "Axioms.csv"
            lines = axioms_path.read_text(encoding="utf-8").splitlines()
            lines[0] = lines[0].replace("axiom_id", "bad_column", 1)
            axioms_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                import_axioms_csv(export_dir, store_path=store_path)

    def test_roundtrip_export_import(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            store_path = self._init_store(tmp_path)
            axiom = create_axiom("Law Three", store_path=store_path)
            link_contribution(
                axiom["axiom_id"],
                "ang:002-0001",
                category="Primary",
                store_path=store_path,
            )
            save_description(
                axiom["axiom_id"],
                type="axiom_specific",
                text="Description",
                store_path=store_path,
            )
            merge_keywords(
                axiom["axiom_id"],
                "LiteralSyn",
                ["Truth"],
                store_path=store_path,
            )
            queue_store = AxiomWorkqueueStore(store_path=store_path)
            queue_store.enqueue_or_update(
                verse_key="ang:002-0001",
                status="pending",
                translation_revision_seen=1,
            )

            export_dir_one = tmp_path / "export1"
            export_axioms_csv(export_dir_one, store_path=store_path)

            import_axioms_csv(export_dir_one, store_path=store_path)

            export_dir_two = tmp_path / "export2"
            export_axioms_csv(export_dir_two, store_path=store_path)

            for name in EXPECTED_FILES:
                first = (export_dir_one / name).read_bytes()
                second = (export_dir_two / name).read_bytes()
                self.assertEqual(second, first, name)

    def test_empty_sheet_exports_with_headers_only(self):
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            store_path = self._init_store(tmp_path)
            export_dir = tmp_path / "export"
            export_axioms_csv(export_dir, store_path=store_path)

            for name in EXPECTED_FILES:
                csv_path = export_dir / name
                content = csv_path.read_text(encoding="utf-8")
                lines = [line for line in content.splitlines() if line or line == ""]
                expected_headers = ",".join(AxiomsStore.SHEET_SCHEMAS[name[:-4]])
                self.assertTrue(lines, name)
                self.assertEqual(lines[0], expected_headers)
                self.assertLessEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main()
