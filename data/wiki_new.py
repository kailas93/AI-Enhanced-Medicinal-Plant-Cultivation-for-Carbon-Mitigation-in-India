import json
import re
import requests
import wikipediaapi
from tqdm import tqdm


# ==================================================
# 1. WIKIPEDIA API INIT (USER AGENT REQUIRED)
# ==================================================
USER_AGENT = "MedLeaf-LLM-Dataset/1.0 (academic research; India)"

wiki = wikipediaapi.Wikipedia(
    language="en",
    user_agent=USER_AGENT
)


# ==================================================
# 2. LOAD INPUT DATA
# ==================================================
with open("bsi_medicinal_plants.json", "r", encoding="utf-8") as f:
    plants = json.load(f)


# ==================================================
# 3. HELPER FUNCTIONS
# ==================================================

def normalize_scientific_name(name):
    """
    Remove author citations → Genus species
    """
    if not name:
        return ""

    name = re.sub(r"\(.*?\)", "", name)           # remove (L.)
    name = re.sub(r"\s+ex\s+.*$", "", name, flags=re.I)
    name = re.sub(r"\s+[A-Z][a-z]*\.?$", "", name)

    parts = name.strip().split()
    return " ".join(parts[:2]) if len(parts) >= 2 else name.strip()


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"\[[0-9]+\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_all_sections(page):
    """
    Recursively extract ALL headers and subheaders
    """
    sections = {}

    def recurse(section):
        sections[section.title] = clean_text(section.text)
        for sub in section.sections:
            recurse(sub)

    for sec in page.sections:
        recurse(sec)

    return sections


def mediawiki_search(query, limit=3):
    """
    Wikipedia search using MediaWiki API
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": limit
    }

    headers = {"User-Agent": USER_AGENT}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        return [item["title"] for item in data.get("query", {}).get("search", [])]
    except Exception:
        return []


def resolve_page(scientific_name):
    """
    Resolution strategy:
    1. Direct species page
    2. Wikipedia search API
    3. Genus page
    """
    # 1. Direct lookup
    page = wiki.page(scientific_name)
    if page.exists():
        return page, "species"

    # 2. Search fallback
    titles = mediawiki_search(scientific_name)
    for title in titles:
        page = wiki.page(title)
        if page.exists():
            return page, "search"

    # 3. Genus fallback
    genus = scientific_name.split()[0]
    page = wiki.page(genus)
    if page.exists():
        return page, "genus"

    return None, None


# ==================================================
# 4. SCRAPING LOOP
# ==================================================

output = []

for plant in tqdm(plants, desc="Scraping Wikipedia"):
    original_name = plant.get("plant_name", "")
    family = plant.get("family", "")
    common_name = plant.get("common_name", "")

    normalized_name = normalize_scientific_name(original_name)

    page, source = resolve_page(normalized_name)

    if not page:
        wikipedia_data = {
            "error": "Wikipedia page not found"
        }
    else:
        wikipedia_data = {
            "page_title": page.title,
            "summary": clean_text(page.summary),
            "sections": extract_all_sections(page),
            "source": source
        }

    output.append({
        "plant_name": original_name,
        "normalized_name": normalized_name,
        "family": family,
        "common_name": common_name,
        "wikipedia_data": wikipedia_data
    })


# ==================================================
# 5. SAVE OUTPUT
# ==================================================

with open("bsi_medicinal_plants_with_wikipedia.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\n✅ Wikipedia scraping completed successfully")
