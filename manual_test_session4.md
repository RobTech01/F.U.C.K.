# Manual Test Procedure: Session 4 - Data Export Capability

## Test Objective
Validate that the export command successfully exports category data to CSV, JSON, and TXT formats with proper filtering support.

## Prerequisites
- Hash table with categorized transactions
- Multiple categories with varying amounts

## Setup
```bash
python3 main.py process dummy-data/january.csv
python3 main.py process dummy-data/february.csv
```

## Test Cases

### Test 1: Basic CSV Export

**Steps:**
1. Export to CSV:
   ```bash
   python3 main.py export --format csv --output test_export.csv
   ```
2. Open file in text editor or Excel

**Expected Result:**
- ✅ File created: test_export.csv
- ✅ Success message shows number of categories exported
- ✅ CSV has header row: category,amount
- ✅ All categories listed alphabetically
- ✅ Amounts formatted to 2 decimal places
- ✅ Opens correctly in Excel/Sheets

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 2: JSON Export

**Steps:**
1. Export to JSON:
   ```bash
   python3 main.py export --format json --output test_export.json
   ```
2. Open file and verify JSON structure

**Expected Result:**
- ✅ File created: test_export.json
- ✅ Valid JSON format (can parse without errors)
- ✅ Contains: export_date, total_categories, grand_total, categories
- ✅ Categories array has objects with category and amount fields
- ✅ Pretty-printed (indented) for readability
- ✅ Grand total matches sum of all categories

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 3: TXT Export

**Steps:**
1. Export to TXT:
   ```bash
   python3 main.py export --format txt --output test_export.txt
   ```
2. Open file in text editor

**Expected Result:**
- ✅ File created: test_export.txt
- ✅ Header: "F.U.C.K. SPENDING REPORT"
- ✅ Shows export date
- ✅ Shows total categories count
- ✅ Shows grand total
- ✅ Table with category names and amounts
- ✅ Professional formatting (80-char width)
- ✅ Human-readable format

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 4: Default Filename Generation

**Steps:**
1. Export without --output flag:
   ```bash
   python3 main.py export --format csv
   ```

**Expected Result:**
- ✅ File created with auto-generated name
- ✅ Filename format: fuck_export_YYYYMMDD_HHMMSS.csv
- ✅ Timestamp in filename is current time
- ✅ Success message shows actual filename

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 5: Export with Category Filter

**Steps:**
1. Export filtered data:
   ```bash
   python3 main.py export --format csv --category "Groceries" --output filtered.csv
   ```

**Expected Result:**
- ✅ Shows "Applying filters..." message
- ✅ Shows filter details
- ✅ Shows matching categories count
- ✅ Exported file contains only matching categories
- ✅ Categories match filter substring (case-insensitive)

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 6: Export with Amount Range Filter

**Steps:**
1. Export with amount filter:
   ```bash
   python3 main.py export --format json --min-amount 100 --max-amount 500 --output range.json
   ```

**Expected Result:**
- ✅ Shows applied filters
- ✅ Only categories within range are exported
- ✅ Min and max amounts are inclusive
- ✅ Grand total reflects filtered data only

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 7: Export with Combined Filters

**Steps:**
1. Combine multiple filters:
   ```bash
   python3 main.py export --format csv --category "Food" --min-amount 50 --output combined.csv
   ```

**Expected Result:**
- ✅ All filters applied (AND logic)
- ✅ Only categories matching all criteria exported
- ✅ Filter details shown in output
- ✅ Correct count of matching categories

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 8: Export with No Matching Filters

**Steps:**
1. Use filters that match nothing:
   ```bash
   python3 main.py export --format csv --category "NonexistentCategory"
   ```

**Expected Result:**
- ✅ Error: "No categories match the specified filters"
- ✅ No file created
- ✅ Exit code 1
- ✅ Helpful error message

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 9: Export with No Data

**Steps:**
1. Remove hash table:
   ```bash
   rm -f storage/hash_table.enc
   ```
2. Try to export:
   ```bash
   python3 main.py export --format csv
   ```

**Expected Result:**
- ✅ Error: "No hash table found"
- ✅ Suggestion to process CSV first
- ✅ Exit code 1
- ✅ No file created

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 10: Invalid Format

**Steps:**
1. Try invalid format (should be caught by argparse):
   ```bash
   python3 main.py export --format pdf
   ```

**Expected Result:**
- ✅ Error: invalid choice
- ✅ Shows valid choices: csv, json, txt
- ✅ Exit code non-zero
- ✅ No file created

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 11: CSV Import into Excel

**Steps:**
1. Export to CSV:
   ```bash
   python3 main.py export --format csv --output excel_test.csv
   ```
2. Open in Microsoft Excel or Google Sheets
3. Verify formatting

**Expected Result:**
- ✅ Opens without errors
- ✅ Header row recognized
- ✅ Category column is text
- ✅ Amount column is numeric
- ✅ No encoding issues (UTF-8 preserved)
- ✅ Can sort/filter data
- ✅ Can create charts from data

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 12: File Overwrite

**Steps:**
1. Export to file:
   ```bash
   python3 main.py export --format csv --output overwrite.csv
   ```
2. Export again to same file:
   ```bash
   python3 main.py export --format csv --output overwrite.csv
   ```

**Expected Result:**
- ✅ Second export overwrites first
- ✅ No error about file exists
- ✅ File contains latest export
- ✅ No confirmation prompt needed

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

## Usage Examples

```bash
# Basic CSV export with auto-generated filename
python3 main.py export --format csv

# JSON export with custom filename
python3 main.py export --format json --output my_data.json

# TXT export for human reading
python3 main.py export --format txt --output report.txt

# Export only groceries
python3 main.py export --format csv --category "Groceries" --output groceries.csv

# Export categories over $100
python3 main.py export --format json --min-amount 100 --output high_spending.json

# Combine filters
python3 main.py export --format csv --category "Util" --min-amount 50 --max-amount 300
```

## Example Output

### CSV Format
```
category,amount
Entertainment,75.25
Groceries/Food,450.75
Utilities/Bills,250.00
```

### JSON Format
```json
{
  "export_date": "2025-12-13",
  "total_categories": 3,
  "grand_total": 776.0,
  "categories": [
    {
      "category": "Entertainment",
      "amount": 75.25
    },
    {
      "category": "Groceries/Food",
      "amount": 450.75
    },
    {
      "category": "Utilities/Bills",
      "amount": 250.0
    }
  ]
}
```

### TXT Format
```
================================================================================
F.U.C.K. SPENDING REPORT
================================================================================
Export Date: 2025-12-13
Total Categories: 3
Grand Total: $776.00
--------------------------------------------------------------------------------

Category                                           Amount
--------------------------------------------------------------------------------
Entertainment                                      $    75.25
Groceries/Food                                     $   450.75
Utilities/Bills                                    $   250.00
================================================================================
```

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Test 1: Basic CSV Export | ⬜ | |
| Test 2: JSON Export | ⬜ | |
| Test 3: TXT Export | ⬜ | |
| Test 4: Default Filename | ⬜ | |
| Test 5: Category Filter | ⬜ | |
| Test 6: Amount Filter | ⬜ | |
| Test 7: Combined Filters | ⬜ | |
| Test 8: No Matches | ⬜ | |
| Test 9: No Data | ⬜ | |
| Test 10: Invalid Format | ⬜ | |
| Test 11: Excel Import | ⬜ | |
| Test 12: File Overwrite | ⬜ | |

**Overall Status:** Not Tested

---

**Test Completed By:** _____________
**Date:** _____________
**Environment:** _____________
