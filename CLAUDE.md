# F.U.C.K. — Finances Under Control Kit

Working agreements for this repo. Where these conflict with the vendored
skills in `.claude/skills/`, this file wins.

## Hard constraints

- **Runtime is stdlib-only, Python >= 3.10.** pytest is the only dev
  tool. Any new dependency (runtime or dev) needs the owner's explicit
  OK first.
- **Never commit real financial data.** Test data is synthetic, always.
  `exports/`, `snapshot.json`, `journal.md` are gitignored on purpose.
- **Lean is the house style** (README Principle 4): every added line is
  a liability. No speculative features, no unrequested tooling.

## Workflow

- **TDD for all production code**
  (`.claude/skills/test-driven-development`): failing test first,
  minimal implementation, green, commit. Configuration files are exempt.
- Run tests: `python -m pytest` (config in `pyproject.toml`).
- Specs go to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`,
  plans to `docs/superpowers/plans/YYYY-MM-DD-<feature>.md`.
- The backlog lives in GitHub Issues — check open issues when
  cold-starting a session. Specs and plans stay in-repo as above.
- Code review before merging to `main`.
- Never claim tests pass without a fresh run in the same message.

## Git: fast-forward commit principles

- Small, atomic commits; each commit leaves the tree green.
- **History stays linear.** Rebase local work onto latest `main` before
  integrating; integrate fast-forward (`git merge --ff-only`) or squash.
  No merge commits.
- `git pull --rebase`, never a plain pull on a diverged branch.
- Never force-push a shared branch without the owner's explicit request.
- Conventional Commits (`feat:` `fix:` `docs:` `ci:` `chore:`, `!` for
  breaking changes), imperative subject, body explains why. Every
  Claude-authored commit carries its Co-Authored-By and Claude-Session
  trailers.

## CI

`.github/workflows/ci.yml` runs pytest plus the demo smoke on Python
3.10 and 3.13, Ubuntu only — the repo name's trailing dot is an illegal
Windows path, so Windows runners cannot check this repo out. Keep CI
green; a red run on your branch is yours to fix.
