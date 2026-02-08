import json
import itertools
import random

instructions = []

# Load datasets
with open("plant_ai_dataset_v2_native_state.json") as f:
    native_data = json.load(f)

with open("bsi_medicinal_plants_with_wikipedia.json") as f:
    wiki_data = {p["plant_name"]: p for p in json.load(f)}

nitm = []
with open("nitm_plants_all.jsonl") as f:
    for line in f:
        nitm.append(json.loads(line))
nitm_map = {p["plant_name"]: p for p in nitm}

# Templates
ecology_templates = [
    "Explain the ecological importance of {name}.",
    "Why is {name} important for biodiversity?",
    "How does {name} interact with local ecosystems?"
]

native_templates = [
    "Is {name} native or exotic and why does it matter?",
    "Explain native vs exotic aspects of {name}."
]

safety_templates = [
    "Is {name} safe for home use?",
    "What precautions are needed when using {name}?",
    "Can {name} be grown around children and pets?"
]

med_templates = [
    "How is {name} traditionally used for {disease}?",
    "Explain the traditional medicinal use of {name} for {disease}.",
    "Which part of {name} is used for {disease} and why?"
]

prep_templates = [
    "Explain the traditional preparation of {name}.",
    "How is {name} prepared in traditional medicine?"
]

chat_templates = [
    "A user asks: Can you tell me about {name}?",
    "User question: Is {name} good for health?",
    "Beginner question: What is {name} used for?"
]

for plant in native_data:
    name = plant["plant_name"]
    origin = plant["origin_type"]
    carbon = plant.get("carbon_score", 0)
    risk = plant.get("risk_notes", "")
    states = ", ".join(plant.get("suitable_states", []))

    # Base description
    summary = wiki_data.get(name, {}).get(
        "wikipedia_data", {}
    ).get("summary", f"{name} is a plant species.")

    # --- Identity & ecology ---
    for t in ecology_templates:
        instructions.append({
            "instruction": t.format(name=name),
            "input": "",
            "output": f"{name} is a {origin} plant that contributes to biodiversity. Carbon score: {carbon}."
        })

    for t in native_templates:
        instructions.append({
            "instruction": t.format(name=name),
            "input": "",
            "output": f"{name} is classified as {origin}. Native plants support ecosystems more effectively."
        })

    # --- Safety ---
    for t in safety_templates:
        instructions.append({
            "instruction": t.format(name=name),
            "input": "",
            "output": (
                f"{name} has safety concerns. {risk}"
                if risk else
                f"{name} has no major recorded toxicity but should be used responsibly."
            )
        })

    # --- Medicinal ---
    if name in nitm_map:
        for use in nitm_map[name].get("uses", []):
            disease = use["disease"]
            part = use["part_used"]

            for t in med_templates:
                instructions.append({
                    "instruction": t.format(name=name, disease=disease),
                    "input": "",
                    "output": (
                        f"{name} is traditionally used for {disease} using the {part}. "
                        "This is traditional knowledge, not a medical prescription."
                    )
                })

            for t in prep_templates:
                instructions.append({
                    "instruction": t.format(name=name),
                    "input": "",
                    "output": (
                        f"Traditionally, the {part} of {name} is prepared carefully. "
                        "Expert guidance is recommended."
                    )
                })

    # --- Conversational ---
    for t in chat_templates:
        instructions.append({
            "instruction": t.format(name=name),
            "input": "",
            "output": summary
        })

# --- Pairwise comparisons (BIG MULTIPLIER) ---
pairs = list(itertools.combinations(
    [p["plant_name"] for p in native_data[:200]], 2
))

for a, b in random.sample(pairs, 2000):
    instructions.append({
        "instruction": f"Compare {a} and {b} in terms of ecological value.",
        "input": "",
        "output": "Native plants generally support biodiversity better than exotic plants."
    })

# Save
with open("plant_instruction_dataset_v2.jsonl", "w") as f:
    for item in instructions:
        f.write(json.dumps(item) + "\n")

print(f"✅ Generated {len(instructions)} instruction samples")
