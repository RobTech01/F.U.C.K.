# Manual Test Procedure: Session 7 - Bulk Operations

## Test Objective
Validate that bulk-edit command allows users to recategorize multiple addresses at once with pattern matching and preview.

## Prerequisites
- Hash table with multiple addresses
- Some addresses sharing common patterns (e.g., "walmart", "amazon")

## Test Cases

### Test 1: Basic Bulk Edit with Preview

**Steps:**
1. Run bulk edit:
   ```bash
   python3 main.py bulk-edit --pattern "Doe" --category "Personal"
   ```
2. Review preview
3. Confirm with 'y'

**Expected Result:**
- ✅ Shows search message
- ✅ Displays preview with matching addresses
- ✅ Shows old → new category for each
- ✅ Prompts for confirmation
- ✅ Applies changes after confirmation
- ✅ Success message with count
- ✅ Changes saved

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 2: Bulk Edit with Auto-Confirm

**Steps:**
1. Run with --yes flag:
   ```bash
   python3 main.py bulk-edit --pattern "Corporation" --category "Business" --yes
   ```

**Expected Result:**
- ✅ Shows preview
- ✅ NO confirmation prompt
- ✅ Automatically applies changes
- ✅ Success message

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 3: Cancel Bulk Edit

**Steps:**
1. Run bulk edit
2. When prompted, enter 'n' to cancel

**Expected Result:**
- ✅ Message: "Bulk edit cancelled"
- ✅ No changes applied
- ✅ Clean exit (return code 0)

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 4: No Matches Found

**Steps:**
1. Use pattern that doesn't match any addresses:
   ```bash
   python3 main.py bulk-edit --pattern "XYZ999" --category "Test"
   ```

**Expected Result:**
- ✅ Error: "No addresses found matching pattern 'XYZ999'"
- ✅ Helpful message about target category
- ✅ Exit code 1

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 5: Case-Insensitive Matching

**Steps:**
1. Try different cases:
   ```bash
   python3 main.py bulk-edit --pattern "walmart" --category "Shopping"
   python3 main.py bulk-edit --pattern "WALMART" --category "Shopping"
   ```

**Expected Result:**
- ✅ Both commands find same addresses
- ✅ Case-insensitive pattern matching works

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 6: Missing Required Arguments

**Steps:**
1. Try without --pattern:
   ```bash
   python3 main.py bulk-edit --category "Test"
   ```
2. Try without --category:
   ```bash
   python3 main.py bulk-edit --pattern "test"
   ```

**Expected Result:**
- ✅ Error message about missing required argument
- ✅ Shows usage help
- ✅ Exit code non-zero

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 7: Verify Changes Persist

**Steps:**
1. Bulk edit some addresses
2. Run edit command to view one of the changed addresses

**Expected Result:**
- ✅ Address shows new category
- ✅ Changes persisted to database
- ✅ Can change again if needed

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

## Usage Examples

```bash
# Basic bulk edit (with confirmation)
python3 main.py bulk-edit --pattern "walmart" --category "Groceries/Food"

# Auto-confirm (skip prompt)
python3 main.py bulk-edit --pattern "amazon" --category "Shopping" --yes

# Partial match (finds all addresses containing "store")
python3 main.py bulk-edit --pattern "store" --category "Retail"
```

## Example Output

```
================================================================================
BULK RECATEGORIZATION PREVIEW
================================================================================
Addresses to be recategorized: 3
New category: Groceries/Food
--------------------------------------------------------------------------------

1. Walmart Store #123 (Shopping → Groceries/Food)
2. Walmart Online (Shopping → Groceries/Food)
3. Walmart Neighborhood Market (Retail → Groceries/Food)

================================================================================

Apply these changes? (y/n): y

Applying changes...

✓ Successfully recategorized 3 addresses
✓ Changes saved successfully

Note: Category totals will be updated when you next process these addresses
```

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Test 1: Basic with Preview | ⬜ | |
| Test 2: Auto-Confirm | ⬜ | |
| Test 3: Cancel | ⬜ | |
| Test 4: No Matches | ⬜ | |
| Test 5: Case-Insensitive | ⬜ | |
| Test 6: Missing Args | ⬜ | |
| Test 7: Persistence | ⬜ | |

**Overall Status:** Not Tested

---

**Test Completed By:** _____________
**Date:** _____________
**Environment:** _____________
