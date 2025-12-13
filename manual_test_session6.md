# Manual Test Procedure: Session 6 - Spending Insights & Reports

## Test Objective
Validate that the report command generates useful spending insights with visualization.

## Prerequisites
- Hash table with categorized transactions
- Multiple categories with varying amounts

## Setup
```bash
python3 main.py process dummy-data/january.csv
python3 main.py process dummy-data/february.csv
```

## Test Cases

### Test 1: Basic Report Generation

**Steps:**
1. Generate basic report:
   ```bash
   python3 main.py report
   ```

**Expected Result:**
- ✅ Shows "SPENDING BREAKDOWN BY CATEGORY" header
- ✅ Lists total amount
- ✅ Shows category count
- ✅ Categories sorted by amount (highest first)
- ✅ Each category shows: number, name, amount, percentage
- ✅ ASCII bar charts displayed (█ characters)
- ✅ Professional formatting (80-char width)

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 2: Report Without Bars

**Steps:**
1. Generate report without bars:
   ```bash
   python3 main.py report --no-bars
   ```

**Expected Result:**
- ✅ Same data as basic report
- ✅ No ASCII bar charts shown
- ✅ More compact display
- ✅ All other info intact

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 3: Report With Statistics

**Steps:**
1. Generate report with stats:
   ```bash
   python3 main.py report --stats
   ```

**Expected Result:**
- ✅ Shows basic report
- ✅ Additional STATISTICS section
- ✅ Shows average per category
- ✅ Shows median
- ✅ Shows highest category with amount
- ✅ Shows lowest category with amount
- ✅ Accurate calculations

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 4: Combined Flags

**Steps:**
1. Use both flags:
   ```bash
   python3 main.py report --no-bars --stats
   ```

**Expected Result:**
- ✅ No bars shown
- ✅ Statistics shown
- ✅ Both flags work together

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 5: Report With No Data

**Steps:**
1. Remove hash table:
   ```bash
   rm -f storage/hash_table.enc
   ```
2. Run report:
   ```bash
   python3 main.py report
   ```

**Expected Result:**
- ✅ Error: "No hash table found. Process a CSV file first."
- ✅ Helpful message to user
- ✅ Exit code 1

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 6: Percentage Accuracy

**Steps:**
1. Generate report and verify percentages sum to 100%

**Expected Result:**
- ✅ All percentages add up to 100.0%
- ✅ Rounding handled correctly
- ✅ Each percentage accurate to 1 decimal place

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 7: Bar Chart Scaling

**Steps:**
1. Observe bar lengths in report

**Expected Result:**
- ✅ Largest category has longest bar
- ✅ Bar lengths proportional to amounts
- ✅ Smallest category has shortest (or no) bar
- ✅ Bars scale correctly

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

## Usage Examples

```bash
# Basic report with bars
python3 main.py report

# Report without visual bars
python3 main.py report --no-bars

# Report with additional statistics
python3 main.py report --stats

# Minimal report (no bars, with stats)
python3 main.py report --no-bars --stats
```

## Example Output

```
================================================================================
SPENDING BREAKDOWN BY CATEGORY
================================================================================
Total: $776.00
Categories: 3
--------------------------------------------------------------------------------

1. Groceries/Food                        $    450.75  ( 58.1%)
   ████████████████████████████████████████
2. Utilities/Bills                       $    250.00  ( 32.2%)
   ██████████████████████
3. Entertainment                         $     75.25  (  9.7%)
   ██████

================================================================================
```

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Test 1: Basic Report | ⬜ | |
| Test 2: No Bars | ⬜ | |
| Test 3: With Stats | ⬜ | |
| Test 4: Combined Flags | ⬜ | |
| Test 5: No Data | ⬜ | |
| Test 6: Percentage Accuracy | ⬜ | |
| Test 7: Bar Scaling | ⬜ | |

**Overall Status:** Not Tested

---

**Test Completed By:** _____________
**Date:** _____________
**Environment:** _____________
