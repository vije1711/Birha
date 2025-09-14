import importlib.util
from pathlib import Path


def load_module():
    mod_path = (Path(__file__).resolve().parents[1] / '1.1.0_birha.py').resolve()
    spec = importlib.util.spec_from_file_location('birha_mod', str(mod_path))
    assert spec and spec.loader, f"Cannot load module from {mod_path}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def assert_eq(a, b):
    if a != b:
        raise AssertionError(f"Expected {b!r}, got {a!r}")


def main():
    mod = load_module()
    st = getattr(mod, '_strip_terminators')

    # Basic: dandas
    assert_eq(st('ਨਿਰਵੈਰੁ॥'), 'ਨਿਰਵੈਰੁ')
    assert_eq(st('ਨਿਰਵੈਰੁ।'), 'ਨਿਰਵੈਰੁ')
    assert_eq(st('ਨਿਰਵੈਰੁ॥    '), 'ਨਿਰਵੈਰੁ')

    # Mixed punctuation
    assert_eq(st('ਸਤਿ ਨਾਮੁ ਕਰਤਾ ਪੁਰਖੁ ਨਿਰਭਉ ਨਿਰਵੈਰੁ?!'), 'ਸਤਿ ਨਾਮੁ ਕਰਤਾ ਪੁਰਖੁ ਨਿਰਭਉ ਨਿਰਵੈਰੁ')
    assert_eq(st('ਸਤਿ ਨਾਮੁ ਕਰਤਾ ਪੁਰਖੁ, ਨਿਰਭਉ ਨਿਰਵੈਰੁ?'), 'ਸਤਿ ਨਾਮੁ ਕਰਤਾ ਪੁਰਖੁ, ਨਿਰਭਉ ਨਿਰਵੈਰੁ')

    # Fullwidth variants
    assert_eq(st('… ਨਿਰਵੈਰੁ？'), '… ਨਿਰਵੈਰੁ')
    assert_eq(st('… ਨਿਰਵੈਰੁ！'), '… ਨਿਰਵੈਰੁ')

    # Interior punctuation preserved
    text = 'ਕਰਤਾ, ਪੁਰਖੁ ਨਿਰਭਉ; ਨਿਰਵੈਰੁ:'
    assert_eq(st(text), 'ਕਰਤਾ, ਪੁਰਖੁ ਨਿਰਭਉ; ਨਿਰਵੈਰੁ')

    print('OK: _strip_terminators tests passed')


if __name__ == '__main__':
    main()

