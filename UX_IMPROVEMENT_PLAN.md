# F.U.C.K. UX Improvement Plan

Following [Anthropic's effective harness methodology](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) for systematic UX enhancements.

**Created:** 2025-12-13
**Branch:** `claude/plan-ux-improvements-01MqAaCghEdYJojN4QS4JWpr`
**Philosophy:** Incremental, testable, trackable improvements

---

## Executive Summary

This plan addresses quality-of-life improvements for F.U.C.K. users through **8 focused improvement sessions**, each delivering tangible value while maintaining the project's KISS principle. The plan prioritizes high-impact, low-complexity enhancements that reduce friction and improve daily usage.

---

## Current UX Baseline

### ✅ Strengths
- Simple CLI with 4 clear commands
- Smart memory (column mappings, categorization)
- Progress indicators for long operations
- Graceful error recovery (Ctrl+C handling)
- Secure input handling (hidden passwords)
- Clear error messages

### ❌ Pain Points Identified

| Category | Issue | User Impact |
|----------|-------|-------------|
| **Visibility** | No transaction review before save | Can't verify categorization accuracy |
| **Editing** | No way to fix categorization mistakes | Manual database editing required |
| **Reporting** | Only basic totals, no trends | Limited financial insights |
| **Discovery** | No search/filter for transactions | Can't find specific purchases |
| **Export** | No data export capability | Can't analyze in Excel/other tools |
| **Validation** | Silent transaction skips | Unclear why data was rejected |
| **Efficiency** | No bulk operations | Must recategorize transactions one-by-one |
| **Learning** | Limited help/documentation | New users struggle with first setup |

---

## UX Improvement Roadmap

### Priority Framework

Following Anthropic's methodology, improvements are prioritized by:
1. **Impact:** How much does this improve daily usage?
2. **Complexity:** Can this be implemented in one session?
3. **Risk:** Does this break existing functionality?
4. **Testability:** Can we validate this works?

**Priority tiers:**
- **P0 (Critical):** Blocks common workflows, high frustration
- **P1 (High):** Significant friction reduction
- **P2 (Medium):** Nice-to-have, quality of life
- **P3 (Low):** Future enhancements

---

## Session-Based Implementation Plan

### Session 1: Transaction Review & Confirmation [P0]
**Impact:** High | **Complexity:** Low | **Duration:** 1-2 hours

**Problem:** Users can't review categorizations before saving, leading to mistakes that require manual database editing.

**Solution:** Add pre-save review step showing all categorized transactions.

**Deliverables:**
1. New command: `process --review` flag (default: on)
2. Review screen showing:
   - Transaction summary table (date, amount, category)
   - Totals by category
   - Option to edit/confirm/cancel
3. Unit tests for review workflow
4. Manual test: Process CSV, review, confirm

**Files to modify:**
- `main.py`: Add `--review` flag to process command
- `cli.py`: Add `display_review()` and `confirm_processing()` functions
- `tests/test_cli.py`: Add review workflow tests

**Acceptance criteria:**
- ✅ User sees all transactions before save
- ✅ Can cancel without saving
- ✅ Can return to categorization to fix mistakes
- ✅ Review is skippable with `--no-review` flag

**Git commit:** "feat: Add transaction review before saving"

---

### Session 2: Fix Categorization Mistakes [P0]
**Impact:** High | **Complexity:** Medium | **Duration:** 2-3 hours

**Problem:** Once categorized, there's no way to fix mistakes without manual database editing.

**Solution:** Add `edit` command to recategorize transactions.

**Deliverables:**
1. New command: `edit [--category CATEGORY] [--address ADDRESS]`
2. Interactive search: "Which transaction to recategorize?"
3. Show current category, prompt for new category
4. Update hash table and totals
5. Unit tests for edit operations
6. Integration test for edit workflow

**Files to create/modify:**
- `main.py`: Add `cmd_edit()` handler
- `package/category_manager.py`: Add `recategorize_address()`
- `cli.py`: Add `select_transaction_to_edit()` function
- `tests/test_category_manager.py`: Add recategorization tests

**Acceptance criteria:**
- ✅ Can search for transactions by address substring
- ✅ Can recategorize specific address
- ✅ Totals update correctly (decrement old, increment new)
- ✅ Handles edge cases (address not found, invalid category)

**Git commit:** "feat: Add edit command for fixing categorization mistakes"

---

### Session 3: Enhanced View with Filters [P1]
**Impact:** High | **Complexity:** Low | **Duration:** 1-2 hours

**Problem:** Can only view "all" or "totals", no way to filter by category, date range, or amount.

**Solution:** Add filtering options to `view` command.

**Deliverables:**
1. New flags: `--category CATEGORY`, `--month YYYY-MM`, `--min-amount X`, `--max-amount Y`
2. Filtered transaction display
3. Filtered totals calculation
4. Unit tests for filtering logic
5. Manual test: View with various filters

**Files to modify:**
- `main.py`: Add filter arguments to `view_parser`
- `package/storage.py`: Add `filter_transactions()` function
- `cli.py`: Add `format_filtered_results()` function
- `tests/test_storage.py`: Add filter tests

**Acceptance criteria:**
- ✅ Can view single category (e.g., `view --category "Groceries/Food"`)
- ✅ Can view by month (e.g., `view --month 2024-01`)
- ✅ Can combine filters (e.g., `view --category Utilities --month 2024-01`)
- ✅ Shows filtered totals accurately

**Git commit:** "feat: Add filtering options to view command"

---

### Session 4: Data Export Capability [P1]
**Impact:** High | **Complexity:** Low | **Duration:** 1-2 hours

**Problem:** No way to export data for analysis in Excel, Google Sheets, or custom scripts.

**Solution:** Add `export` command with multiple format support.

**Deliverables:**
1. New command: `export [--format csv|json|txt] [--output FILE]`
2. Export formats:
   - CSV: `date,address,category,amount`
   - JSON: Structured transaction array
   - TXT: Human-readable report
3. Support filters from Session 3
4. Unit tests for export formats
5. Manual test: Export, open in Excel

**Files to create/modify:**
- `main.py`: Add `cmd_export()` handler
- `package/export.py`: New module with export functions
- `tests/test_export.py`: New test file
- `cli.py`: Add export progress indicators

**Acceptance criteria:**
- ✅ CSV export opens correctly in Excel
- ✅ JSON export is valid JSON
- ✅ Respects filters (e.g., `export --category Groceries --format csv`)
- ✅ Handles decryption correctly (addresses shown as original)

**Git commit:** "feat: Add data export with CSV, JSON, TXT formats"

---

### Session 5: Better Error Reporting [P1]
**Impact:** Medium | **Complexity:** Low | **Duration:** 1 hour

**Problem:** Transactions fail silently with generic "skipped" messages, unclear why.

**Solution:** Add detailed validation reporting with actionable messages.

**Deliverables:**
1. Verbose error messages: "Skipped: Invalid amount on line 42"
2. Summary table at end:
   - Validation errors by type
   - Affected line numbers
   - Suggestions for fixing
3. Optional `--strict` mode: Fail on any error
4. Unit tests for error reporting
5. Manual test: Process CSV with errors

**Files to modify:**
- `package/core.py`: Add `ValidationError` exception with details
- `package/read_data.py`: Track line numbers and error types
- `cli.py`: Add `print_validation_summary()` function
- `main.py`: Add `--strict` flag

**Acceptance criteria:**
- ✅ Each skipped transaction shows specific reason
- ✅ Line numbers provided for easy CSV debugging
- ✅ Summary table groups errors by type
- ✅ `--strict` mode exits on first error

**Git commit:** "feat: Add detailed validation error reporting"

---

### Session 6: Spending Insights & Reports [P2]
**Impact:** Medium | **Complexity:** Medium | **Duration:** 2-3 hours

**Problem:** Only raw totals shown, no trends, comparisons, or insights.

**Solution:** Add `report` command with spending analysis.

**Deliverables:**
1. New command: `report [--type monthly|category|trends]`
2. Report types:
   - **Monthly:** Compare spending month-over-month
   - **Category:** Top categories with percentages
   - **Trends:** Identify unusual spending (>20% deviation)
3. ASCII bar charts for visualization
4. Unit tests for report calculations
5. Manual test: Generate reports, verify accuracy

**Files to create/modify:**
- `main.py`: Add `cmd_report()` handler
- `package/reports.py`: New module with analysis functions
- `package/visualization.py`: ASCII chart helpers
- `tests/test_reports.py`: New test file

**Acceptance criteria:**
- ✅ Monthly report shows month-over-month changes
- ✅ Category report shows top 10 with percentages
- ✅ Trends report flags unusual spending
- ✅ Charts render correctly in terminal (80-char width)

**Git commit:** "feat: Add spending insights and reports"

---

### Session 7: Bulk Operations [P2]
**Impact:** Medium | **Complexity:** Medium | **Duration:** 2 hours

**Problem:** Must recategorize transactions one by one, no batch operations.

**Solution:** Add bulk recategorization by address pattern.

**Deliverables:**
1. New command: `bulk-edit --pattern PATTERN --category CATEGORY`
2. Pattern matching (substring or regex)
3. Preview before applying: "This will affect N transactions"
4. Confirmation prompt with dry-run option
5. Unit tests for pattern matching
6. Integration test for bulk operations

**Files to create/modify:**
- `main.py`: Add `cmd_bulk_edit()` handler
- `package/category_manager.py`: Add `bulk_recategorize()`
- `cli.py`: Add `preview_bulk_changes()` function
- `tests/test_category_manager.py`: Add bulk operation tests

**Acceptance criteria:**
- ✅ Can match multiple addresses with substring (e.g., "Walmart*")
- ✅ Preview shows all affected transactions
- ✅ Dry-run mode doesn't modify data
- ✅ Confirmation required before applying

**Git commit:** "feat: Add bulk recategorization operations"

---

### Session 8: Interactive Help & Onboarding [P2]
**Impact:** Low | **Complexity:** Low | **Duration:** 1 hour

**Problem:** New users struggle with first-time setup, limited guidance.

**Solution:** Add interactive help and setup wizard.

**Deliverables:**
1. New command: `help [TOPIC]`
2. Topics: `setup`, `categories`, `csv-format`, `security`
3. First-run wizard: `init` command
   - Walks through CSV format selection
   - Suggests category structure
   - Explains security best practices
4. Enhanced `--help` with examples
5. Manual test: New user onboarding

**Files to create/modify:**
- `main.py`: Add `cmd_help()` and `cmd_init()` handlers
- `package/help.py`: New module with help content
- `cli.py`: Add `run_setup_wizard()` function
- `README.md`: Update with help command examples

**Acceptance criteria:**
- ✅ `help setup` shows first-time setup instructions
- ✅ `init` wizard guides new users step-by-step
- ✅ Each command has `--help` with real examples
- ✅ Help topics cover common questions

**Git commit:** "feat: Add interactive help and setup wizard"

---

## Testing Strategy (Anthropic Methodology)

### Per-Session Testing
Each session follows this testing pattern:

1. **Unit tests first:** Write tests before implementation
2. **Integration tests:** Verify component interactions
3. **Manual testing:** Validate real user workflows
4. **Regression tests:** Ensure existing features still work

### Test Coverage Goals
- New code: 80% coverage minimum
- Critical paths: 100% coverage (categorization, encryption, storage)
- CLI interactions: Manual test procedures documented

### Continuous Validation
```bash
# Run after each session
python3 -m pytest tests/ -v --cov=package --cov-report=term-missing

# Manual smoke test
python3 main.py process dummy-data/january.csv
python3 main.py view
python3 main.py view --all
```

---

## Progress Tracking (Git-Based)

Following Anthropic's approach, each session creates clear artifacts:

### Session Artifacts
1. **Code changes:** Committed with descriptive messages
2. **Tests:** New test files or additions
3. **Documentation:** Updated README/help content
4. **Progress file:** This document updated with ✅ checkmarks

### Git Workflow
```bash
# Start session
git checkout -b claude/ux-session-N
git commit -m "feat: [SESSION DELIVERABLE]"

# End session (update progress)
echo "Session N: ✅ Complete" >> ux_progress.txt
git add ux_progress.txt
git commit -m "docs: Mark session N complete"
git push -u origin claude/ux-session-N
```

### Progress Checkpoints

- [ ] **Session 1:** Transaction review & confirmation
- [ ] **Session 2:** Fix categorization mistakes
- [ ] **Session 3:** Enhanced view with filters
- [ ] **Session 4:** Data export capability
- [ ] **Session 5:** Better error reporting
- [ ] **Session 6:** Spending insights & reports
- [ ] **Session 7:** Bulk operations
- [ ] **Session 8:** Interactive help & onboarding

**Completion:** 0/8 sessions (0%)

---

## Risk Mitigation

### Backwards Compatibility
- All new features are **opt-in** (flags, new commands)
- Existing `process`, `view`, `config` commands unchanged
- Hash table format remains compatible
- No breaking changes to core functionality

### Data Safety
- No modifications to encryption/storage layer
- All edits require confirmation
- Dry-run modes for bulk operations
- Automatic backups before destructive changes

### User Experience
- Progressive enhancement (advanced features don't clutter basic usage)
- Clear help text for all new features
- Graceful degradation (missing data doesn't crash)

---

## Success Metrics

### Quantitative
- ✅ All 8 sessions completed
- ✅ Test coverage >80% on new code
- ✅ Zero regressions in existing tests
- ✅ All manual test procedures pass

### Qualitative
- ✅ Users can fix mistakes without database editing
- ✅ Users can export data for external analysis
- ✅ Users can generate spending reports
- ✅ New users complete setup without external help

---

## Implementation Order Rationale

**Why this order?**

1. **Session 1-2 (Review & Edit):** Highest user pain, unblocks critical workflows
2. **Session 3-4 (Filters & Export):** Builds on existing `view`, enables analysis
3. **Session 5 (Error Reporting):** Improves data quality visibility
4. **Session 6-7 (Insights & Bulk):** Advanced features, higher complexity
5. **Session 8 (Help):** Polish, onboarding for new users

**Dependencies:**
- Session 3 filters are used by Session 4 export
- Session 2 edit uses same UI patterns as Session 7 bulk-edit
- Session 6 reports need Session 3 filtering logic

---

## Future Enhancements (Post-Plan)

These are **not in scope** but identified for future consideration:

- 🔮 **Web UI:** Browser-based interface for non-CLI users
- 🔮 **Budget tracking:** Set monthly budgets with alerts
- 🔮 **Recurring transactions:** Auto-categorize subscriptions
- 🔮 **Multi-currency support:** Handle foreign transactions
- 🔮 **Import from Mint/YNAB:** Migrate from other tools
- 🔮 **Machine learning categorization:** AI-suggested categories
- 🔮 **Mobile app:** iOS/Android companion
- 🔮 **Cloud sync:** Encrypted cloud backup (optional)

---

## References

- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [KISS Principle](https://en.wikipedia.org/wiki/KISS_principle)
- [Semantic Versioning](https://semver.org/) for release planning
- [Git-based Progress Tracking](https://git-scm.com/book/en/v2/Git-Basics-Tagging)

---

## Next Steps

1. **Review this plan:** Confirm priorities align with user needs
2. **Start Session 1:** Transaction review & confirmation
3. **Update progress:** Check off completed sessions
4. **Iterate:** Adjust plan based on learnings

**Ready to begin?** Start with Session 1.

---

**Last updated:** 2025-12-13
**Author:** Claude (Anthropic)
**Branch:** `claude/plan-ux-improvements-01MqAaCghEdYJojN4QS4JWpr`
