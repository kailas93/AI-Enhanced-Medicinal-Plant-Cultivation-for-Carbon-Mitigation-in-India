import json

input_file = "nitm_plants_all.jsonl"
output_file = "plant_disease_support.json"

records = []
toxic_keywords = ["toxic", "poison", "fatal"]

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        plant = json.loads(line)

        plant_name = plant.get("plant_name")
        family = plant.get("family", "")
        pharmacology = plant.get("pharmacology", "").lower()

        # crude toxicity detection
        toxicity = any(word in pharmacology for word in toxic_keywords)

        uses = plant.get("uses", [])
        for u in uses:
            disease = u.get("disease")
            part_used = u.get("part_used", "Unknown")

            if disease:
                records.append({
                    "disease": disease.strip().title(),
                    "plant_name": plant_name,
                    "plant_part": part_used,
                    "family": family,
                    "toxicity": toxicity
                })

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2)

print(f"✅ Created {output_file} with {len(records)} entries")
