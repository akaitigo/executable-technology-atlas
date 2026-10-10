---
name: atlas-relational-database-sql
description: Reproduce or explain this module's bounded SQLite lesson for SQL NULL, three-valued logic, JOIN row retention, and basic constraint rejection. Use for this lesson's evidence and UI; do not route PostgreSQL, other SQL dialects, planner analysis, or full database coverage here.
---

# Relational Database SQL lesson

Use the existing module two directories above this skill. Read `../../README.md` and `../../COVERAGE.md` before answering.

- For evidence questions, inspect `../../evidence/raw-results.json`, `../../evidence/run.json`, and `../../sources.json`. Keep raw SQLite observations distinct from the explanatory browser model.
- To reproduce the requested lesson, run `python3 ../../observe.py` and then `python3 ../../verify.py` from this skill directory. Regeneration is a module-local write; do it only when the request calls for a fresh run.
- For a visual walkthrough, serve or open `../../index.html`; it reads `../../evidence/data.js` and does not execute SQL in the browser.
- State the recorded Python and SQLite versions. Never describe this evidence as PostgreSQL or cross-dialect execution.
- For SQL features, engines, planner behavior, concurrency, migration, backup, or operations outside `../../COVERAGE.md`'s observed rows, answer that the request is unlearned by this module and identify the missing runtime or artifact. Do not infer completion from this one lesson.

Reuse the module's existing runner, checker, evidence, and UI. Do not add a parallel harness or install this skill globally.
