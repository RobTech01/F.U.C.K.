# Manual Test Procedure: Session 5 - Better Error Reporting

## Test Objective
Validate that validation errors are reported with detailed information including line numbers, error types, and actionable suggestions.

## Prerequisites
- F.U.C.K. installed and working
- Ability to create test CSV files with intentional errors

## Setup

Create a test CSV file with intentional errors:

```csv
Date;Address;Amount
2024-01-15;Walmart Store #123;87.45
2024-01-16;Electric Company;invalid_amount
2024-01-17;Gas Station;45.00
2024-01-18;Restaurant;
2024-01-19;Coffee Shop;5.50;Extra Column
```

Save as `test_errors.csv`

## Test Cases

### Test 1: Process CSV with Validation Errors (Normal Mode)

**Steps:**
1. Process CSV with errors:
   ```bash
   python3 main.py process test_errors.csv
   ```

**Expected Result:**
- ✅ Processing continues despite errors
- ✅ Each error shows line number and reason
- ✅ Example: "Line 3: Invalid amount value: 'invalid_amount'"
- ✅ All valid transactions are processed
- ✅ Validation summary shown at end
- ✅ Summary groups errors by type
- ✅ Suggestions for fixing shown

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 2: Validation Summary Format

**Steps:**
1. After processing CSV with errors, check summary format

**Expected Result:**
- ✅ Header: "VALIDATION ERRORS SUMMARY"
- ✅ Shows total error count
- ✅ Errors grouped by type (INVALID_AMOUNT, MISSING_FIELD, etc.)
- ✅ Each error shows line number
- ✅ "HOW TO FIX" section with actionable suggestions
- ✅ Common fixes listed
- ✅ Professional 80-char formatting

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 3: Strict Mode - Fail on First Error

**Steps:**
1. Process same CSV with --strict flag:
   ```bash
   python3 main.py process test_errors.csv --strict
   ```

**Expected Result:**
- ✅ Processing stops at first validation error
- ✅ Error message shows line number and reason
- ✅ ValidationError exception raised
- ✅ Exit code 1
- ✅ No transactions saved
- ✅ Clear error message about which line failed

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 4: Different Error Types

Create CSV with various error types:
```csv
Date;Address;Amount
;Empty Date;100
2024-01-01;;50
2024-01-02;Valid Address;999999999999
2024-01-03;Valid;not_a_number
```

**Steps:**
1. Process CSV:
   ```bash
   python3 main.py process various_errors.csv
   ```

**Expected Result:**
- ✅ INVALID_DATE error for empty date
- ✅ INVALID_ADDRESS error for empty address
- ✅ INVALID_AMOUNT error for too-large amount
- ✅ INVALID_AMOUNT error for non-numeric amount
- ✅ Each error shows correct line number
- ✅ Errors grouped by type in summary

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 5: Line Number Accuracy

**Steps:**
1. Create CSV with error on known line (e.g., line 10)
2. Process CSV
3. Verify error reports correct line number

**Expected Result:**
- ✅ Line number in error matches actual CSV line
- ✅ Line numbers are 1-indexed (header is line 1)
- ✅ Easy to navigate to error in text editor

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 6: Multiple Errors Same Type

Create CSV with multiple amount errors:
```csv
Date;Address;Amount
2024-01-01;Store A;abc
2024-01-02;Store B;def
2024-01-03;Store C;100
2024-01-04;Store D;xyz
```

**Steps:**
1. Process CSV

**Expected Result:**
- ✅ All three amount errors detected
- ✅ Grouped under INVALID_AMOUNT section
- ✅ Line numbers: 2, 3, 5 shown
- ✅ Count shows 3 errors of this type

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 7: Mix of Valid and Invalid Transactions

**Steps:**
1. Process CSV with 10 transactions, 3 invalid
2. Check final statistics

**Expected Result:**
- ✅ Total: 10 transactions
- ✅ Processed: 7 transactions
- ✅ Skipped: 3 transactions
- ✅ All valid transactions saved
- ✅ Invalid transactions listed in error summary
- ✅ Category totals only include valid transactions

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 8: Error Suggestions Accuracy

**Steps:**
1. Process CSV with various errors
2. Review "HOW TO FIX" section

**Expected Result:**
- ✅ Suggestions match error types
- ✅ Example: "Empty amounts: Fill in the amount value"
- ✅ Example: "Invalid amounts: Ensure amounts are numeric"
- ✅ Example: "Missing fields: Add required date, address, or amount"
- ✅ Helpful and actionable

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 9: Strict Mode with Review Mode

**Steps:**
1. Try processing with both --strict and without --no-review:
   ```bash
   python3 main.py process test_errors.csv --strict
   ```

**Expected Result:**
- ✅ Strict mode takes precedence
- ✅ Fails on first error before review
- ✅ No review screen shown
- ✅ Clear error message

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 10: No Errors - No Summary

**Steps:**
1. Process valid CSV with no errors:
   ```bash
   python3 main.py process dummy-data/january.csv
   ```

**Expected Result:**
- ✅ Processing completes successfully
- ✅ NO validation summary shown
- ✅ Only normal processing summary shown
- ✅ Clean output

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

## Usage Examples

```bash
# Process CSV and see detailed error report
python3 main.py process bank_statement.csv

# Fail immediately on first error
python3 main.py process bank_statement.csv --strict

# Skip review but still show validation errors
python3 main.py process bank_statement.csv --no-review
```

## Example Error Output

```
Processing 5 transactions...
Warning: Line 3: Invalid amount value: 'invalid'
Warning: Line 5: Address cannot be empty
Processing: 5/5 (100.0%)

==================================================
PROCESSING SUMMARY
==================================================
Total transactions in CSV: 5
New transactions added:    3
Duplicates skipped:        0
==================================================

================================================================================
VALIDATION ERRORS SUMMARY
================================================================================
Total errors: 2

INVALID_AMOUNT:
--------------------------------------------------------------------------------
  Line 3: Invalid amount value: 'invalid'

INVALID_ADDRESS:
--------------------------------------------------------------------------------
  Line 5: Address cannot be empty

================================================================================
HOW TO FIX:
================================================================================
1. Open your CSV file in a text editor or spreadsheet
2. Navigate to the line numbers listed above
3. Fix the issues according to the error messages
4. Save the file and try processing again

Common fixes:
  - Empty amounts: Fill in the amount value
  - Invalid amounts: Ensure amounts are numeric (no $, commas, etc.)
  - Missing fields: Add required date, address, or amount
  - Invalid dates: Use format YYYY-MM-DD or MM/DD/YYYY
================================================================================
```

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Test 1: Process with Errors | ⬜ | |
| Test 2: Summary Format | ⬜ | |
| Test 3: Strict Mode | ⬜ | |
| Test 4: Different Error Types | ⬜ | |
| Test 5: Line Number Accuracy | ⬜ | |
| Test 6: Multiple Same Type | ⬜ | |
| Test 7: Mix Valid/Invalid | ⬜ | |
| Test 8: Error Suggestions | ⬜ | |
| Test 9: Strict + Review | ⬜ | |
| Test 10: No Errors | ⬜ | |

**Overall Status:** Not Tested

---

**Test Completed By:** _____________
**Date:** _____________
**Environment:** _____________
