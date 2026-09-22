import sys

# strategy.py reads sys.argv[1] as a config path at IMPORT time (module-level
# open()), so any pytest invocation with a positional path arg (e.g. `pytest
# tests/`) makes it try to open that path as YAML and crash. Neutralize argv
# before collection imports strategy.py (directly, or via backtest_engine.py)
# — this is test infrastructure, not a change to strategy.py itself.
sys.argv = sys.argv[:1]
