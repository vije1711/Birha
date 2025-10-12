import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


MODULE_PATH = Path(__file__).resolve().parents[2] / "1.1.0_birha.py"


def _load_birha_module():
    spec = importlib.util.spec_from_file_location("birha_module_t6", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


BIRHA = _load_birha_module()
create_axiom = BIRHA.create_axiom
find_axioms = BIRHA.find_axioms
update_axiom = BIRHA.update_axiom
link_contribution = BIRHA.link_contribution
link_contributions_bulk = BIRHA.link_contributions_bulk
AxiomContribStore = BIRHA.AxiomContribStore


class AxiomCatalogCrudTest(unittest.TestCase):
    def test_create_find_and_update_axioms(self):
        with TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "1.3.0_axioms.xlsx"
            created = create_axiom("Divine Law", store_path=store_path)
            self.assertTrue(created["axiom_id"].startswith("AX-"))
            self.assertEqual(created["status"], "active")

            create_axiom("Secondary Law", store_path=store_path)
            matches = find_axioms("law", store_path=store_path)
            self.assertEqual(len(matches), 2)

            limited = find_axioms("law", store_path=store_path, limit=1)
            self.assertEqual(len(limited), 1)

            updated = update_axiom(
                created["axiom_id"],
                law_text="Divine Law Revised",
                status="deprecated",
                store_path=store_path,
            )
            self.assertEqual(updated["axiom_law"], "Divine Law Revised")
            self.assertEqual(updated["status"], "deprecated")

    def test_link_contribution_prevents_duplicates_and_supports_multiple_axioms(self):
        with TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "1.3.0_axioms.xlsx"
            ax_primary = create_axiom("Primary Guidance", store_path=store_path)
            ax_support = create_axiom("Supporting Guidance", store_path=store_path)
            verse_key = "ang:001-001"

            first = link_contribution(
                ax_primary["axiom_id"],
                verse_key,
                category="Primary",
                notes="initial",
                store_path=store_path,
            )
            self.assertEqual(first["category"], "Primary")

            # Duplicate link updates rather than creating a second row
            duplicate = link_contribution(
                ax_primary["axiom_id"],
                verse_key,
                category="Primary",
                notes="updated",
                store_path=store_path,
            )
            self.assertEqual(duplicate["contribution_notes"], "updated")

            # Same verse can link to a different axiom
            secondary = link_contribution(
                ax_support["axiom_id"],
                verse_key,
                category="Secondary",
                store_path=store_path,
            )
            self.assertEqual(secondary["category"], "Secondary")

            records = AxiomContribStore(store_path=store_path).list_contributions(verse_key=verse_key)
            self.assertEqual(len(records), 2)

            # Bulk helper ignores empty inputs but links valid entries
            additional = link_contributions_bulk(
                ax_support["axiom_id"],
                [verse_key, " ", "ang:001-002"],
                category="Secondary",
                store_path=store_path,
            )
            self.assertEqual(len(additional), 2)
            records_all = AxiomContribStore(store_path=store_path).list_contributions(axiom_id=ax_support["axiom_id"])
            self.assertEqual(len(records_all), 2)


if __name__ == "__main__":
    unittest.main()
