import requests
from bs4 import BeautifulSoup
import json

URL = "https://bsi.gov.in/page/en/medicinal-plant-database"

response = requests.get(URL)
soup = BeautifulSoup(response.text, "html.parser")

plants = []

rows = soup.select("table tr")

for tr in rows[1:]:  # skip header
    cols = tr.find_all("td")
    if len(cols) >= 4:
        plant_name = cols[1].text.strip()
        family = cols[2].text.strip()
        common_name = cols[3].text.strip()

        plants.append({
            "plant_name": plant_name,
            "family": family,
            "common_name": common_name
        })

with open("bsi_medicinal_plants.json", "w", encoding="utf-8") as f:
    json.dump(plants, f, indent=4, ensure_ascii=False)

print("Saved → bsi_medicinal_plants.json")

