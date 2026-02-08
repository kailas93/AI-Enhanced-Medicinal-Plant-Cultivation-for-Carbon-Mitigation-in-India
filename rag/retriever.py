import json
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

DATA_PATH = Path("data/plant_ai_dataset_v2_native_state.json")

_model = None
_plants = None
_embeddings = None


def load_data():
    global _model, _plants, _embeddings

    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")

    if _plants is None:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            _plants = json.load(f)

        texts = [
            f"{p['plant_name']} {p.get('common_name','')} {p.get('medicinal_uses','')}"
            for p in _plants
        ]
        _embeddings = _model.encode(texts, convert_to_tensor=True)


def retrieve(query, top_k=5, state=None, native_only=True):
    load_data()

    query_emb = _model.encode(query, convert_to_tensor=True)
    scores = util.cos_sim(query_emb, _embeddings)[0]

    ranked = scores.argsort(descending=True)

    results = []
    for idx in ranked:
        plant = _plants[int(idx)]

        if native_only and plant.get("origin_type") != "native":
            continue

        if state and state not in plant.get("suitable_states", []):
            continue

        results.append(plant)
        if len(results) >= top_k:
            break

    return results
