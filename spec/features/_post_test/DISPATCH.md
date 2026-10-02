# Post-test dispatch runbook (COORDINATOR_RESEARCH_PROTOCOL §16)

> Repeatable process. After a T0 experiment produces `output/<OUTPUT_DIR>/{results,monthly,trades}.csv`,
> the coordinator does NOT compute anything by hand. Copy each template below into
> `spec/features/active/<EXPERIMENT_ID>-<Tn>/ticket.md`, substitute the four placeholders, commit
> the tickets to the branch the worker will read, then `limen spawn` with the model in the table.
> Nothing here needs re-deriving — only the placeholder values change per experiment.

## Placeholders (fill once, reuse in every ticket)

| placeholder | meaning | example |
| --- | --- | --- |
| `{{EXPERIMENT_ID}}` | pre-registered hypothesis id | `H-CATALOG5-BREADTH-REGIME-01` |
| `{{OUTPUT_DIR}}` | output subdir with results/monthly/trades csv | `f006_breadth_regime` |
| `{{PROFILE}}` | strategy profile file | `spec/research/strategy_profiles/EMA3_21_50_200.md` |
| `{{BASELINE}}` | baseline label for comparison | `EMA3_21_50_200 NO_TRAIL both-dir Train-1` |

## Order (max 2 workers at a time — §16.2)

1. `T1-metrics` + `T2-monthly`  (parallel, both read only the csv)
2. `T3-registry` + `T4-profile` (parallel, both read T1/T2 outputs)
3. `T5-digest`

## Spawn commands (copy-paste, swap `<...>`)

```bash
# before each wave: limen jobs --running   (must be < 2)
limen spawn "Do the post-test metrics task exactly per the ticket. Ticket: spec/features/active/<EXPERIMENT_ID>-T1-metrics/ticket.md" \
  --label <EXPERIMENT_ID>-t1 --provider openai-codex --model gpt-5.3-codex-spark
limen spawn "Do the post-test monthly task exactly per the ticket. Ticket: spec/features/active/<EXPERIMENT_ID>-T2-monthly/ticket.md" \
  --label <EXPERIMENT_ID>-t2 --provider openai-codex --model gpt-5.3-codex-spark
# wave 2
limen spawn "Fill the decision-registry skeleton per the ticket; leave decision/reason/next_action blank. Ticket: spec/features/active/<EXPERIMENT_ID>-T3-registry/ticket.md" \
  --label <EXPERIMENT_ID>-t3 --provider openai-codex --model gpt-5.3-codex-spark
limen spawn "Update the profile rows per the ticket; leave the status line blank. Ticket: spec/features/active/<EXPERIMENT_ID>-T4-profile/ticket.md" \
  --label <EXPERIMENT_ID>-t4 --provider openai-codex --model gpt-5.3-codex-spark
# wave 3
limen spawn "Regenerate the cross-family digest per the ticket. Ticket: spec/features/active/<EXPERIMENT_ID>-T5-digest/ticket.md" \
  --label <EXPERIMENT_ID>-t5 --provider openai-codex --model gpt-5.3-codex-spark
```

Use `gpt-5.6-sol` instead of `gpt-5.3-codex-spark` only if a task proves too subtle for spark
(e.g. causal feature handling). The T0 experiment-run ticket is separate and normally `gpt-5.6-sol`.

## Reserved for the coordinator (NEVER a worker — §16.4)

- the `decision` value in the §14 registry, and `reason` / `next_action`;
- the §15 end-of-series report;
- the next hypothesis; whether a falsifier tripped; the profile `status:` line.
