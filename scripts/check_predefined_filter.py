import os
import tempfile

from pathlib import Path


def main() -> int:
    # Craft a small CSV with BOM-prefixed first header and mixed Evaluation
    content = (
        "\ufeffVowel Ending,Number / ???,Grammar / ??????,Gender / ???? ,Word Root,Type,Evaluation\n"
        "foo, Singular / ?? ,Nominative / ????, Masculine / ?????? , ROOT1 , Noun / ????, Predefined\n"
        "bar, Singular / ?? ,Nominative / ????, Masculine / ?????? , ROOT1 , Noun / ????, Derived\n"
        "baz, Plural / ??? ,Genitive / ?????, Feminine / ????? , ROOT2 , Pronoun / ??????, Predefined\n"
    )

    # Locate project root (this script lives under scripts/)
    here = Path(__file__).resolve()
    root = here.parent.parent

    # Load module from file path (filename starts with digits)
    import importlib.util
    mod_path = root / "1.1.0_birha.py"
    spec = importlib.util.spec_from_file_location("birha_mod", mod_path)
    if spec is None or spec.loader is None:
        print("Failed to load module spec for 1.1.0_birha.py")
        return 3
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "sample_bom.csv"
        # Write as UTF-8 to keep explicit BOM character on first header token
        p.write_text(content, encoding="utf-8")

        keyset = mod.load_predefined_keyset(str(p))
        # Expect only the two Predefined combos
        expect = {
            ("Singular / ??", "Nominative / ????", "Masculine / ??????", "ROOT1", "Noun / ????"),
            ("Plural / ???", "Genitive / ?????", "Feminine / ?????", "ROOT2", "Pronoun / ??????"),
        }

        if keyset != expect:
            print("Unexpected keyset:\n", keyset)
            return 2

    print("OK: Predefined filter keeps only expected rows and accepts BOM headers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
