import importlib.util
from pathlib import Path

import pandas as pd
import pytest


MODULE_PATH = Path(__file__).resolve().parents[2] / "1.1.0_birha.py"


def _load_birha_module():
    spec = importlib.util.spec_from_file_location("birha_module", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


@pytest.fixture(scope="module")
def birha():
    return _load_birha_module()


@pytest.fixture
def store_path(tmp_path):
    return tmp_path / "1.3.0_axioms.xlsx"


def test_ensure_store_creates_all_sheets_with_headers_in_order(birha, store_path):
    birha.AxiomsStore.ensure_store(store_path)

    with pd.ExcelFile(store_path) as workbook:
        sheet_names = set(workbook.sheet_names)
        expected_sheets = set(birha._AxiomStoreBase.SHEET_SCHEMAS.keys())
        assert sheet_names == expected_sheets
        for sheet, columns in birha._AxiomStoreBase.SHEET_SCHEMAS.items():
            frame = pd.read_excel(workbook, sheet_name=sheet)
            assert list(frame.columns) == list(columns)


def test_create_and_get_axiom_round_trip(birha, store_path):
    store = birha.AxiomsStore(store_path=store_path)

    created = store.create_axiom("Law of Grace")
    fetched = store.get_axiom(created["axiom_id"])

    assert fetched == created
    assert fetched["status"] == "active"
    assert fetched["axiom_law"] == "Law of Grace"


def test_find_axioms_case_insensitive(birha, store_path):
    store = birha.AxiomsStore(store_path=store_path)
    first = store.create_axiom("Path of Mercy")
    store.create_axiom("Guide of Wisdom")

    matches = store.find_axioms("mercy")
    assert any(item["axiom_id"] == first["axiom_id"] for item in matches)


def test_add_and_list_descriptions_with_revision(birha, store_path):
    axioms = birha.AxiomsStore(store_path=store_path)
    axiom = axioms.create_axiom("Law of Kindness")

    desc_store = birha.AxiomDescStore(store_path=store_path)
    desc_store.add_description(
        axiom_id=axiom["axiom_id"],
        type="verse_specific",
        description="Verse insight",
        verse_key="Ang001|1|1|A",
        revision=2,
    )
    desc_store.add_description(
        axiom_id=axiom["axiom_id"],
        type="axiom_specific",
        description="General summary",
        verse_key=None,
        revision=3,
    )

    records = desc_store.list_descriptions(axiom["axiom_id"], type="verse_specific")
    assert len(records) == 1
    assert records[0]["revision"] == 2
    assert records[0]["verse_key"] == "Ang001|1|1|A"


def test_link_contribution_dedup_by_axiom_and_verse_key(birha, store_path):
    axioms = birha.AxiomsStore(store_path=store_path)
    axiom = axioms.create_axiom("Discipline of Courage")

    contrib_store = birha.AxiomContribStore(store_path=store_path)
    first = contrib_store.link_contribution(
        axiom_id=axiom["axiom_id"],
        verse_key="Ang002|1|2|B",
        category="Primary",
        contribution_notes="Initial",
        translation_revision_seen=1,
    )
    second = contrib_store.link_contribution(
        axiom_id=axiom["axiom_id"],
        verse_key="Ang002|1|2|B",
        category="Secondary",
        contribution_notes="Updated",
        translation_revision_seen=3,
    )

    assert first["axiom_id"] == second["axiom_id"]
    assert second["category"] == "Secondary"
    assert second["translation_revision_seen"] == 3

    all_records = contrib_store.list_contributions(axiom_id=axiom["axiom_id"])
    assert len(all_records) == 1


def test_keywords_add_dedup_and_list(birha, store_path):
    axioms = birha.AxiomsStore(store_path=store_path)
    axiom = axioms.create_axiom("Thread of Light")

    keywords_store = birha.AxiomKeywordsStore(store_path=store_path)
    added = keywords_store.add_keywords(
        axiom_id=axiom["axiom_id"],
        bucket="LiteralSyn",
        keywords=["Light", "Illumination", "light"],
        weight=2,
        source="edited",
    )

    assert added == 2

    records = keywords_store.list_keywords(axiom["axiom_id"], bucket="LiteralSyn")
    assert {item["keyword"] for item in records} == {"Light", "Illumination"}
    assert all(item["weight"] == 2 for item in records)


def test_all_sheets_preserve_column_order_on_multiple_saves(birha, store_path):
    axioms = birha.AxiomsStore(store_path=store_path)
    axiom = axioms.create_axiom("Order of Harmony")
    axioms.update_axiom(axiom["axiom_id"], status="deprecated")

    desc_store = birha.AxiomDescStore(store_path=store_path)
    desc_store.add_description(
        axiom_id=axiom["axiom_id"],
        type="axiom_specific",
        description="Shared context",
        verse_key=None,
        revision=0,
    )

    contrib_store = birha.AxiomContribStore(store_path=store_path)
    contrib_store.link_contribution(
        axiom_id=axiom["axiom_id"],
        verse_key="Ang003|1|3|C",
        category="Tertiary",
        contribution_notes="Supportive verse",
        translation_revision_seen=0,
    )

    keywords_store = birha.AxiomKeywordsStore(store_path=store_path)
    keywords_store.add_keywords(
        axiom_id=axiom["axiom_id"],
        bucket="SpiritualSyn",
        keywords=["Harmony"],
    )

    queue_store = birha.AxiomWorkqueueStore(store_path=store_path)
    queue_store.enqueue_or_update(
        verse_key="Ang003|1|3|C",
        status="in_progress",
        translation_revision_seen=1,
    )
    queue_store.enqueue_or_update(
        verse_key="Ang003|1|3|C",
        status="done",
        translation_revision_seen=1,
    )

    with pd.ExcelFile(store_path) as workbook:
        for sheet, columns in birha._AxiomStoreBase.SHEET_SCHEMAS.items():
            frame = pd.read_excel(workbook, sheet_name=sheet)
            assert list(frame.columns) == list(columns)


def test_workqueue_enqueue_and_list(birha, store_path):
    queue_store = birha.AxiomWorkqueueStore(store_path=store_path)
    queue_store.enqueue_or_update(
        verse_key="Ang004|1|4|D",
        status="pending",
        translation_revision_seen=0,
    )
    queue_store.enqueue_or_update(
        verse_key="Ang005|1|5|E",
        status="reanalysis_required",
        translation_revision_seen=5,
    )

    pending = queue_store.list_queue(status="pending")
    assert len(pending) == 1
    assert pending[0]["verse_key"] == "Ang004|1|4|D"

    all_items = queue_store.list_queue()
    assert len(all_items) == 2


def test_csv_export_and_import_helpers(birha, store_path, tmp_path):
    axioms = birha.AxiomsStore(store_path=store_path)
    axiom = axioms.create_axiom("Law of Resonance")

    export_path = tmp_path / "axioms.csv"
    axioms.export_axioms_csv(export_path)
    assert export_path.exists()

    # Import into a fresh store file and ensure record appears
    new_store_path = tmp_path / "copy.xlsx"
    target_store = birha.AxiomsStore(store_path=new_store_path)
    target_store.import_axioms_csv(export_path)
    fetched = target_store.get_axiom(axiom["axiom_id"])
    assert fetched is not None
