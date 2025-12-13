# Manual Test Procedure: Session 8 - Interactive Help & Onboarding

## Test Objective
Validate that the help system provides useful guidance and the setup wizard guides new users through initial configuration.

## Prerequisites
- F.U.C.K. installed and working
- Terminal access

## Test Cases

### Test 1: Help Overview

**Steps:**
1. Run help without topic:
   ```bash
   python3 main.py help
   ```

**Expected Result:**
- ✅ Shows "F.U.C.K. HELP SYSTEM" header
- ✅ Lists all available topics (setup, categories, csv-format, security)
- ✅ Shows usage examples
- ✅ Shows quick start commands
- ✅ Lists common commands
- ✅ Professional formatting (80-char width)

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 2: Help Topic - Setup

**Steps:**
1. Get setup help:
   ```bash
   python3 main.py help setup
   ```

**Expected Result:**
- ✅ Shows "FIRST-TIME SETUP GUIDE" header
- ✅ Includes sections: Prepare Data, Security Setup, Process CSV, View Data
- ✅ Mentions FUCK_GLOBAL_SALT and FUCK_ENCRYPTION_KEY
- ✅ Shows export command examples
- ✅ Suggests running `init` wizard
- ✅ Clear, actionable instructions

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 3: Help Topic - Categories

**Steps:**
1. Get categories help:
   ```bash
   python3 main.py help categories
   ```

**Expected Result:**
- ✅ Shows "CATEGORY MANAGEMENT GUIDE" header
- ✅ Lists built-in categories (Groceries/Food, etc.)
- ✅ Explains custom category creation
- ✅ Shows view, edit, and bulk-edit examples
- ✅ Includes tips for category management
- ✅ Professional formatting

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 4: Help Topic - CSV Format

**Steps:**
1. Get CSV format help:
   ```bash
   python3 main.py help csv-format
   ```

**Expected Result:**
- ✅ Shows "CSV FORMAT GUIDE" header
- ✅ Lists required columns (Date, Address, Amount)
- ✅ Lists optional columns
- ✅ Shows supported date formats
- ✅ Includes bank-specific examples (Chase, BofA, Wells Fargo, etc.)
- ✅ Shows example CSV format
- ✅ Testing tips included

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 5: Help Topic - Security

**Steps:**
1. Get security help:
   ```bash
   python3 main.py help security
   ```

**Expected Result:**
- ✅ Shows "SECURITY GUIDE" header
- ✅ Explains encryption (Fernet, AES-128, SHA-256)
- ✅ Describes both required secrets (salt and key)
- ✅ Shows key generation examples
- ✅ Lists best practices
- ✅ Explains threat model
- ✅ Clear warnings about key storage

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 6: Help Topic - Unknown

**Steps:**
1. Try unknown topic:
   ```bash
   python3 main.py help foobar
   ```

**Expected Result:**
- ✅ Shows "UNKNOWN HELP TOPIC: foobar" message
- ✅ Lists available topics
- ✅ Suggests trying valid topics
- ✅ Helpful error message

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 7: Help Case-Insensitivity

**Steps:**
1. Try different cases:
   ```bash
   python3 main.py help SETUP
   python3 main.py help Setup
   python3 main.py help setup
   ```

**Expected Result:**
- ✅ All three commands show same content
- ✅ Case-insensitive topic matching works
- ✅ No errors

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 8: Setup Wizard - Complete Flow

**Steps:**
1. Run wizard:
   ```bash
   python3 main.py init
   ```
2. Press Enter at each prompt
3. Answer 'n' for "already have keys"
4. Complete all steps

**Expected Result:**
- ✅ Shows welcome message
- ✅ Step 1: Security setup information
- ✅ Step 2: CSV preparation guidance
- ✅ Step 3: Category structure recommendations
- ✅ Completion message with next steps
- ✅ No errors or crashes
- ✅ Can exit cleanly

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 9: Setup Wizard - Cancel Early

**Steps:**
1. Run wizard:
   ```bash
   python3 main.py init
   ```
2. Press Ctrl+C at first prompt

**Expected Result:**
- ✅ Shows "Setup cancelled by user" message
- ✅ Clean exit with no traceback
- ✅ Exit code 130

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 10: Setup Wizard - Already Have Keys

**Steps:**
1. Run wizard:
   ```bash
   python3 main.py init
   ```
2. Press Enter at welcome
3. Answer 'y' for "already have keys"
4. Complete wizard

**Expected Result:**
- ✅ Shows verification instructions
- ✅ Suggests echo $FUCK_GLOBAL_SALT
- ✅ Continues with rest of wizard
- ✅ Completion message shown

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 11: Command Help Integration

**Steps:**
1. Check that each command has --help:
   ```bash
   python3 main.py process --help
   python3 main.py view --help
   python3 main.py edit --help
   python3 main.py bulk-edit --help
   python3 main.py report --help
   python3 main.py help --help
   python3 main.py init --help
   ```

**Expected Result:**
- ✅ All commands show detailed help
- ✅ Argument descriptions clear
- ✅ Examples provided where appropriate
- ✅ No errors

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

### Test 12: Help Consistency

**Steps:**
1. Compare help content across commands
2. Check terminology consistency
3. Verify examples match actual command syntax

**Expected Result:**
- ✅ Consistent terminology (e.g., "category" vs "categories")
- ✅ Command examples work as shown
- ✅ No contradictions between topics
- ✅ Professional, clear language throughout

**Status:** ⬜ Not Tested | ⬜ Passed | ⬜ Failed

---

## Usage Examples

```bash
# Get overview of help system
python3 main.py help

# Get specific help topic
python3 main.py help setup
python3 main.py help categories
python3 main.py help csv-format
python3 main.py help security

# Run setup wizard for new users
python3 main.py init

# Get command-specific help
python3 main.py process --help
python3 main.py report --help
```

## Example Output

### Help Overview
```
================================================================================
F.U.C.K. HELP SYSTEM
================================================================================

Fund Utilization and Categorization Kit - Personal Finance Tracker

Available help topics:

  setup       - First-time setup guide and getting started
  categories  - How to manage and organize spending categories
  csv-format  - Understanding CSV file formats and requirements
  security    - Security features and encryption details

USAGE:
  python3 main.py help <topic>

  Example: python3 main.py help setup

QUICK START:
  1. Run the setup wizard: python3 main.py init
  2. Process your first CSV: python3 main.py process transactions.csv
  3. View your data: python3 main.py view
...
```

### Setup Wizard
```
================================================================================
F.U.C.K. INTERACTIVE SETUP WIZARD
================================================================================

Welcome to F.U.C.K. (Fund Utilization and Categorization Kit)!

This wizard will help you get started with tracking your finances.

We'll walk through:
  1. Understanding security requirements
  2. Setting up encryption keys
  3. Preparing your CSV file
  4. Choosing your category structure
  5. Processing your first transactions

This should take about 5-10 minutes.

Press Enter to continue or Ctrl+C to exit...
```

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Test 1: Help Overview | ⬜ | |
| Test 2: Setup Topic | ⬜ | |
| Test 3: Categories Topic | ⬜ | |
| Test 4: CSV Format Topic | ⬜ | |
| Test 5: Security Topic | ⬜ | |
| Test 6: Unknown Topic | ⬜ | |
| Test 7: Case-Insensitive | ⬜ | |
| Test 8: Wizard Complete | ⬜ | |
| Test 9: Wizard Cancel | ⬜ | |
| Test 10: Wizard With Keys | ⬜ | |
| Test 11: Command Help | ⬜ | |
| Test 12: Consistency | ⬜ | |

**Overall Status:** Not Tested

---

**Test Completed By:** _____________
**Date:** _____________
**Environment:** _____________
