import time
import sys
import yaml


config_path = sys.argv[1] if len(sys.argv) > 1 else "configuration/default.yaml"
with open(config_path, "r") as file:
    config = yaml.safe_load(file)    

SYMBOL = config.get("SYMBOL", "BTCUSDT")
INTERVAL = config.get("INTERVAL", "15")

bot_name = f"{SYMBOL}_{INTERVAL}"
bot_id = int(time.time())  # UNIX timestamp w sekundach