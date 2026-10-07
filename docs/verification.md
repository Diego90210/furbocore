# Verification — How to Demonstrate That the Work Works

> Golden rule: **the agent does not say "it works"; it demonstrates it**.
>
> Every feature must end with executable evidence, not assertions.

## Verification Levels

### Level 1 — Unit Tests (mandatory)

Every public function in `src/` must have at least one test in `tests/` that:

1. Covers the happy path.
2. Covers at least one error path if the function can fail.

Command:

```bash
python -m unittest discover -s tests -v
```

### Level 2 — Build + Lint (mandatory for frontend features)

Any change to `app/`, `components/`, or `lib/` must pass both gates:

```bash
npm run lint
npm run build
```

Both must exit 0. A TypeScript error or lint warning fails the verification.

### Level 3 — Pipeline Smoke Test (mandatory for data/ML features)

Run the actual pipeline script end-to-end against Supabase (read-only check is acceptable if writes are gated):

```bash
PYTHONPATH=. python src/models/transfer_value/run_pipeline.py
```

Then verify the output in the database:

```sql
SELECT count(*), min(predicted_value_eur), max(predicted_value_eur)
FROM transfer_values
WHERE predicted_value_eur IS NOT NULL;
```

Predictions must vary (not a single constant value).

### Level 4 — Manual Smoke Test (optional but recommended)

Before closing the session, start the dev server and click through the affected route:

```bash
npm run dev
# Visit /transfers, /matches, /scouting — confirm no console errors
```

## Anti-Patterns (Do Not Do)

* ❌ "I added the endpoint, it should work." → executable test or build output is missing.
* ❌ A test that only verifies that the function does not raise an exception. → it must check the concrete result.
* ❌ Mocking the Supabase client for integration tests. → use a real read query against the test data or assert on the SQL logic.
* ❌ Marking the feature as `done` without passing `./init.sh` or the indicated test file.
* ❌ Claiming a prediction model works without showing that predictions vary across rows.

## Final Verification Before Closing

```bash
./init.sh    # must finish with [OK] — lints, builds, runs tests
```

If `./init.sh` fails, **do not** mark anything as `done`. Record the blocker in `progress/current.md` and set `"status": "blocked"` in `feature_list.json`.
