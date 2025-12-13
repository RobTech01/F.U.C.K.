# Manual Test Procedure: Session 1 - Transaction Review

## Test Objective
Validate that the review mode functionality works correctly, allowing users to review transactions before saving.

## Prerequisites
- Dummy CSV file exists: `dummy-data/january.csv`
- Python 3.6+ installed
- All dependencies installed from `requirements.txt`

## Test Cases

### Test 1: Review Mode Enabled (Default Behavior)

**Steps:**
1. Clean environment:
   ```bash
   rm -rf storage/
   rm -f config.json
   ```

2. Run process command with review mode (default):
   ```bash
   python3 main.py process dummy-data/january.csv
   ```

3. When prompted:
   - Enter encryption key (first time)
   - Select column mappings as needed
   - Categorize new addresses as prompted

4. After processing, observe:
   - Review screen should appear showing:
     - Transaction count
     - Table with Date, Amount, Category columns
     - Category totals summary
   - Options: [c] Confirm, [x] Cancel, [e] Edit

5. Choose [c] to confirm

**Expected Result:**
- ✅ Review screen displays all transactions
- ✅ Category totals are accurate
- ✅ Confirming saves data to `storage/hash_table.enc`
- ✅ Success message: "Changes applied successfully"

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 2: Review Mode Disabled (--no-review Flag)

**Steps:**
1. Clean environment (optional):
   ```bash
   rm -rf storage/
   rm -f config.json
   ```

2. Run process command with --no-review:
   ```bash
   python3 main.py process dummy-data/january.csv --no-review
   ```

3. Complete categorization prompts as normal

**Expected Result:**
- ✅ NO review screen appears
- ✅ Data is saved immediately after processing
- ✅ Success message appears without confirmation prompt

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 3: User Cancels Review

**Steps:**
1. Process a CSV file:
   ```bash
   python3 main.py process dummy-data/january.csv
   ```

2. When review screen appears, choose [x] to cancel

**Expected Result:**
- ✅ Message: "Processing cancelled by user"
- ✅ Message: "No changes were saved to the database"
- ✅ Error message about cancelled review
- ✅ `storage/hash_table.enc` is NOT created/modified
- ✅ Exit code is non-zero (error state)

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 4: Review with Existing Data

**Steps:**
1. Process January CSV and confirm:
   ```bash
   python3 main.py process dummy-data/january.csv
   ```
   Choose [c] to confirm

2. Process February CSV:
   ```bash
   python3 main.py process dummy-data/february.csv
   ```

3. Review screen should show:
   - Only new transactions from February
   - Updated category totals (combining January + February)

4. Choose [c] to confirm

**Expected Result:**
- ✅ Review shows only new transactions
- ✅ Category totals accumulate correctly
- ✅ No duplicate transactions
- ✅ Both months' data persists

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 5: Review Screen Display Format

**Steps:**
1. Process a CSV file and observe review screen format

**Expected Result:**
- ✅ Header: "TRANSACTION REVIEW" with === border
- ✅ Transaction count displayed
- ✅ Table columns aligned: # | Date | Amount | Category
- ✅ Date truncated to 12 chars max
- ✅ Amount formatted as $XX.XX
- ✅ Category truncated to 30 chars max
- ✅ Category totals section with === border
- ✅ Categories sorted alphabetically
- ✅ Totals right-aligned with $ prefix
- ✅ Clear prompt for user action

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 6: Edit Option (Not Yet Implemented)

**Steps:**
1. Process a CSV and at review screen, choose [e]

**Expected Result:**
- ✅ Message: "Edit functionality coming in Session 2!"
- ✅ Prompt returns to confirmation options (c/x/e)
- ✅ Does not crash or exit

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Test 1: Review Enabled | ⬜ | |
| Test 2: Review Disabled | ⬜ | |
| Test 3: User Cancels | ⬜ | |
| Test 4: Incremental Data | ⬜ | |
| Test 5: Display Format | ⬜ | |
| Test 6: Edit Placeholder | ⬜ | |

**Overall Status:** Not Tested

---

## Known Issues
None identified yet.

---

## Notes
- Review mode is enabled by default (opt-out with --no-review)
- Edit functionality will be implemented in Session 2
- Tests require working encryption environment

---

**Test Completed By:** _____________
**Date:** _____________
**Environment:** _____________
