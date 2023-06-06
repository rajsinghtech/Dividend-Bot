import json
import requests

url = "https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/JEPI?apikey="
r = requests.get(url=url)
data = r.json()
print(json.dumps(data["historical"][0], indent=4))