# F.U.C.K. Sanitation & Reworking Plan

## Executive Summary
This plan addresses critical code quality, architecture, and security issues in the Fund Utilization and Categorization Kit (F.U.C.K.) following KISS principles and effective harness methodology for maintainable software.

---

## Current State Analysis

### Codebase Overview
- **Total Lines of Code:** 462 lines
- **Main Components:**
  - `main.py` (8 lines) - Non-functional entry point
  - `read_data.py` (73 lines) - CSV processing
  - `category_manager.py` (153 lines) - Transaction categorization
  - `crypto_utils.py` (132 lines) - Encryption/hashing
  - `storage.py` (96 lines) - Data persistence

### Critical Issues Identified

#### 1. **CRITICAL BUGS** 🔴
- **Syntax Error:** Missing comma in category list (category_manager.py:24)
- **Logic Error:** Invalid index access in get_user_category() (line 39)
- **File Naming:** `__init.py__` instead of `__init__.py` breaks package imports
- **Weak Transaction IDs:** Only date+amount used (high collision risk)

#### 2. **Architecture Problems** 🟡
- No separation of concerns (UI/business logic/data access mixed)
- Global state passed everywhere (cipher_suite, SALT)
- No configuration management
- main.py doesn't serve any real purpose
- Duplicate functions (user_confirm_action appears twice)
- Relative imports inconsistency

#### 3. **Security Concerns** 🟠
- Transaction ID collision vulnerability
- No input validation on CSV data
- Environment variable handling could be improved
- No sanitization of file paths

#### 4. **Usability Issues** 🟢
- Manual column selection on every run (no saved configs)
- No error recovery mechanisms
- Poor user feedback
- No progress indicators for large CSV files

#### 5. **Code Quality** 🔵
- Inconsistent docstrings (some are copy-pasted incorrectly)
- Test functions exist but aren't executable
- No proper test suite
- Magic numbers and hardcoded paths
- No logging system

---

## Sanitation Plan (KISS Approach)

### Phase 1: Critical Fixes (DO FIRST)
**Goal:** Make the code actually work

1. **Fix Syntax Errors**
   - Add missing comma in categories list (category_manager.py:24)
   - Rename `__init.py__` → `__init__.py`

2. **Fix Logic Errors**
   - Fix get_user_category() line 39: `categories[user_input]` → proper handling
   - Improve transaction ID generation to include address hash

3. **Remove Dead Code**
   - Clean up main.py (currently useless)
   - Remove duplicate user_confirm_action function
   - Remove broken test functions

### Phase 2: Architecture Simplification (KISS)
**Goal:** Clear separation of concerns

1. **Create Simple Layer Structure**
   ```
   package/
   ├── __init__.py          (fixed name)
   ├── cli.py               (NEW - all user interaction)
   ├── core.py              (NEW - business logic only)
   ├── crypto.py            (RENAME crypto_utils.py)
   ├── storage.py           (KEEP - data layer)
   └── config.py            (NEW - configuration)
   ```

2. **State Management**
   - Create Config class to hold cipher_suite, SALT, categories
   - Pass single config object instead of multiple parameters
   - Initialize once, use everywhere

3. **Proper Entry Point**
   - Make main.py a real CLI with commands:
     - `process <csv_file>` - Process new CSV
     - `view` - View category totals
     - `export` - Export data
     - `config` - Configure column mappings

### Phase 3: Input Validation & Error Handling
**Goal:** Robustness without complexity

1. **CSV Validation**
   - Check file exists and is readable
   - Validate CSV format before processing
   - Handle malformed rows gracefully

2. **User Input Validation**
   - Validate column selections
   - Validate category choices
   - Validate file paths

3. **Error Recovery**
   - Save progress after each transaction
   - Allow resume on failure
   - Clear error messages (not stack traces)

### Phase 4: Security Hardening
**Goal:** Fix vulnerabilities simply

1. **Transaction ID Improvement**
   ```python
   # OLD: f"{date}-{amount}"
   # NEW: f"{date}-{address_hash[:8]}-{amount}"
   ```

2. **Input Sanitization**
   - Validate CSV content (check for injection attempts)
   - Sanitize file paths
   - Validate amount is numeric

3. **Better Secret Management**
   - Add .env file support
   - Validate key/salt format before use
   - Clear error if keys missing

### Phase 5: Usability Improvements
**Goal:** Better UX without bloat

1. **Save Column Mappings**
   - Detect CSV format automatically if possible
   - Save mapping per bank (by CSV structure)
   - Ask once, remember forever

2. **Progress Feedback**
   - Show progress for large CSV files
   - Summary at end (X transactions, Y new, Z duplicates)

3. **Better CLI**
   - Use argparse properly with subcommands
   - Add --help that's actually helpful
   - Add --dry-run mode

### Phase 6: Code Quality
**Goal:** Maintainability

1. **Consistent Style**
   - Fix docstrings (remove copy-paste errors)
   - Consistent type hints
   - Remove commented code

2. **Add Logging**
   - Simple logging to file (not print statements)
   - Debug mode for troubleshooting
   - Keep console clean

3. **Proper Tests**
   - Move test functions to tests/ directory
   - Make them actually runnable
   - Add pytest support

---

## Implementation Priority

### 🔴 CRITICAL (Do Immediately)
1. Fix syntax error (missing comma)
2. Fix __init__.py filename
3. Fix get_user_category() logic error
4. Fix transaction ID collision issue

### 🟡 HIGH (Next Sprint)
5. Restructure into clean layers (cli/core/storage)
6. Create Config class for state management
7. Add input validation
8. Fix main.py to be useful

### 🟠 MEDIUM (Soon)
9. Save column mappings
10. Add proper error handling
11. Improve security (better transaction IDs, input sanitization)
12. Add logging system

### 🟢 LOW (When Time Permits)
13. Progress indicators
14. Proper test suite
15. Documentation improvements
16. Data export features

---

## Success Criteria

### Must Have
- [ ] All syntax/logic errors fixed
- [ ] Code runs without crashes on valid CSV
- [ ] No duplicate code
- [ ] Clear separation: UI / Business Logic / Data
- [ ] Config saved and reusable
- [ ] Basic error handling

### Should Have
- [ ] Proper CLI with subcommands
- [ ] Input validation
- [ ] Logging instead of print
- [ ] Tests that actually run
- [ ] Security improvements

### Nice to Have
- [ ] Progress indicators
- [ ] Auto-detect CSV format
- [ ] Export functionality
- [ ] Visualization features

---

## Anti-Patterns to Avoid

### ❌ DON'T
- Over-engineer with complex abstractions
- Add unnecessary dependencies
- Create "future-proof" code for features that don't exist
- Use OOP when simple functions work
- Add features not in requirements

### ✅ DO
- Keep functions small and focused
- Use simple data structures (dicts, lists)
- Write obvious code over clever code
- Fix bugs before adding features
- Test as you go

---

## File-by-File Breakdown

### `package/category_manager.py` (153 lines)
**Issues:**
- Missing comma line 24
- Duplicate user_confirm_action (also in read_data.py)
- Invalid logic line 39
- find_category_by_address inefficient (O(n) decrypt loop)

**Actions:**
- Fix syntax and logic errors
- Remove duplicate function
- Extract UI code to cli.py
- Keep only business logic

### `package/crypto_utils.py` (132 lines)
**Issues:**
- Poor docstrings (copy-paste errors)
- initialize_crypto() does too much (UI + crypto)
- Non-functional test_crypto_functions()

**Actions:**
- Rename to crypto.py
- Split initialize_crypto into get_crypto_config() + init_cipher()
- Move user prompts to cli.py
- Fix docstrings

### `package/read_data.py` (73 lines)
**Issues:**
- Mixes CSV parsing, UI, and business logic
- Column selection UI every time
- Duplicate user_confirm_action
- No error handling for malformed CSV

**Actions:**
- Extract UI to cli.py
- Extract column selection to config.py
- Add CSV validation
- Simplify to just CSV reading

### `package/storage.py` (96 lines)
**Issues:**
- Hardcoded path
- get_categories_and_totals just prints (not very useful)
- Non-functional test function

**Actions:**
- Move path to config
- Improve get_categories_and_totals to return proper data
- Remove test function (move to tests/)

### `main.py` (8 lines)
**Issues:**
- Doesn't do anything useful
- No CLI interface
- Loads data but doesn't use it

**Actions:**
- Rewrite as proper CLI entry point
- Add subcommands (process, view, export, config)
- Make it the single entry point

---

## Estimated Effort

**Total Time:** ~8-12 hours for complete sanitation

- Phase 1 (Critical Fixes): 1 hour
- Phase 2 (Architecture): 3-4 hours
- Phase 3 (Validation): 2 hours
- Phase 4 (Security): 1-2 hours
- Phase 5 (Usability): 2 hours
- Phase 6 (Quality): 1-2 hours

---

## Post-Sanitation State

### Expected Outcome
```
package/
├── __init__.py          # Proper init
├── cli.py               # All user interaction
├── core.py              # Pure business logic
├── crypto.py            # Crypto utilities
├── storage.py           # Data persistence
└── config.py            # Configuration management

main.py                  # CLI entry point
tests/                   # Actual runnable tests
  ├── test_core.py
  ├── test_crypto.py
  └── test_storage.py
config.json              # Saved column mappings
.env.example             # Example environment vars
```

### Code Metrics (Target)
- Total LOC: ~500-600 (slight increase for proper structure)
- Average function length: <20 lines
- Test coverage: >60%
- No code duplication
- Zero syntax/logic errors

---

## Next Steps

1. **Review & Approve** this plan
2. **Create feature branch** for sanitation work
3. **Execute Phase 1** (critical fixes)
4. **Test** after each phase
5. **Commit** with clear messages
6. **Review** before merging

---

## Notes

- This is a **sanitation** plan, not a feature addition plan
- Focus is on making existing code work properly and maintainable
- KISS principle: simpler is better
- No unnecessary abstractions or premature optimization
- Each phase should leave code in working state
