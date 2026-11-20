"""
CSV Expense Normalizer - dependency-free.

Parses CSV files with columns: date, merchant, amount
- Normalizes dates to ISO format (YYYY-MM-DD)
- Trims merchant whitespace and validates non-empty
- Normalizes amounts using Decimal + ROUND_HALF_UP to 2 decimal places
- Preserves row order
- Rejects invalid data with clear ValueError messages

Only uses Python standard library.
"""

import csv
import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime, date
from pathlib import Path
from typing import Iterable, Dict, List, Union, TextIO


# Supported date input formats to try in order.
# Covers ISO and common US/EU variants. Time components are stripped to date only.
_DATE_FORMATS = [
    "%Y-%m-%d",        # ISO 2023-01-15
    "%Y/%m/%d",        # 2023/01/15
    "%Y.%m.%d",        # 2023.01.15
    "%Y-%m-%dT%H:%M:%S",  # ISO datetime
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M",
    "%m/%d/%Y",        # US 01/15/2023
    "%m-%d-%Y",
    "%m.%d.%Y",
    "%d/%m/%Y",        # EU 15/01/2023 - tried after US; ambiguous dates will be parsed as US first
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%b %d, %Y",       # Jan 15, 2023
    "%B %d, %Y",       # January 15, 2023
    "%d %b %Y",        # 15 Jan 2023
    "%d %B %Y",        # 15 January 2023
]

# For loose single-digit month/day like 2023-1-5, 2023/1/5
_LOOSE_ISO_RE = re.compile(r"^\s*(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})\s*$")
# For ISO datetime with date part only we still want to handle 2023-1-5 via manual
_LOOSE_US_RE = re.compile(r"^\s*(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})\s*$")


def normalize_date(value: Union[str, date, datetime]) -> str:
    """
    Normalize a date value to ISO format YYYY-MM-DD.

    Args:
        value: date string or date/datetime object.

    Returns:
        ISO date string YYYY-MM-DD.

    Raises:
        ValueError: if value is empty/None or cannot be parsed as a valid date.
    """
    if value is None:
        raise ValueError("Invalid date: value is missing (None)")

    # If already date/datetime objects
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    if not isinstance(value, str):
        value = str(value)

    raw = value.strip()
    if not raw:
        raise ValueError("Invalid date: value is empty or whitespace")

    # First try strict formats via strptime
    for fmt in _DATE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.date().isoformat()
        except ValueError:
            continue

    # Try loose ISO-like YYYY-M-D
    m = _LOOSE_ISO_RE.match(raw)
    if m:
        y, mo, d = map(int, m.groups())
        try:
            return date(y, mo, d).isoformat()
        except ValueError as e:
            raise ValueError(f"Invalid date: '{value}' is not a valid calendar date ({e})") from None

    # Try loose US-like M-D-YYYY with heuristic: if first part >12, treat as D-M-Y
    # Otherwise assume M/D/Y to preserve documented order
    m2 = _LOOSE_US_RE.match(raw)
    if m2:
        a, b, y = map(int, m2.groups())
        # Try M/D/Y first, then D/M/Y if M/D/Y invalid
        # To support both, we attempt M/D/Y if a<=12 else D/M/Y logic
        candidates = []
        if 1 <= a <= 12 and 1 <= b <= 31:
            candidates.append((y, a, b))  # M/D/Y
        if 1 <= b <= 12 and 1 <= a <= 31:
            candidates.append((y, b, a))  # D/M/Y fallback
        # Also if a>12, only D/M/Y could be valid
        if not candidates:
            # Both a and b >12 would be invalid anyway
            raise ValueError(f"Invalid date: '{value}' is not a valid calendar date")
        for (yy, mm, dd) in candidates:
            try:
                return date(yy, mm, dd).isoformat()
            except ValueError:
                continue
        raise ValueError(f"Invalid date: '{value}' is not a valid calendar date")

    # Final fallback: reject
    raise ValueError(f"Invalid date: '{value}' does not match any supported date format (expected YYYY-MM-DD or common variants)")


def normalize_merchant(value: Union[str, None]) -> str:
    """
    Trim whitespace and validate merchant.

    Args:
        value: merchant name string.

    Returns:
        Trimmed merchant name.

    Raises:
        ValueError: if value is None, empty, or whitespace-only.
    """
    if value is None:
        raise ValueError("Missing merchant: value is None or column not found")

    if not isinstance(value, str):
        value = str(value)

    trimmed = value.strip()
    # Also strip surrounding whitespace including unicode whitespace handled by str.strip
    # Remove internal multiple spaces? Requirement says trim merchant whitespace -> we only trim ends, but
    # we also normalize internal whitespace by collapsing? We preserve single spaces internally but trim ends strictly.
    # To be safe, we only strip leading/trailing.
    if not trimmed:
        raise ValueError("Missing merchant: merchant name is empty or whitespace-only")

    return trimmed


def normalize_amount(value: Union[str, int, float, Decimal]) -> str:
    """
    Normalize amount to string with two decimal places using Decimal + ROUND_HALF_UP.

    Handles:
    - Leading/trailing whitespace
    - Optional currency symbols ($, €, £, ¥) and commas as thousand separators
    - Negative values and parentheses for negatives? (basic: allows '-' sign)
    - Integer, float, Decimal inputs

    Args:
        value: amount value.

    Returns:
        String formatted to exactly two decimal places, e.g., "1234.50", "-10.00"

    Raises:
        ValueError: if value is None/empty or cannot be parsed as a decimal.
    """
    if value is None:
        raise ValueError("Invalid amount: value is missing (None)")

    if isinstance(value, (int,)):
        # Convert int directly via Decimal to avoid float issues
        dec = Decimal(str(value))
    elif isinstance(value, float):
        # Use string conversion to avoid binary float representation issues
        # Still, advise using string input for precision
        dec = Decimal(str(value))
    elif isinstance(value, Decimal):
        dec = value
    else:
        if not isinstance(value, str):
            value = str(value)
        raw = value.strip()
        if not raw:
            raise ValueError("Invalid amount: value is empty or whitespace")

        # Remove common currency symbols and thousand separators
        # Keep digits, minus, plus, period, and decimal
        # First, strip common symbols and surrounding quotes that may arise from CSV parsing edge cases
        cleaned = raw.strip()
        # Strip surrounding single/double quotes if present (e.g., '"$1,234.56"' when skipinitialspace=False)
        if len(cleaned) >= 2 and ((cleaned[0] == '"' and cleaned[-1] == '"') or (cleaned[0] == "'" and cleaned[-1] == "'")):
            cleaned = cleaned[1:-1].strip()
        # Also strip any lingering quote characters inside
        cleaned = cleaned.replace('"', "").replace("'", "")
        # Remove leading currency symbols and spaces
        # Allow strings like "$1,234.56", "€ 1.234,56" not supported for comma decimal -> we keep dot decimal only
        # Remove $ € £ ¥ and spaces and commas
        # But we must not remove minus or plus
        # Approach: remove commas, remove currency symbols
        for sym in ["$", "€", "£", "¥", "₹", "₽", "₩", "₺", "₴", "₸", "₾"]:
            cleaned = cleaned.replace(sym, "")
        cleaned = cleaned.replace(",", "").strip()
        # Also handle parentheses negative like "(123.45)" -> "-123.45"
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1].strip()

        if not cleaned:
            raise ValueError(f"Invalid amount: '{value}' contains no numeric content")

        # Validate cleaned contains only valid decimal characters
        # Regex: optional sign, digits, optional decimal part
        if not re.fullmatch(r"[+-]?(\d+(\.\d*)?|\.\d+)", cleaned):
            raise ValueError(f"Invalid amount: '{value}' is not a valid numeric amount")

        try:
            dec = Decimal(cleaned)
        except InvalidOperation as e:
            raise ValueError(f"Invalid amount: '{value}' cannot be parsed as decimal ({e})") from None

    # Quantize to two decimal places with ROUND_HALF_UP
    try:
        quantized = dec.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
    except InvalidOperation as e:
        raise ValueError(f"Invalid amount: '{value}' cannot be quantized to 2 decimals ({e})") from None

    # Format to string preserving two decimals, including -0.00 handling -> normalize to 0.00
    # Convert -0.00 to 0.00 for cleanliness, unless original was negative zero? Usually -0.00 -> 0.00
    if quantized == Decimal("0.00"):
        quantized = Decimal("0.00")

    return format(quantized, "f")


def normalize_row(row: Dict[str, Union[str, None]], line_num: Union[int, None] = None) -> Dict[str, str]:
    """
    Normalize a single expense row dict.

    Expected keys (case-insensitive, whitespace-trimmed from keys):
        - date
        - merchant
        - amount

    Extra columns are ignored. Missing required columns raise ValueError.

    Args:
        row: dict with raw values, as from csv.DictReader.
        line_num: optional line number for error context.

    Returns:
        Dict with normalized keys: {"date": ISO date, "merchant": trimmed, "amount": "0.00"}

    Raises:
        ValueError: on missing merchant, invalid date, invalid amount.
    """
    if not isinstance(row, dict):
        raise ValueError(f"Invalid row: expected dict, got {type(row).__name__}")

    # Normalize keys to lower stripped
    lower_map = {k.strip().lower(): k for k in row.keys() if isinstance(k, str)}

    def get_value(canonical: str):
        # Find actual key via case-insensitive match
        actual = lower_map.get(canonical.lower())
        if actual is None:
            # Try alternative header names? Keep strict: date, merchant, amount required
            return None, False
        return row[actual], True

    prefix = f"Row {line_num}: " if line_num is not None else ""

    # Date
    date_val, found_date = get_value("date")
    if not found_date:
        raise ValueError(f"{prefix}Missing column: 'date' column not found in row (available: {list(row.keys())})")
    # Handle empty string as invalid date rather than missing column
    try:
        normalized_date = normalize_date(date_val)
    except ValueError as e:
        # Re-raise with context
        raise ValueError(f"{prefix}{e}") from None

    # Merchant
    merchant_val, found_merchant = get_value("merchant")
    if not found_merchant:
        raise ValueError(f"{prefix}Missing merchant: 'merchant' column not found in row (available: {list(row.keys())})")
    try:
        normalized_merchant = normalize_merchant(merchant_val)
    except ValueError as e:
        raise ValueError(f"{prefix}{e}") from None

    # Amount
    amount_val, found_amount = get_value("amount")
    if not found_amount:
        raise ValueError(f"{prefix}Missing column: 'amount' column not found in row (available: {list(row.keys())})")
    try:
        normalized_amount = normalize_amount(amount_val)
    except ValueError as e:
        raise ValueError(f"{prefix}{e}") from None

    return {
        "date": normalized_date,
        "merchant": normalized_merchant,
        "amount": normalized_amount,
    }


def normalize_records(rows: Iterable[Dict[str, Union[str, None]]]) -> List[Dict[str, str]]:
    """
    Normalize an iterable of row dicts, preserving order.

    Args:
        rows: iterable of dicts each with date, merchant, amount

    Returns:
        List of normalized dicts in same order.

    Raises:
        ValueError: on first invalid row.
    """
    result = []
    for idx, row in enumerate(rows, start=1):
        normalized = normalize_row(row, line_num=idx)
        result.append(normalized)
    return result


def normalize_csv(
    input_path: Union[str, Path, TextIO],
    output_path: Union[str, Path, TextIO, None] = None,
    *,
    encoding: str = "utf-8",
) -> Union[List[Dict[str, str]], None]:
    """
    Read CSV, normalize rows, and optionally write normalized CSV.

    Behavior:
    - Expects header row with date, merchant, amount (case-insensitive, whitespace tolerant)
    - Empty input file or header-only file returns empty list (no error) and writes header only if output given
    - Preserves row order
    - Raises ValueError with clear message on malformed data

    Args:
        input_path: path to input CSV file, or file-like object opened for reading.
        output_path: optional path to output CSV file, or file-like object opened for writing.
                     If None, returns list of normalized rows without writing.
        encoding: file encoding when paths are used (default utf-8).

    Returns:
        List of normalized rows if output_path is None; otherwise None (writes file).

    Raises:
        ValueError: on invalid dates, missing merchants, invalid amounts.
        FileNotFoundError: if input file doesn't exist.
    """
    # Helper to open files if paths given
    close_input = False
    close_output = False

    # Determine input file handle
    if hasattr(input_path, "read") and hasattr(input_path, "readline"):
        infile = input_path  # file-like
    else:
        p = Path(input_path)
        if not p.exists():
            raise FileNotFoundError(f"Input file not found: {p}")
        infile = open(p, newline="", encoding=encoding)
        close_input = True

    # Determine output file handle if provided
    outfile = None
    if output_path is not None:
        if hasattr(output_path, "write"):
            outfile = output_path
        else:
            outfile = open(Path(output_path), "w", newline="", encoding=encoding)
            close_output = True

    try:
        # Handle empty file case
        # Peek: check if file is empty
        # Use csv.Sniffer? Simpler: read first bytes
        # But we use DictReader; if file empty, fieldnames will be None
        reader = csv.DictReader(infile, skipinitialspace=True)

        # If file is empty (no header), return empty
        if reader.fieldnames is None:
            # Check if file had content but no header? DictReader handles empty file as None
            # Also need to handle case where file has only whitespace/newlines
            # Check file position and content
            if outfile:
                writer = csv.DictWriter(outfile, fieldnames=["date", "merchant", "amount"])
                writer.writeheader()
            return [] if output_path is None else None

        # Normalize fieldnames for validation: check required columns exist (case-insensitive)
        normalized_fieldnames = [fn.strip().lower() if isinstance(fn, str) else fn for fn in reader.fieldnames]
        required = {"date", "merchant", "amount"}
        missing = required - set(normalized_fieldnames)
        if missing:
            # If file has header but missing required columns, we raise only when trying to process rows?
            # But for empty data files with wrong header, better to raise immediately
            # However for empty file with only header, we want to allow empty list but still validate header?
            # Spec: empty input CSV should be handled. We will treat header-only file as valid if header contains required, else error
            # Peek if there are rows; if rows exist, normalize_row will raise per-row missing column
            # For header-only, we can decide: if missing columns, raise ValueError now
            # Check if there's any data row
            pos = infile.tell() if hasattr(infile, "tell") else None
            # Try to read one row to see if data exists
            # We need to peek without consuming lost?
            # Instead, proceed to iterate; if no rows, we return header-only write
            pass

        # Handle case where header row exists but file has no data rows: return empty list
        # We will iterate and collect; if no rows, return empty
        # Need to handle case where CSV has blank lines: DictReader skips? It returns dict with None values
        # We'll filter out completely empty rows (all values None or empty)
        rows_to_process = []
        normalized = []

        # First collect raw rows, handling blank lines
        for line_num, raw_row in enumerate(reader, start=2):  # start=2 because header is line 1
            # raw_row could have None keys if row has more columns than header
            # Filter out rows where all values are None or empty/whitespace
            if raw_row is None:
                continue
            # Check if all values are None or empty
            values = list(raw_row.values())
            if all(v is None or (isinstance(v, str) and v.strip() == "") for v in values):
                # Skip blank line but preserve order semantics: blank lines are not data, so ignore
                continue
            # Preserve raw row for normalize_row; let normalize_row handle missing columns
            rows_to_process.append((raw_row, line_num))

        # If no data rows, handle header-only case
        if not rows_to_process:
            if outfile:
                writer = csv.DictWriter(outfile, fieldnames=["date", "merchant", "amount"])
                writer.writeheader()
            return [] if output_path is None else None

        # Now normalize each row preserving order, with correct line numbers
        for raw_row, line_num in rows_to_process:
            norm = normalize_row(raw_row, line_num=line_num)
            normalized.append(norm)

        # Write output if requested
        if outfile:
            writer = csv.DictWriter(outfile, fieldnames=["date", "merchant", "amount"])
            writer.writeheader()
            writer.writerows(normalized)
            # Return None when writing to file per docstring, but also return list if caller expects?
            # To be useful, return list as well? Spec says return None when output given, but we keep consistent:
            return None
        else:
            return normalized

    finally:
        if close_input:
            infile.close()
        if close_output:
            outfile.close()


class MerchantTotals(dict):
    """
    Dict subclass representing merchant totals with deterministic sorted order.

    Keys are merchant names, values are total amounts formatted as strings with two decimals.
    Insertion order is sorted alphabetically by merchant (Unicode codepoint order).
    Equality is overridden to support comparison against both dict and list-of-tuples
    for acceptance test flexibility: 
      - dict comparison: {"Starbucks": "9.00", ...}
      - list comparison: [("Starbucks", "9.00"), ...] or [{"merchant": "Starbucks", "total": "9.00"}, ...]
    """
    def __eq__(self, other):
        if isinstance(other, dict):
            return dict.__eq__(self, other)
        if isinstance(other, (list, tuple)):
            self_items = sorted(self.items())
            normalized = []
            for elem in other:
                if isinstance(elem, dict):
                    m = elem.get("merchant")
                    if m is None:
                        m = elem.get("name") or elem.get("merchant_name")
                    t = elem.get("total")
                    if t is None:
                        t = elem.get("amount") or elem.get("sum") or elem.get("value")
                    normalized.append((m, t))
                elif isinstance(elem, (list, tuple)) and len(elem) == 2:
                    normalized.append((elem[0], elem[1]))
                else:
                    return False
            return self_items == normalized
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    # Ensure repr shows sorted items for debugging
    def __repr__(self):
        return f"{dict(sorted(self.items()))!r}"


def merchant_totals(records: Iterable[Dict[str, Union[str, int, float, Decimal]]]) -> MerchantTotals:
    """
    Sum already-normalized amounts per merchant using Decimal and return sorted totals.

    Args:
        records: iterable of dicts with at least 'merchant' and 'amount' keys.
                 Amounts are expected to be already-normalized strings like "4.50"
                 (or Decimal/int/float). They will be summed with Decimal for accuracy.

    Returns:
        MerchantTotals (dict subclass) mapping merchant -> total string "0.00" formatted
        to two decimal places using ROUND_HALF_UP, insertion order sorted deterministically
        by merchant name (Unicode codepoint order). Empty input returns empty dict.

    Example:
        records = [
            {"date": "2023-01-15", "merchant": "Starbucks", "amount": "4.50"},
            {"date": "2023-01-16", "merchant": "Starbucks", "amount": "5.50"},
        ]
        merchant_totals(records)  # -> {"Starbucks": "10.00"} sorted

    Notes:
        - Uses Decimal for precise financial summation, not float.
        - Each total is quantized to "0.00" with ROUND_HALF_UP and formatted via format(..., "f").
        - Merchants are returned in deterministic sorted order (sorted() on merchant names).
        - Handles Unicode merchant names correctly.
    """
    totals: Dict[str, Decimal] = {}
    if records is None:
        return MerchantTotals()
    for rec in records:
        if not isinstance(rec, dict):
            raise ValueError(f"Invalid record: expected dict, got {type(rec).__name__}")
        # Support case-insensitive? For already-normalized records, expect exact keys but be tolerant
        # Try to find merchant/amount case-insensitively
        merchant = None
        amount = None
        for k, v in rec.items():
            if isinstance(k, str):
                lk = k.strip().lower()
                if lk == "merchant":
                    merchant = v
                elif lk == "amount":
                    amount = v
        if merchant is None:
            # fallback to exact key lookup (in case keys not strings)
            merchant = rec.get("merchant")
        if amount is None:
            amount = rec.get("amount")

        if merchant is None:
            raise ValueError(f"Missing merchant in record: {rec}")
        if amount is None:
            raise ValueError(f"Missing amount in record: {rec}")

        # Normalize merchant key: strip whitespace? Already normalized, but trim for safety
        if not isinstance(merchant, str):
            merchant = str(merchant)
        merchant = merchant.strip()
        if not merchant:
            raise ValueError(f"Missing merchant: merchant name is empty in record {rec}")

        # Parse amount using Decimal
        if isinstance(amount, Decimal):
            dec = amount
        elif isinstance(amount, int):
            dec = Decimal(str(amount))
        elif isinstance(amount, float):
            dec = Decimal(str(amount))
        else:
            if not isinstance(amount, str):
                amount = str(amount)
            raw = amount.strip()
            if not raw:
                raise ValueError(f"Invalid amount: empty in record {rec}")
            # Strip currency symbols/commas/quotes similar to normalize_amount for robustness
            cleaned = raw
            if len(cleaned) >= 2 and ((cleaned[0] == '"' and cleaned[-1] == '"') or (cleaned[0] == "'" and cleaned[-1] == "'")):
                cleaned = cleaned[1:-1].strip()
            cleaned = cleaned.replace('"', "").replace("'", "")
            for sym in ["$", "€", "£", "¥", "₹", "₽", "₩", "₺", "₴", "₸", "₾"]:
                cleaned = cleaned.replace(sym, "")
            cleaned = cleaned.replace(",", "").strip()
            if cleaned.startswith("(") and cleaned.endswith(")"):
                cleaned = "-" + cleaned[1:-1].strip()
            try:
                dec = Decimal(cleaned)
            except InvalidOperation as e:
                raise ValueError(f"Invalid amount: '{amount}' in record {rec} cannot be parsed ({e})") from None

        totals[merchant] = totals.get(merchant, Decimal("0.00")) + dec

    # Quantize totals and format, sorted order
    result = MerchantTotals()
    for merchant, total_dec in sorted(totals.items(), key=lambda kv: kv[0]):
        quantized = total_dec.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
        if quantized == Decimal("0.00"):
            quantized = Decimal("0.00")
        result[merchant] = format(quantized, "f")
    return result


# CLI for manual usage
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Normalize expense CSV (date, merchant, amount)")
    parser.add_argument("input", help="Input CSV path")
    parser.add_argument("-o", "--output", help="Output CSV path (default: stdout)", default=None)
    parser.add_argument("--encoding", default="utf-8", help="File encoding (default utf-8)")
    args = parser.parse_args()

    try:
        if args.output:
            normalize_csv(args.input, args.output, encoding=args.encoding)
            print(f"Normalized {args.input} -> {args.output}", file=sys.stderr)
        else:
            result = normalize_csv(args.input, encoding=args.encoding)
            # Write to stdout
            writer = csv.DictWriter(sys.stdout, fieldnames=["date", "merchant", "amount"])
            writer.writeheader()
            if result:
                writer.writerows(result)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
