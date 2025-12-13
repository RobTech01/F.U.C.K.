# F.U.C.K. Testing Plan

Following [Anthropic's effective harness methodology](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) for systematic testing.

## Testing Philosophy: KISS (Keep It Simple, Stupid)

- **Manual testing first** - Understand the user flow before automating
- **Mock external dependencies** - Don't rely on real encryption keys or files
- **One test, one purpose** - Each test validates exactly one thing
- **Progress tracking** - Document what's tested and what's not

---

## Current Test Coverage

### ✅ Already Tested (Existing)
- **Core validation** (`tests/test_core.py`) - 9 tests
  - String sanitization, transaction validation, ID generation, filepath sanitization
- **Config management** (`tests/test_config.py`) - 3 tests
  - Config creation, column mapping save/load, bank identifier
- **Integration smoke tests** (`integration_test.py`) - 5 checks
  - Imports, CSV validation, transaction processing, security, config

### ❌ Not Yet Tested
- **Crypto operations** (`package/crypto.py`)
- **Storage layer** (`package/storage.py`)
- **CSV reading** (`package/read_data.py`)
- **Category manager** (`package/category_manager.py`)
- **CLI interactions** (`package/cli.py`)
- **Main entry points** (`main.py` commands)
- **End-to-end user workflows**

---

## Test Plan Structure

Following Anthropic's approach: **incremental, testable, trackable**

### Phase 1: Unit Tests for Untested Modules (Mock-Heavy)

#### 1.1 Crypto Module Tests (`tests/test_crypto.py`)
**Purpose**: Validate encryption/decryption and hashing without real keys

**Mocking strategy**: Use known test vectors
- ✅ Test: Key derivation from password (mock PBKDF2)
- ✅ Test: Encrypt then decrypt returns original data
- ✅ Test: Hash generation is deterministic
- ✅ Test: Invalid password fails decryption

**Manual validation**:
1. Run crypto with test password "test123"
2. Verify encrypted data is not readable
3. Verify decryption works

#### 1.2 Storage Module Tests (`tests/test_storage.py`)
**Purpose**: Test hash table save/load without real encryption

**Mocking strategy**: Mock cipher_suite, use temp files
- ✅ Test: Initialize empty hash table
- ✅ Test: Save and load hash table (mocked encryption)
- ✅ Test: Get categories and totals from hash table
- ✅ Test: Handle corrupted storage file gracefully

**Manual validation**:
1. Create test hash table with known data
2. Save to temp file
3. Load and verify structure intact

#### 1.3 CSV Reading Tests (`tests/test_read_data.py`)
**Purpose**: Test CSV parsing without processing full pipeline

**Mocking strategy**: Use in-memory CSV strings
- ✅ Test: Parse valid CSV with standard headers
- ✅ Test: Handle missing columns
- ✅ Test: Handle malformed CSV (extra commas, quotes)
- ✅ Test: Respect column mappings
- ✅ Test: File size limits (100MB)

**Manual validation**:
1. Create minimal CSV: `date,address,amount`
2. Parse and verify data extracted correctly

#### 1.4 Category Manager Tests (`tests/test_category_manager.py`)
**Purpose**: Test categorization logic without user prompts

**Mocking strategy**: Mock CLI prompts, use predefined hash table
- ✅ Test: Lookup existing address returns category
- ✅ Test: New address triggers prompt (mock user input)
- ✅ Test: Update hash table with new category
- ✅ Test: Handle duplicate addresses correctly

**Manual validation**:
1. Create hash table with "Walmart" → "Groceries/Food"
2. Categorize transaction for "Walmart"
3. Verify returned "Groceries/Food" without prompt

---

### Phase 2: Integration Tests (Component Interaction)

#### 2.1 Crypto + Storage Integration
**Purpose**: Test encrypted save/load cycle

**Test**:
1. Initialize crypto with test password
2. Create hash table with test data
3. Save encrypted
4. Load encrypted
5. Verify data matches

**No mocking**: Use real crypto, temp files

#### 2.2 CSV + Category Manager Integration
**Purpose**: Test processing pipeline without crypto

**Test**:
1. Mock CSV file with 3 transactions
2. Mock hash table with 1 known address
3. Process CSV (mock user prompts for 2 new addresses)
4. Verify hash table updated correctly

**Mocking**: CLI prompts only

#### 2.3 Full Pipeline Mock Test
**Purpose**: Test complete flow with mocked user interaction

**Test**:
1. Mock crypto initialization (predefined key)
2. Mock CSV file (5 transactions, 3 new addresses)
3. Mock user prompts (predefined categories)
4. Run process command
5. Verify hash table has 5 entries with correct categories

**Mocking**: User input only (crypto and storage are real)

---

### Phase 3: End-to-End Manual Testing Procedures

These are **manual test scripts** - not automated. Follow step-by-step.

#### 3.1 First-Time Setup Test (Clean Slate)
**Purpose**: Verify new user experience

**Manual steps**:
```bash
# 1. Clean environment
rm -rf storage/
rm config.json

# 2. Run first process
python3 main.py process dummy-data/january.csv

# Expected prompts:
# - Enter encryption key: (type "testkey123")
# - Confirm encryption key: (type "testkey123")
# - For each unknown address: (select category 1-13)

# 3. Verify output
# - Should see "X/Y transactions processed"
# - Should create storage/hash_table.enc
# - Should create config.json

# 4. View results
python3 main.py view

# Expected: Category totals displayed

# 5. View all details
python3 main.py view --all

# Expected: All addresses and categories shown
```

**Pass criteria**:
- ✅ All files created
- ✅ No errors or crashes
- ✅ Data persists between commands

#### 3.2 Incremental Processing Test (Existing Data)
**Purpose**: Verify processing multiple files doesn't duplicate

**Manual steps**:
```bash
# 1. Use existing storage from 3.1
# (storage/ and config.json should exist)

# 2. Process second file
python3 main.py process dummy-data/february.csv

# Expected:
# - Prompt for encryption key only
# - Known addresses auto-categorized (no prompt)
# - New addresses prompt for category

# 3. Verify totals updated
python3 main.py view
```

**Pass criteria**:
- ✅ Known addresses not re-prompted
- ✅ Totals accumulate correctly
- ✅ No duplicate entries in hash table

#### 3.3 Error Recovery Test (Interrupted Process)
**Purpose**: Verify graceful handling of interruptions

**Manual steps**:
```bash
# 1. Start processing
python3 main.py process dummy-data/january.csv

# 2. During categorization prompts, press Ctrl+C

# Expected:
# - Prompt: "Save progress so far? (y/n)"

# 3. Type "y" and confirm

# 4. Restart processing
python3 main.py process dummy-data/january.csv

# Expected:
# - Previously categorized addresses not re-prompted
# - Resume from interruption point
```

**Pass criteria**:
- ✅ Ctrl+C doesn't lose data
- ✅ Partial progress saved
- ✅ Can resume seamlessly

#### 3.4 Wrong Password Test (Security)
**Purpose**: Verify encryption protects data

**Manual steps**:
```bash
# 1. Process with password "correct123"
python3 main.py process dummy-data/january.csv
# Enter key: correct123

# 2. Try viewing with wrong password
python3 main.py view
# Enter key: wrong999

# Expected:
# - Error: "Invalid token" or decryption failure
# - Data NOT displayed
```

**Pass criteria**:
- ✅ Wrong password rejected
- ✅ No data leak

#### 3.5 Malicious CSV Test (Security)
**Purpose**: Verify SQL injection and path traversal blocked

**Manual steps**:
```bash
# 1. Create malicious CSV
echo 'date,address,amount' > /tmp/evil.csv
echo "2024-01-01,'; DROP TABLE users; --,100" >> /tmp/evil.csv
echo '2024-01-01,../../etc/passwd,50' >> /tmp/evil.csv

# 2. Process malicious CSV
python3 main.py process /tmp/evil.csv

# Expected:
# - Transaction with SQL injection SKIPPED
# - Warning message about "Suspicious content detected"
# - Path traversal sanitized

# 3. View results
python3 main.py view --all

# Expected:
# - Malicious addresses NOT in hash table
```

**Pass criteria**:
- ✅ SQL injection detected and blocked
- ✅ No crashes or data corruption

#### 3.6 Multi-Bank Format Test (Config)
**Purpose**: Verify column mapping saves per bank

**Manual steps**:
```bash
# 1. Create Bank A CSV (columns: Date, Merchant, Amount)
echo 'Date,Merchant,Amount' > /tmp/bank_a.csv
echo '2024-01-01,Store A,100' >> /tmp/bank_a.csv

# 2. Process Bank A
python3 main.py process /tmp/bank_a.csv
# Expected: Prompt to map columns
# Map: Date=Date, Address=Merchant, Amount=Amount

# 3. Create Bank B CSV (columns: Trans Date, Vendor, Total)
echo 'Trans Date,Vendor,Total' > /tmp/bank_b.csv
echo '2024-01-01,Store B,200' >> /tmp/bank_b.csv

# 4. Process Bank B
python3 main.py process /tmp/bank_b.csv
# Expected: Prompt to map different columns

# 5. Process Bank A again
python3 main.py process /tmp/bank_a.csv
# Expected: NO column mapping prompt (remembered)
```

**Pass criteria**:
- ✅ Each bank format saved separately
- ✅ Re-processing same format auto-loads mapping

---

## Testing Progress Tracker

Create `testing_progress.txt` to track completion:

```
=== F.U.C.K. Testing Progress ===

Phase 1: Unit Tests (Mock-Heavy)
[ ] 1.1 Crypto module tests
[ ] 1.2 Storage module tests
[ ] 1.3 CSV reading tests
[ ] 1.4 Category manager tests

Phase 2: Integration Tests
[ ] 2.1 Crypto + Storage integration
[ ] 2.2 CSV + Category Manager integration
[ ] 2.3 Full pipeline mock test

Phase 3: Manual End-to-End Tests
[ ] 3.1 First-time setup test
[ ] 3.2 Incremental processing test
[ ] 3.3 Error recovery test
[ ] 3.4 Wrong password test
[ ] 3.5 Malicious CSV test
[ ] 3.6 Multi-bank format test

Last updated: [DATE]
Completed by: [NAME]
```

---

## Test Execution Strategy

Following Anthropic's incremental approach:

### Session 1: Unit Tests (Crypto)
1. Write `tests/test_crypto.py`
2. Run tests: `python3 -m pytest tests/test_crypto.py -v`
3. Commit: "Add crypto module unit tests"
4. Update progress tracker

### Session 2: Unit Tests (Storage)
1. Write `tests/test_storage.py`
2. Run tests: `python3 -m pytest tests/test_storage.py -v`
3. Commit: "Add storage module unit tests"
4. Update progress tracker

### Session 3: Unit Tests (CSV + Category Manager)
1. Write `tests/test_read_data.py`
2. Write `tests/test_category_manager.py`
3. Run tests: `python3 -m pytest tests/ -v`
4. Commit: "Add CSV and category manager unit tests"
5. Update progress tracker

### Session 4: Integration Tests
1. Create `tests/test_integration.py` (replaces integration_test.py)
2. Implement 2.1, 2.2, 2.3
3. Run: `python3 -m pytest tests/test_integration.py -v`
4. Commit: "Add component integration tests"
5. Update progress tracker

### Session 5: Manual Testing Day
1. Follow 3.1 through 3.6 procedures
2. Document results in `manual_test_results.txt`
3. Log any bugs found
4. Commit: "Document manual test results"

---

## Success Criteria

✅ **Complete** when:
- All Phase 1 unit tests pass (green)
- All Phase 2 integration tests pass (green)
- All Phase 3 manual tests documented with pass/fail
- `testing_progress.txt` shows 100% completion
- All critical bugs fixed
- Code committed with clear messages

---

## Tools Required

- **Python unittest** (already used)
- **pytest** (optional, better reporting)
- **unittest.mock** (for mocking user input)
- **tempfile** (for temporary test files)
- **io.StringIO** (for in-memory CSV testing)

**Install**: `pip3 install pytest pytest-cov`

---

## Notes on KISS Principle

❌ **Avoid**:
- Complex test frameworks (Selenium, etc.)
- Over-mocking (mock only user input and external deps)
- Testing implementation details (test behavior, not internals)
- Flaky tests (use deterministic data)

✅ **Do**:
- Test one thing per test
- Use descriptive test names: `test_encrypt_decrypt_roundtrip`
- Keep test data minimal (3-5 transactions max)
- Manual tests for UX validation
- Document expected vs actual

---

## References

This testing plan follows methodologies from:
- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- KISS Principle: Simplicity in design and testing
- Git-based progress tracking for clarity

**Next step**: Begin Phase 1, Session 1 (Crypto unit tests)
