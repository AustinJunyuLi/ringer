## Post-run review ritual

1. Read the run JSON in `~/.ringer/runs/` — statuses, retries, durations.
2. For any retried or failed task, read the raw worker log in
   `<workdir>/logs/` before deciding anything. Retries that passed on
   attempt 2 often reveal a spec ambiguity worth fixing in your next
   manifest.
3. Spot-check at least one PASSING task's artifact per run. The check
   catches most laziness; you catch the rest.
4. Failures with useless error messages mean your CHECK needs work, not
   (only) the worker.
5. **Update `docs/MODEL-NOTES.md`** (in the ringer repo) when a run taught
   you something about a model: one dated line under the model — task type,
   what happened (attempts, tokens, failure mode), what you'd do
   differently. Only what the executed checks and raw logs support. The raw
   numbers took care of themselves — every attempt already landed in the
   local model log (`./ringer.py models` to see the updated scoreboard).
