import pandas as pd
from build_lexicon import build_lexicon_from_df


def main():
    # Create a small DF with one valid verse and one NaN verse
    df = pd.DataFrame({
        'S. No.': [1, 2],
        'Verse': ['ਸਤਿ ਨਾਮੁ', float('nan')],
    })

    payload = build_lexicon_from_df(df)
    counts = payload['counts']

    assert 'nan' not in counts, "NaN verse incorrectly tokenized as 'nan'"
    assert 'ਸਤਿ' in counts or 'ਨਾਮੁ' in counts, "Valid verse tokens missing"
    print('OK: NaN verse rows are skipped; no "nan" token present.')


if __name__ == '__main__':
    main()

