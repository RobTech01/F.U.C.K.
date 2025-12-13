# Manual Test Procedure: Session 3 - Enhanced View with Filters

## Test Objective
Validate that the view command supports filtering by category name and amount ranges.

## Prerequisites
- Hash table with existing categorized data
- Multiple categories with varying amounts
- Python 3.6+ installed

## Setup
Process some test data first:
```bash
python3 main.py process dummy-data/january.csv
python3 main.py process dummy-data/february.csv
```

## Test Cases

### Test 1: View Without Filters (Baseline)

**Steps:**
1. Run view command without filters:
   ```bash
   python3 main.py view
   ```

**Expected Result:**
- ✅ Shows "CATEGORY TOTALS" header
- ✅ Lists all categories alphabetically
- ✅ Shows amounts formatted as $XXX.XX
- ✅ Shows grand total at bottom
- ✅ Shows count: "Showing X categories"
- ✅ No filter information displayed

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 2: Filter by Category Name (Exact Match)

**Steps:**
1. Filter for specific category:
   ```bash
   python3 main.py view --category "Groceries"
   ```

**Expected Result:**
- ✅ Shows "FILTERED CATEGORY TOTALS" header
- ✅ Shows "Filters applied:" section
- ✅ Lists filter: "Category contains: 'Groceries'"
- ✅ Only shows categories containing "Groceries"
- ✅ Grand total reflects filtered categories only
- ✅ Shows correct count

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 3: Filter by Category (Case-Insensitive)

**Steps:**
1. Try different cases:
   ```bash
   python3 main.py view --category "food"
   python3 main.py view --category "FOOD"
   python3 main.py view --category "FoOd"
   ```

**Expected Result:**
- ✅ All three commands show same results
- ✅ Matches "Groceries/Food" regardless of case
- ✅ Case-insensitive matching works

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 4: Filter by Minimum Amount

**Steps:**
1. Filter by minimum:
   ```bash
   python3 main.py view --min-amount 100
   ```

**Expected Result:**
- ✅ Shows "FILTERED CATEGORY TOTALS"
- ✅ Shows filter: "Minimum amount: $100.00"
- ✅ Only shows categories with totals >= $100.00
- ✅ Categories under $100 not shown
- ✅ Grand total is accurate

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 5: Filter by Maximum Amount

**Steps:**
1. Filter by maximum:
   ```bash
   python3 main.py view --max-amount 500
   ```

**Expected Result:**
- ✅ Shows filter: "Maximum amount: $500.00"
- ✅ Only shows categories with totals <= $500.00
- ✅ Categories over $500 not shown
- ✅ Grand total reflects filtered data

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 6: Filter by Amount Range

**Steps:**
1. Use both min and max:
   ```bash
   python3 main.py view --min-amount 50 --max-amount 200
   ```

**Expected Result:**
- ✅ Shows both filters:
  - "Minimum amount: $50.00"
  - "Maximum amount: $200.00"
- ✅ Only shows categories in range [50, 200]
- ✅ Excludes categories outside range
- ✅ Grand total is sum of shown categories

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 7: Combine Category and Amount Filters

**Steps:**
1. Use multiple filters:
   ```bash
   python3 main.py view --category "i" --min-amount 100
   ```

**Expected Result:**
- ✅ Shows all three filters applied
- ✅ Results match BOTH category AND amount criteria
- ✅ Only categories containing "i" with total >= $100
- ✅ Correct filtering logic (AND, not OR)

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 8: Filter with No Matches

**Steps:**
1. Use filter that matches nothing:
   ```bash
   python3 main.py view --category "NonexistentCategory"
   ```

**Expected Result:**
- ✅ Shows "FILTERED CATEGORY TOTALS"
- ✅ Shows filter applied
- ✅ Message: "No categories match the specified filters."
- ✅ No error, graceful handling
- ✅ No grand total shown (no data)

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 9: Filters with --all Flag

**Steps:**
1. Try filters with --all:
   ```bash
   python3 main.py view --all --category "Food"
   ```

**Expected Result:**
- ✅ Warning: "--all mode doesn't support filters. Showing all data."
- ✅ Shows full hash table (unfiltered)
- ✅ Filters are ignored
- ✅ User informed filters don't work with --all

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 10: Edge Case - Exact Amount Match

**Steps:**
1. Filter for exact amount (if known):
   ```bash
   # Find a category's exact total first
   python3 main.py view
   # Then filter for that exact amount
   python3 main.py view --min-amount 250.00 --max-amount 250.00
   ```

**Expected Result:**
- ✅ Shows only category(ies) with exactly $250.00
- ✅ Inclusive boundaries (>= min, <= max)
- ✅ Correct match

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 11: Display Format Validation

**Steps:**
1. Run filtered view and verify formatting:
   ```bash
   python3 main.py view --category "s"
   ```

**Expected Result:**
- ✅ 80-character width formatting
- ✅ Categories left-aligned (50 chars)
- ✅ Amounts right-aligned (12 chars) with $ prefix
- ✅ Amounts show 2 decimal places
- ✅ Clear separator lines (= and -)
- ✅ Professional appearance

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 12: Decimal Amount Filtering

**Steps:**
1. Use decimal values:
   ```bash
   python3 main.py view --min-amount 99.99 --max-amount 150.50
   ```

**Expected Result:**
- ✅ Accepts decimal input
- ✅ Filters correctly with decimals
- ✅ Displays decimals in filter description

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Test 1: No Filters | ⬜ | |
| Test 2: Exact Match | ⬜ | |
| Test 3: Case-Insensitive | ⬜ | |
| Test 4: Min Amount | ⬜ | |
| Test 5: Max Amount | ⬜ | |
| Test 6: Amount Range | ⬜ | |
| Test 7: Combined Filters | ⬜ | |
| Test 8: No Matches | ⬜ | |
| Test 9: --all Override | ⬜ | |
| Test 10: Exact Amount | ⬜ | |
| Test 11: Display Format | ⬜ | |
| Test 12: Decimal Amounts | ⬜ | |

**Overall Status:** Not Tested

---

## Usage Examples

```bash
# View all categories
python3 main.py view

# Filter by category name
python3 main.py view --category "Groceries"
python3 main.py view --category "utilities"  # Case-insensitive

# Filter by amount
python3 main.py view --min-amount 100
python3 main.py view --max-amount 500
python3 main.py view --min-amount 50 --max-amount 200

# Combine filters
python3 main.py view --category "food" --min-amount 100
python3 main.py view --category "s" --min-amount 50 --max-amount 300

# Full details (filters not supported)
python3 main.py view --all
```

---

## Known Limitations

1. **--all mode:** Filters are not supported with --all flag (full hash table display)
2. **Category totals only:** Can filter by category total, not individual transactions (data structure limitation)
3. **Substring matching:** Category filter uses substring match, not regex or exact match

---

## Integration with Previous Sessions

- **Session 1:** Review mode and filtering are independent features
- **Session 2:** Can use `edit` to change categories, then `view` with filters to verify changes

---

**Test Completed By:** _____________
**Date:** _____________
**Environment:** _____________
