# CSV Expense Normalizer

Dependency-free Python CSV expense normalizer located in `connector_acceptance_20261120/`.

## Overview

This module normalizes expense CSV files with columns `date`, `merchant`, and `amount`:

- **Dates** are normalized to ISO 8601 format `YYYY-MM-DD`, accepting common input variants (e.g., `2023/01/15`, `01/15/2023`, `2023-1-5`, `Jan 15, 2023`) and rejecting invalid dates with a clear `ValueError: Invalid date: ...`.
- **Merchants** are trimmed of leading/trailing whitespace (Unicode-aware via `str.strip()`); empty or whitespace-only values raise `ValueError: Missing merchant: ...`.
- **Amounts** are parsed using `Decimal` and quantized to two decimal places with `ROUND_HALF_UP` (e.g., `1.005` → `1.01`, `2.675` → `2.68`), stripping currency symbols (`$`, `€`, `£`, etc.) and commas; invalid amounts raise `ValueError: Invalid amount: ...`.
- **Row order** is preserved exactly as input.
- No external dependencies beyond the Python standard library.

## Structure

```
connector_acceptance_20261120/
├── normalizer.py        # Core normalization logic
├── test_normalizer.py   # unittest suite (≥6 cases)
├── fixtures/
│   └── input.csv        # Example input CSV
└── README.md            # This file
```

## Requirements

- Python 3.8+ (uses `pathlib`, `typing`, `decimal`, `csv`, `datetime`)
- No third-party packages

## Usage

### As a library

```python
from normalizer import normalize_csv, normalize_row, normalize_date, normalize_merchant, normalize_amount

# File-to-file
normalize_csv("fixtures/input.csv", "output.csv")

# File-to-list (no output path returns normalized rows)
rows = normalize_csv("fixtures/input.csv")
# rows = [
#   {"date": "2023-01-15", "merchant": "Starbucks", "amount": "4.50"},
#   {"date": "2023-01-20", "merchant": "Café Müller", "amount": "12.35"},
#   ...
# ]

# Single row
normalize_row({"date": "01/15/2023", "merchant": "  Starbucks ", "amount": "$1,234.5"})
# -> {"date": "2023-01-15", "merchant": "Starbucks", "amount": "1234.50"}

# Individual helpers
normalize_date("2023/01/15")        # "2023-01-15"
normalize_merchant("  東京商店 ")     # "東京商店"
normalize_amount("1.005")           # "1.01" (ROUND_HALF_UP)
```

### CLI

```bash
python normalizer.py fixtures/input.csv -o output.csv
python normalizer.py fixtures/input.csv  # writes normalized CSV to stdout
```

### Fixture Example

`fixtures/input.csv`:

```csv
date,merchant,amount
2023-01-15, Starbucks , 4.5
01/20/2023,  Café Müller  , 12.345
2023/02/05,東京商店,1000
2023-03-10,  Whole Foods Market ,"$1,234.56"
2023-02-28,   Boulangerie Lumière   , 8.999
2023-01-05,Bücher & Co.,  45.10
```

Normalized output preserves order, trims merchants, converts dates to ISO, and formats amounts to `4.50`, `12.35`, `1000.00`, etc.

## API

### `normalize_date(value: str | date | datetime) -> str`
- Trims input, tries supported formats (`YYYY-MM-DD`, `YYYY/MM/DD`, `MM/DD/YYYY`, etc., plus loose `YYYY-M-D`).
- Returns ISO date.
- Raises `ValueError` with prefix `Invalid date:` on failure.

### `normalize_merchant(value: str) -> str`
- Trims Unicode whitespace.
- Raises `ValueError` with prefix `Missing merchant:` if empty/whitespace.

### `normalize_amount(value: str | int | float | Decimal) -> str`
- Strips currency symbols and commas, handles parentheses negatives.
- Uses `Decimal.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)`.
- Returns string with exactly two decimals (e.g., `"1234.50"`).
- Raises `ValueError` with prefix `Invalid amount:` on failure.

### `normalize_row(row: dict, line_num: int | None) -> dict`
- Expects keys `date`, `merchant`, `amount` case-insensitive.
- Returns `{"date": ..., "merchant": ..., "amount": ...}`.
- Raises `ValueError` with context `Row N: ...` if `line_num` given.

### `normalize_records(rows: Iterable[dict]) -> List[dict]`
- Applies `normalize_row` to each, preserving order.
- Raises on first invalid row.

### `normalize_csv(input_path, output_path=None, encoding="utf-8")`
- `input_path`: file path or file-like object.
- `output_path`: optional file path or file-like object. If `None`, returns list; else writes header + rows and returns `None`.
- Handles empty files (no header or header-only) by returning `[]` and writing header only if output given.
- Preserves row order; skips blank lines; raises `ValueError`/`FileNotFoundError` as appropriate.

## Testing

Run only the new tests (from this directory):

```bash
python -m unittest test_normalizer.py -v
# or
python -m unittest discover -s . -p "test_normalizer.py" -v
```

Test coverage includes:
- Unicode merchant names (Japanese, German umlauts, French accents, Arabic, etc.)
- Rounding with `ROUND_HALF_UP` (`1.005→1.01`, `2.675→2.68`, etc.)
- Malformed data (invalid dates, missing merchants, invalid amounts) with correct `ValueError` messages
- Empty input CSV (0 bytes and header-only)
- Fixture integration, file I/O, row order preservation, and edge cases

All tests are `unittest`-based and dependency-free.

## Design Notes

- **Decimal handling**: All amount parsing uses `Decimal` via string conversion to avoid binary float errors; quantization explicitly uses `ROUND_HALF_UP` to match financial rounding expectations rather than Python's default `ROUND_HALF_EVEN`.
- **Date parsing**: Tries `datetime.strptime` formats in priority order (ISO first), then loose regex for `YYYY-M-D` and `M/D/YYYY` variants; ambiguous dates prefer US `M/D/Y` before EU `D/M/Y`; invalid calendar dates are rejected.
- **CSV handling**: Uses `csv.DictReader`/`DictWriter` with UTF-8; header names are case-insensitive and whitespace-tolerant; blank lines are ignored; file-like objects are supported for testability.
- **Error messages**: Each validation raises `ValueError` with a clear prefix (`Missing merchant:`, `Invalid date:`, `Invalid amount:`) plus input context and optional row number.

## License

MIT - Example for acceptance testing.
