import os
import json
import loghandler

log_handler = loghandler.LogHandler()

import requests

resp = requests.get(
    "https://api.coinmetrics.io/v4/timeseries/asset-metrics?assets=btc&metrics=PriceUSD,FlowInGEMUSD&frequency=1b&pretty=true"
)
print(resp.json())

print()

# print(json.loads(resp))