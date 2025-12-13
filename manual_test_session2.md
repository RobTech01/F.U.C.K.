# Manual Test Procedure: Session 2 - Fix Categorization Mistakes

## Test Objective
Validate that the edit command allows users to recategorize addresses without manual database editing.

## Prerequisites
- Hash table with existing data (`storage/hash_table.enc`)
- Python 3.6+ installed
- Session 1 completed (data exists to edit)

## Test Cases

### Test 1: Search and Edit an Address

**Steps:**
1. Ensure you have processed data:
   ```bash
   python3 main.py process dummy-data/january.csv
   ```

2. Run edit command without search term:
   ```bash
   python3 main.py edit
   ```

3. When prompted, enter a search term (e.g., "Doe"):
   ```
   Enter search term (address substring): Doe
   ```

4. Observe search results display

5. Select an address by number

6. Review current category

7. Select new category from list (or enter custom)

8. Confirm changes

**Expected Result:**
- ✅ Search finds matching addresses
- ✅ Results display in table format
- ✅ Can select address by number
- ✅ Current category shown
- ✅ Can select from available categories
- ✅ Success message with old → new category
- ✅ Changes saved message
- ✅ Note about totals update shown

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 2: Edit with Command-Line Search

**Steps:**
1. Run edit with --search flag:
   ```bash
   python3 main.py edit --search "Corporation"
   ```

2. Select from results

3. Change category

**Expected Result:**
- ✅ Skips search prompt
- ✅ Goes directly to results
- ✅ Rest of flow works normally

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 3: Cancel During Address Selection

**Steps:**
1. Run edit command:
   ```bash
   python3 main.py edit
   ```

2. Enter search term

3. When prompted to select address, enter 'c' to cancel

**Expected Result:**
- ✅ Message: "Edit cancelled"
- ✅ No changes saved
- ✅ Clean exit (return code 0)

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 4: Cancel During Category Selection

**Steps:**
1. Run edit and search for address

2. Select an address

3. When prompted for new category, enter 'c' to cancel

**Expected Result:**
- ✅ Message: "Edit cancelled"
- ✅ No changes saved
- ✅ Clean exit

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 5: Search with No Matches

**Steps:**
1. Run edit:
   ```bash
   python3 main.py edit
   ```

2. Enter search term that doesn't exist:
   ```
   Enter search term: XYZ123NotExist
   ```

**Expected Result:**
- ✅ Message: "No addresses found matching 'XYZ123NotExist'"
- ✅ No addresses found message
- ✅ Exit cleanly (return code 1)

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 6: Select Same Category (No-Op)

**Steps:**
1. Run edit and search

2. Select an address with category "Groceries/Food"

3. When selecting new category, choose "Groceries/Food" again

**Expected Result:**
- ✅ Message: "Address already has this category"
- ✅ No changes saved
- ✅ Exit with error code

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 7: Custom Category Entry

**Steps:**
1. Run edit and select address

2. When prompted for category, enter custom text (not a number):
   ```
   > MyCustomCategory
   ```

**Expected Result:**
- ✅ Accepts custom category name
- ✅ Saves successfully
- ✅ Success message shows custom category

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 8: Verify Persistence

**Steps:**
1. Edit an address and change category

2. Exit program

3. Run edit again and search for same address

**Expected Result:**
- ✅ Address shows NEW category (not old)
- ✅ Changes persisted to database
- ✅ Can change again if needed

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 9: Edit with No Existing Data

**Steps:**
1. Remove hash table:
   ```bash
   rm -f storage/hash_table.enc
   ```

2. Run edit:
   ```bash
   python3 main.py edit
   ```

**Expected Result:**
- ✅ Error: "No hash table found. Process a CSV file first."
- ✅ Exit with error code 1
- ✅ Helpful message to user

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 10: Search Results Display Format

**Steps:**
1. Run edit with search that matches multiple addresses

2. Observe display format

**Expected Result:**
- ✅ Header: "SEARCH RESULTS" with === border
- ✅ "Found X matching address(es)" message
- ✅ Table with columns: # | Address | Category
- ✅ Addresses truncated to 40 chars
- ✅ Categories truncated to 30 chars
- ✅ Clear numbering for selection

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Test 1: Search and Edit | ⬜ | |
| Test 2: CLI Search | ⬜ | |
| Test 3: Cancel Selection | ⬜ | |
| Test 4: Cancel Category | ⬜ | |
| Test 5: No Matches | ⬜ | |
| Test 6: Same Category | ⬜ | |
| Test 7: Custom Category | ⬜ | |
| Test 8: Persistence | ⬜ | |
| Test 9: No Data Error | ⬜ | |
| Test 10: Display Format | ⬜ | |

**Overall Status:** Not Tested

---

## Known Limitations

- **Category totals:** The note mentions "Category totals will be updated when you next process this address"
  - This is by design - totals are based on transaction processing
  - Recategorization only updates the address→category mapping
  - Future transactions with this address will use the new category
  - To update totals retroactively, would need to reprocess CSVs

---

## Integration with Session 1

The edit functionality complements Session 1's review mode:
- Review mode catches mistakes before saving
- Edit mode fixes mistakes after saving
- Together they provide complete control over categorization

---

**Test Completed By:** _____________
**Date:** _____________
**Environment:** _____________
