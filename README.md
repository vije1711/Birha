# Birha Toolkit

Birha is an experimental toolkit for studying the grammar of Gurbani, the Sikh holy scripture. The main entry point is a Tkinter application (`1.1.0_birha.py`) that provides a dashboard for analysing verses from the *Sri Guru Granth Sahib* (SGGS), updating grammar entries and reviewing literal translations.

Data files included in the repository:

- `1.1.0_birha.py` – Python application with a GUI for verse analysis, grammar classification and literal meaning work.
- `1.1.1_birha.csv` – core grammar database with information such as vowel endings, number, gender and source verses.
- `1.1.2 Grammatical Meanings Dictionary.csv` – dictionary mapping Punjabi words to lists of meanings.
- `1.1.3 sggs_extracted_with_page_numbers.xlsx` – spreadsheet of SGGS verses including page numbers used for lookups.
- `1.2.1 assessment_data.xlsx` – worksheet tracking manual assessments from the application.

## Requirements

The project targets Python 3.  Exact dependency versions are pinned in `requirements.txt` and can be installed with:

```bash
pip install -r requirements.txt
```

This installs packages such as `pandas`, `numpy`, `rapidfuzz`, `pyperclip` and `openpyxl` (for Excel file support).  `tkinter`
ships with most Python distributions.

## Usage

Run the Tkinter application from the repository root:

```bash
python 1.1.0_birha.py
```

The dashboard window provides buttons to analyse SGGS verses, update the grammar database and work with literal translations.

## Status

This repository is a work in progress. The datasets and interface are subject to change as the grammar resources evolve.
