# Birha Toolkit

Birha is an experimental collection of utilities and datasets for studying the grammar of Gurbani, the Sikh holy scripture. The project centres around a Tkinter application (`1.1.0_birha.py`) that lets scholars analyse verses from the *Sri Guru Granth Sahib* (SGGS), match them against a grammar database and refine word-level entries.

The repository currently contains:

- `1.1.0_birha.py` – Python application with a GUI for verse selection, grammar classification and literal meaning analysis.
- `1.1.1_birha.csv` – core grammar database with information such as vowel endings, number, gender and source verses.
- `1.1.2 Grammatical Meanings Dictionary.csv` – dictionary mapping Punjabi words to lists of meanings.
- `1.1.3 sggs_extracted_with_page_numbers.xlsx` – spreadsheet of SGGS verses including page numbers used for lookups.
- `1.2.1 assessment_data.xlsx` – worksheet tracking manual assessments from the application.

## Requirements

The application uses Python 3 and the following packages:

- `pandas`
- `numpy`
- `rapidfuzz`
- `pyperclip`
- `tkinter` (bundled with most Python installations)

Install dependencies with `pip install pandas numpy rapidfuzz pyperclip`.

## Usage

Run the Tkinter application from the repository root:

```bash
python 1.1.0_birha.py
```

The dashboard window provides buttons to analyse SGGS verses, update the grammar database and work with literal translations.

## Status

This repository is a work in progress. The datasets and interface are subject to change as the grammar resources evolve.
