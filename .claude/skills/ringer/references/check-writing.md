## Check-writing rules

The check is the product. The retry prompt and the eval log both depend on
the check's failure output.

- **Checks must print WHY they fail.** `diff` beats `diff -q`; a validator
  script that prints which assertion broke beats `test -f`. A bare
  `test -f report.md` proves existence, not correctness.
- **Verify content, not existence.** Grep the artifact for required sections,
  run the code it produced, run the build, run the validator — execute
  something that would catch a lazy or hallucinated result.
- **`expect_files` is a floor, not the check.** List deliverables there for
  fast triage, but the check must still validate them.
- **Never `true`, `exit 0`, or `echo done`.** A check that cannot fail is a
  task that cannot be verified — that's just trusting the worker with extra
  steps.
- **Strict on substance, tolerant on format.** Checks that count exact
  headings, demand exact casing, or grep rigid phrasings fail honest work
  over formatting — and a wall of red format-failures reads as a broken
  system, not a careful one (demo-night lesson). Verify what must be TRUE
  (the file proves X, the code runs, the quote exists in the source), use
  case-insensitive and flexible matching for structure, and reserve hard
  failure for substance: missing evidence, fabricated content, code that
  doesn't run.
