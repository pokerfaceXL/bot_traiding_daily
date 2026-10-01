"""
F006 -- H-BETA-GATE-01: rolling beta / correlation gate on a frozen Donchian-20 alt continuation
trigger. Tests the hypothesis in spec/research/F006-hypothesis-beta-gate.md.

Calls scripts/f006_family_runner.py's run_family() once. Does not copy or edit the shared harness
loop, the contract tests, or the digest script -- per F006-shared-harness.md's own instruction.

Registers beta_gate.catalog_entries() (BETA_GATE_DONCH20, BETA_GATE_MR_DONCH20) into
strategy.STRATEGY_CATALOG for this process only; strategy.py is never edited.

Writes only output/f006_beta_gate/. Zero network connections.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import beta_gate
from scripts import f006_family_runner as fam

CANDIDATE_NAMES = ["BETA_GATE_DONCH20", "BETA_GATE_MR_DONCH20"]


def _bar_level_containment_check() -> dict:
    """This note's own extra check (spec/research/F006-hypothesis-beta-gate.md's Method
    section): every bar where a gated signal is nonzero, the raw DONCHIAN_20 trigger at that
    same bar is nonzero and in the same direction. Checked directly on the raw signal series,
    not on trade counts -- a gate reopening mid-run is itself a legitimate new one-shot call
    under entry_masks.one_shot_entry_mask's own semantics, so n_trades is not bounded by the raw
    trigger's own n_trades (an earlier draft of this check wrongly assumed that bound; see the
    hypothesis note's Method section for the correction).
    """
    import entry_masks

    violations = []
    for symbol in fam.SYMBOLS:
        for interval in fam.INTERVALS:
            train1_df, _m = fam.load_train1(symbol, interval)
            raw_trigger = entry_masks.strategy_signal_series(train1_df, "DONCHIAN_20", interval=interval, now=fam.NOW)
            btc_close = beta_gate.load_btc_close(interval)
            trend = beta_gate.gated_trend_signal(train1_df, btc_close)
            mr = beta_gate.gated_mr_signal(train1_df, btc_close)
            # trend arm only permits the raw trigger's own direction; MR arm only fades it
            # (opposite direction), and both require the raw trigger to be active on that bar.
            bad_trend = trend[(trend != 0) & (trend != raw_trigger)]
            bad_mr = mr[(mr != 0) & (mr != -raw_trigger)]
            for name, bad in (("BETA_GATE_DONCH20", bad_trend), ("BETA_GATE_MR_DONCH20", bad_mr)):
                if len(bad):
                    violations.append({"symbol": symbol, "interval": interval, "strategy": name,
                                       "n_bad_bars": int(len(bad))})
    return {"violations": violations}


def main():
    manifest = fam.run_family(
        "beta_gate",
        CANDIDATE_NAMES,
        catalog_entries=beta_gate.catalog_entries(),
        hypothesis_note="spec/research/F006-hypothesis-beta-gate.md",
        script_path="scripts/f006_beta_gate_experiment.py",
    )

    containment_check = _bar_level_containment_check()
    if containment_check["violations"]:
        raise SystemExit(f"STOP: gate fired on a bar the raw DONCHIAN_20 trigger did not license -- "
                          f"{containment_check['violations']}")

    manifest["bar_level_containment_check"] = containment_check
    with open("output/f006_beta_gate/summary/manifest.json", "w") as f:
        import json
        json.dump(manifest, f, indent=2)

    print(f"H1 table: {manifest['h1_table']}")
    print(f"H1 falsified: {manifest['h1_falsified']}")
    print(f"H2 status: {manifest['h2_status']}")
    print(f"bar-level containment violations: {len(containment_check['violations'])}")


if __name__ == "__main__":
    main()
