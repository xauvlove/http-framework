"""
Unit tests for normalizer.py
Covers: Unicode merchant names, rounding with ROUND_HALF_UP, malformed data, empty CSV, whitespace trimming, ISO normalization, row order.
Dependency-free, uses only unittest and standard library.
"""

import unittest
import csv
import tempfile
import os
from pathlib import Path
from decimal import Decimal

# Import under test
from normalizer import (
    normalize_date,
    normalize_merchant,
    normalize_amount,
    normalize_row,
    normalize_records,
    normalize_csv,
)


class TestNormalizeDate(unittest.TestCase):
    def test_iso_date_passthrough(self):
        self.assertEqual(normalize_date("2023-01-15"), "2023-01-15")
        self.assertEqual(normalize_date("2023-12-31"), "2023-12-31")

    def test_normalize_various_formats_to_iso(self):
        self.assertEqual(normalize_date("01/15/2023"), "2023-01-15")
        self.assertEqual(normalize_date("2023/01/15"), "2023-01-15")
        self.assertEqual(normalize_date("2023-1-5"), "2023-01-05")
        self.assertEqual(normalize_date("2023.01.15"), "2023-01-15")

    def test_invalid_date_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            normalize_date("2023-02-30")
        self.assertIn("Invalid date", str(cm.exception))

        with self.assertRaises(ValueError) as cm2:
            normalize_date("not-a-date")
        self.assertIn("Invalid date", str(cm2.exception))

        with self.assertRaises(ValueError) as cm3:
            normalize_date("   ")
        self.assertIn("Invalid date", str(cm3.exception))

        with self.assertRaises(ValueError) as cm4:
            normalize_date("")
        self.assertIn("Invalid date", str(cm4.exception))

    def test_datetime_object_input(self):
        from datetime import date, datetime
        self.assertEqual(normalize_date(date(2023, 1, 15)), "2023-01-15")
        self.assertEqual(normalize_date(datetime(2023, 1, 15, 10, 30, 0)), "2023-01-15")


class TestNormalizeMerchant(unittest.TestCase):
    def test_trim_whitespace(self):
        self.assertEqual(normalize_merchant("  Starbucks  "), "Starbucks")
        self.assertEqual(normalize_merchant("\t Whole Foods \n"), "Whole Foods")
        self.assertEqual(normalize_merchant("Café Müller"), "Café Müller")

    def test_unicode_merchant_names(self):
        # Requirement: Unicode merchant names must be handled
        self.assertEqual(normalize_merchant("  東京商店  "), "東京商店")
        self.assertEqual(normalize_merchant("Bücher & Co."), "Bücher & Co.")
        self.assertEqual(normalize_merchant("  Café Müller  "), "Café Müller")
        self.assertEqual(normalize_merchant("Boulangerie Lumière"), "Boulangerie Lumière")
        self.assertEqual(normalize_merchant("  São Paulo Café  "), "São Paulo Café")
        self.assertEqual(normalize_merchant("Москва Магазин"), "Москва Магазин")
        self.assertEqual(normalize_merchant("المتجر العربي"), "المتجر العربي")

    def test_missing_merchant_raises(self):
        with self.assertRaises(ValueError) as cm:
            normalize_merchant("   ")
        self.assertIn("Missing merchant", str(cm.exception))

        with self.assertRaises(ValueError) as cm2:
            normalize_merchant("")
        self.assertIn("Missing merchant", str(cm2.exception))

        with self.assertRaises(ValueError) as cm3:
            normalize_merchant(None)
        self.assertIn("Missing merchant", str(cm3.exception))


class TestNormalizeAmount(unittest.TestCase):
    def test_basic_decimal_quantization(self):
        self.assertEqual(normalize_amount("4.5"), "4.50")
        self.assertEqual(normalize_amount("100"), "100.00")
        self.assertEqual(normalize_amount("0"), "0.00")
        self.assertEqual(normalize_amount("-10"), "-10.00")

    def test_rounding_half_up(self):
        # Critical: must use ROUND_HALF_UP, not bankers rounding
        self.assertEqual(normalize_amount("2.345"), "2.35")  # half up up
        self.assertEqual(normalize_amount("2.335"), "2.34")
        self.assertEqual(normalize_amount("1.005"), "1.01")  # classic half-up edge
        self.assertEqual(normalize_amount("1.004"), "1.00")
        self.assertEqual(normalize_amount("8.999"), "9.00")
        self.assertEqual(normalize_amount("12.345"), "12.35")
        self.assertEqual(normalize_amount("1.015"), "1.02")
        self.assertEqual(normalize_amount("1.025"), "1.03")
        # Test that 2.675 rounds to 2.68 with HALF_UP (bankers would give 2.67)
        self.assertEqual(normalize_amount("2.675"), "2.68")
        # Negative rounding
        self.assertEqual(normalize_amount("-1.005"), "-1.01")

    def test_currency_and_commas_stripped(self):
        self.assertEqual(normalize_amount("$1,234.56"), "1234.56")
        self.assertEqual(normalize_amount(" $ 1,234.5 "), "1234.50")
        self.assertEqual(normalize_amount("1,000"), "1000.00")

    def test_invalid_amount_raises(self):
        with self.assertRaises(ValueError) as cm:
            normalize_amount("abc")
        self.assertIn("Invalid amount", str(cm.exception))

        with self.assertRaises(ValueError) as cm2:
            normalize_amount("")
        self.assertIn("Invalid amount", str(cm2.exception))

        with self.assertRaises(ValueError) as cm3:
            normalize_amount("   ")
        self.assertIn("Invalid amount", str(cm3.exception))

        with self.assertRaises(ValueError) as cm4:
            normalize_amount(None)
        self.assertIn("Invalid amount", str(cm4.exception))

        with self.assertRaises(ValueError) as cm5:
            normalize_amount("12.34.56")
        self.assertIn("Invalid amount", str(cm5.exception))


class TestNormalizeRow(unittest.TestCase):
    def test_valid_row_normalization(self):
        row = {"date": "2023-01-15", "merchant": "  Starbucks ", "amount": "4.5"}
        result = normalize_row(row)
        self.assertEqual(result, {"date": "2023-01-15", "merchant": "Starbucks", "amount": "4.50"})

    def test_unicode_row(self):
        row = {"date": "2023/02/05", "merchant": "  東京商店 ", "amount": "1000"}
        result = normalize_row(row)
        self.assertEqual(result["merchant"], "東京商店")
        self.assertEqual(result["date"], "2023-02-05")
        self.assertEqual(result["amount"], "1000.00")

    def test_case_insensitive_headers(self):
        row = {"DATE": "2023-01-15", "MERCHANT": "Starbucks", "AMOUNT": "10"}
        result = normalize_row(row)
        self.assertEqual(result["date"], "2023-01-15")

    def test_preserve_row_order_via_normalize_records(self):
        rows = [
            {"date": "2023-03-01", "merchant": "C", "amount": "3"},
            {"date": "2023-01-01", "merchant": "A", "amount": "1"},
            {"date": "2023-02-01", "merchant": "B", "amount": "2"},
        ]
        result = normalize_records(rows)
        self.assertEqual([r["merchant"] for r in result], ["C", "A", "B"])
        self.assertEqual([r["date"] for r in result], ["2023-03-01", "2023-01-01", "2023-02-01"])

    def test_missing_merchant_raises(self):
        row = {"date": "2023-01-15", "merchant": "   ", "amount": "10.00"}
        with self.assertRaises(ValueError) as cm:
            normalize_row(row)
        self.assertIn("Missing merchant", str(cm.exception))

        row2 = {"date": "2023-01-15", "merchant": "", "amount": "10.00"}
        with self.assertRaises(ValueError) as cm2:
            normalize_row(row2)
        self.assertIn("Missing merchant", str(cm2.exception))

    def test_invalid_date_raises(self):
        row = {"date": "2023-13-01", "merchant": "Starbucks", "amount": "10.00"}
        with self.assertRaises(ValueError) as cm:
            normalize_row(row)
        self.assertIn("Invalid date", str(cm.exception))

        row2 = {"date": "not-a-date", "merchant": "Starbucks", "amount": "10.00"}
        with self.assertRaises(ValueError) as cm2:
            normalize_row(row2)
        self.assertIn("Invalid date", str(cm2.exception))

    def test_invalid_amount_raises(self):
        row = {"date": "2023-01-15", "merchant": "Starbucks", "amount": "abc"}
        with self.assertRaises(ValueError) as cm:
            normalize_row(row)
        self.assertIn("Invalid amount", str(cm.exception))

        row2 = {"date": "2023-01-15", "merchant": "Starbucks", "amount": ""}
        with self.assertRaises(ValueError) as cm2:
            normalize_row(row2)
        self.assertIn("Invalid amount", str(cm2.exception))


class TestNormalizeCsvIntegration(unittest.TestCase):
    def test_fixture_input_csv_normalization(self):
        # Use the provided fixtures/input.csv
        fixture_path = Path(__file__).parent / "fixtures" / "input.csv"
        self.assertTrue(fixture_path.exists(), f"Fixture not found: {fixture_path}")
        result = normalize_csv(fixture_path)
        # Should preserve row order and have 6 rows
        self.assertEqual(len(result), 6)
        # Check first row: trimming and amount formatting
        self.assertEqual(result[0]["merchant"], "Starbucks")
        self.assertEqual(result[0]["date"], "2023-01-15")
        self.assertEqual(result[0]["amount"], "4.50")
        # Second row unicode + rounding
        self.assertEqual(result[1]["merchant"], "Café Müller")
        self.assertEqual(result[1]["amount"], "12.35")
        self.assertEqual(result[1]["date"], "2023-01-20")
        # Third row unicode Japanese
        self.assertEqual(result[2]["merchant"], "東京商店")
        # Fourth row with comma currency and trimming
        self.assertEqual(result[3]["merchant"], "Whole Foods Market")
        self.assertEqual(result[3]["amount"], "1234.56")
        self.assertEqual(result[3]["date"], "2023-03-10")
        # Fifth row rounding 8.999 -> 9.00
        self.assertEqual(result[4]["amount"], "9.00")
        self.assertEqual(result[4]["merchant"], "Boulangerie Lumière")

    def test_empty_input_csv(self):
        # Empty file and header-only file should return empty list without error
        with tempfile.NamedTemporaryFile(mode="w", newline="", suffix=".csv", delete=False, encoding="utf-8") as tf:
            tf_path = tf.name
            # Write only header
            writer = csv.DictWriter(tf, fieldnames=["date", "merchant", "amount"])
            writer.writeheader()
        try:
            result = normalize_csv(tf_path)
            self.assertEqual(result, [])
        finally:
            os.unlink(tf_path)

        # Completely empty file (0 bytes)
        with tempfile.NamedTemporaryFile(mode="w", newline="", suffix=".csv", delete=False, encoding="utf-8") as tf2:
            tf2_path = tf2.name
            # write nothing
            pass
        try:
            result2 = normalize_csv(tf2_path)
            self.assertEqual(result2, [])
        finally:
            os.unlink(tf2_path)

    def test_malformed_data_csv_raises(self):
        # Test malformed CSV data raises ValueError
        test_cases = [
            # invalid date
            ("date,merchant,amount\n2023-13-01,Starbucks,10.00\n", "Invalid date"),
            # missing merchant
            ("date,merchant,amount\n2023-01-15,,10.00\n", "Missing merchant"),
            ("date,merchant,amount\n2023-01-15,   ,10.00\n", "Missing merchant"),
            # invalid amount
            ("date,merchant,amount\n2023-01-15,Starbucks,abc\n", "Invalid amount"),
            ("date,merchant,amount\n2023-01-15,Starbucks,\n", "Invalid amount"),
        ]
        for csv_content, expected_msg in test_cases:
            with self.subTest(csv_content=csv_content):
                with tempfile.NamedTemporaryFile(mode="w", newline="", suffix=".csv", delete=False, encoding="utf-8") as tf:
                    tf_path = tf.name
                    tf.write(csv_content)
                try:
                    with self.assertRaises(ValueError) as cm:
                        normalize_csv(tf_path)
                    self.assertIn(expected_msg, str(cm.exception))
                finally:
                    os.unlink(tf_path)

    def test_write_output_csv(self):
        input_content = "date,merchant,amount\n2023-01-15,  Starbucks ,4.5\n"
        with tempfile.NamedTemporaryFile(mode="w", newline="", suffix=".csv", delete=False, encoding="utf-8") as fin:
            fin_path = fin.name
            fin.write(input_content)
        with tempfile.NamedTemporaryFile(mode="w", newline="", suffix=".csv", delete=False, encoding="utf-8") as fout:
            fout_path = fout.name

        try:
            normalize_csv(fin_path, fout_path)
            # Verify output file
            with open(fout_path, newline="", encoding="utf-8") as rf:
                reader = csv.DictReader(rf)
                rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["merchant"], "Starbucks")
            self.assertEqual(rows[0]["amount"], "4.50")
            self.assertEqual(rows[0]["date"], "2023-01-15")
        finally:
            os.unlink(fin_path)
            os.unlink(fout_path)

    def test_rounding_in_csv_context(self):
        content = "date,merchant,amount\n2023-01-15,A,1.005\n2023-01-16,B,2.675\n2023-01-17,C,1.004\n"
        with tempfile.NamedTemporaryFile(mode="w", newline="", suffix=".csv", delete=False, encoding="utf-8") as tf:
            tf_path = tf.name
            tf.write(content)
        try:
            result = normalize_csv(tf_path)
            self.assertEqual(result[0]["amount"], "1.01")
            self.assertEqual(result[1]["amount"], "2.68")
            self.assertEqual(result[2]["amount"], "1.00")
        finally:
            os.unlink(tf_path)

    def test_unicode_merchants_in_csv_file(self):
        content = "date,merchant,amount\n2023-01-15,東京商店,100\n2023-01-16,Bücher & Co.,200\n2023-01-17,Café Müller,300\n"
        with tempfile.NamedTemporaryFile(mode="w", newline="", suffix=".csv", delete=False, encoding="utf-8") as tf:
            tf_path = tf.name
            tf.write(content)
        try:
            result = normalize_csv(tf_path)
            self.assertEqual(result[0]["merchant"], "東京商店")
            self.assertEqual(result[1]["merchant"], "Bücher & Co.")
            self.assertEqual(result[2]["merchant"], "Café Müller")
        finally:
            os.unlink(tf_path)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            normalize_csv("/nonexistent/path/to/file.csv")

    def test_preserve_row_order_in_file(self):
        content = "date,merchant,amount\n2023-03-01,C,3\n2023-01-01,A,1\n2023-02-01,B,2\n"
        with tempfile.NamedTemporaryFile(mode="w", newline="", suffix=".csv", delete=False, encoding="utf-8") as tf:
            tf_path = tf.name
            tf.write(content)
        try:
            result = normalize_csv(tf_path)
            self.assertEqual([r["merchant"] for r in result], ["C", "A", "B"])
        finally:
            os.unlink(tf_path)


# Additional edge case to ensure at least 6 meaningful cases (we already have many, but explicit)
class TestEdgeCases(unittest.TestCase):
    def test_empty_string_amount_currency(self):
        # Already tested invalid, but ensure clear message
        with self.assertRaises(ValueError) as cm:
            normalize_amount("$")
        self.assertIn("Invalid amount", str(cm.exception))

    def test_whitespace_only_merchant_in_row(self):
        row = {"date": "2023-01-15", "merchant": " \t\n ", "amount": "10"}
        with self.assertRaises(ValueError) as cm:
            normalize_row(row)
        self.assertIn("Missing merchant", str(cm.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
