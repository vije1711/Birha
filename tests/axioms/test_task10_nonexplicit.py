import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

MODULE_PATH = Path(__file__).resolve().parents[2] / "1.1.0_birha.py"


def _load_birha_module():
    spec = importlib.util.spec_from_file_location("birha_module_t10", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


BIRHA = _load_birha_module()
create_axiom = BIRHA.create_axiom
link_contribution = BIRHA.link_contribution
find_candidate_primaries = BIRHA.find_candidate_primaries
link_secondary_to_primary = BIRHA.link_secondary_to_primary
AxiomContribStore = BIRHA.AxiomContribStore
_normalize_verse_key = BIRHA._normalize_verse_key


class NonExplicitLinkingTaskTest(unittest.TestCase):
    def test_link_secondary_requires_primary(self):
        with TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "1.3.0_axioms.xlsx"
            with self.assertRaises(ValueError):
                link_secondary_to_primary("ang:ik oankar", [], store_path=store_path)

    def test_link_secondary_to_single_primary(self):
        with TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "1.3.0_axioms.xlsx"
            primary_axiom = create_axiom("Truth Law", store_path=store_path)
            primary_key = "ang:satnam ji"
            link_contribution(
                primary_axiom["axiom_id"],
                primary_key,
                category="Primary",
                store_path=store_path,
            )

            secondary_key = "ang:ik oankar"
            link_secondary_to_primary(
                secondary_key,
                [primary_key],
                store_path=store_path,
            )

            contrib_store = AxiomContribStore(store_path=store_path)
            records = contrib_store.list_contributions(axiom_id=primary_axiom["axiom_id"])
            normalized_secondary = _normalize_verse_key(secondary_key)
            normalized_primary = _normalize_verse_key(primary_key)
            matches = [r for r in records if r.get("verse_key") == normalized_secondary]
            self.assertEqual(len(matches), 1)
            record = matches[0]
            self.assertEqual(record.get("category"), "Secondary")
            self.assertEqual(record.get("is_supporting_of"), normalized_primary)

    def test_link_secondary_to_multiple_primaries(self):
        with TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "1.3.0_axioms.xlsx"
            primary_one = create_axiom("Law One", store_path=store_path)
            primary_two = create_axiom("Law Two", store_path=store_path)

            primary_key_one = "ang:satnam ji"
            primary_key_two = "ang:waheguru simran"

            link_contribution(
                primary_one["axiom_id"],
                primary_key_one,
                category="Primary",
                store_path=store_path,
            )
            link_contribution(
                primary_two["axiom_id"],
                primary_key_two,
                category="Primary",
                store_path=store_path,
            )

            secondary_key = "ang:sevadar spirit"
            link_secondary_to_primary(
                secondary_key,
                [primary_key_one, primary_key_two],
                store_path=store_path,
            )

            contrib_store = AxiomContribStore(store_path=store_path)
            records = contrib_store.list_contributions()
            normalized_secondary = _normalize_verse_key(secondary_key)
            matching = [
                (r.get("axiom_id"), r.get("is_supporting_of"))
                for r in records
                if r.get("verse_key") == normalized_secondary and r.get("category") == "Secondary"
            ]
            self.assertEqual(len(matching), 2)
            self.assertIn(_normalize_verse_key(primary_key_one), {m[1] for m in matching})
            self.assertIn(_normalize_verse_key(primary_key_two), {m[1] for m in matching})

    def test_link_secondary_same_verse_different_axioms(self):
        with TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "1.3.0_axioms.xlsx"
            axiom_one = create_axiom("Unified Law A", store_path=store_path)
            axiom_two = create_axiom("Unified Law B", store_path=store_path)

            shared_primary = "ang:truth beacon"

            link_contribution(
                axiom_one["axiom_id"],
                shared_primary,
                category="Primary",
                store_path=store_path,
            )
            link_contribution(
                axiom_two["axiom_id"],
                shared_primary,
                category="Primary",
                store_path=store_path,
            )

            primaries = find_candidate_primaries(store_path=store_path)
            selected = [
                record
                for record in primaries
                if record.get("axiom_id") in {axiom_one["axiom_id"], axiom_two["axiom_id"]}
            ]
            self.assertEqual(len(selected), 2)

            secondary_key = "ang:devotee reflection"
            link_secondary_to_primary(
                secondary_key,
                selected,
                store_path=store_path,
            )

            contrib_store = AxiomContribStore(store_path=store_path)
            normalized_secondary = _normalize_verse_key(secondary_key)
            records = contrib_store.list_contributions()
            secondary_rows = [
                r
                for r in records
                if r.get("verse_key") == normalized_secondary and r.get("category") == "Secondary"
            ]
            self.assertEqual(len(secondary_rows), 2)
            axiom_ids = {r.get("axiom_id") for r in secondary_rows}
            self.assertEqual(axiom_ids, {axiom_one["axiom_id"], axiom_two["axiom_id"]})
            self.assertTrue(all(r.get("is_supporting_of") == _normalize_verse_key(shared_primary) for r in secondary_rows))

    def test_detect_circular_reference(self):
        with TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "1.3.0_axioms.xlsx"

            axiom_a = create_axiom("Axiom A", store_path=store_path)
            axiom_b = create_axiom("Axiom B", store_path=store_path)
            axiom_c = create_axiom("Axiom C", store_path=store_path)

            key_a = "ang:truth luminous"
            key_b = "ang:divine command"
            key_c = "ang:grace flows"

            link_contribution(axiom_a["axiom_id"], key_a, category="Primary", store_path=store_path)
            link_contribution(axiom_b["axiom_id"], key_b, category="Primary", store_path=store_path)
            link_contribution(axiom_c["axiom_id"], key_c, category="Primary", store_path=store_path)

            link_secondary_to_primary(key_c, [key_a], store_path=store_path)
            link_secondary_to_primary(key_a, [key_b], store_path=store_path)

            with self.assertRaises(ValueError):
                link_secondary_to_primary(
                    key_b,
                    [key_c],
                    store_path=store_path,
                )

    def test_find_candidate_primaries_returns_only_primary(self):
        with TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "1.3.0_axioms.xlsx"
            primary_axiom = create_axiom("Primary Law", store_path=store_path)
            supporting_axiom = create_axiom("Supporting Law", store_path=store_path)

            primary_key = "ang:primary focus"
            secondary_key = "ang:secondary note"

            link_contribution(
                primary_axiom["axiom_id"],
                primary_key,
                category="Primary",
                store_path=store_path,
            )
            link_contribution(
                supporting_axiom["axiom_id"],
                secondary_key,
                category="Secondary",
                store_path=store_path,
            )

            primaries = find_candidate_primaries(store_path=store_path)
            verse_keys = {entry.get("verse_key") for entry in primaries}
            self.assertEqual(verse_keys, {_normalize_verse_key(primary_key)})


if __name__ == "__main__":
    unittest.main()
