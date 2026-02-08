#!/usr/bin/env python3
"""
Full scraper for NITM Medicinal Plants DB
(https://nitmmedplantsdb.in/)

What this script does:
1. Checks robots.txt for permission to access /autocomplete.php and /search_results.php
2. Harvests scientific names via autocomplete.php by iterating over prefixes (a..z, 0..9, common digrams)
3. For each unique name, posts to search_results.php (keycat=1) to retrieve the detail page HTML
4. Parses the detail HTML to extract:
   - plant_name, vernacular names, synonyms, author, family, description, phenology
   - location table rows
   - pharmacology text and reference link
   - chemical composition
   - uses (disease <-> part_used)
   - image URLs
5. Saves each record as a JSONL line to output file
6. Optional: download images to a folder (set DOWNLOAD_IMAGES=True)

USAGE:
    python3 nitmmedplants_full_scraper.py

Requirements:
    pip install requests beautifulsoup4 tqdm

CAUTION / ETHICS:
 - This script checks robots.txt and will not proceed if disallowed.
 - Use a polite User-Agent with contact email and set RATE_LIMIT_SECONDS.
 - If you plan heavy use, contact the site admins first.
"""

import requests, json, time, os, sys, re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from tqdm import tqdm
from requests.adapters import HTTPAdapter, Retry

# ---------- CONFIG ----------
BASE = "https://nitmmedplantsdb.in/"
AUTOCOMPLETE = urljoin(BASE, "autocomplete.php")
SEARCH_RESULTS = urljoin(BASE, "search_results.php")
USER_AGENT = "NITM-MedicinalPlantBot/1.0 (+mailto:your-email@example.com)"
OUTPUT_FILE = "nitm_plants_all.jsonl"
IMAGES_DIR = "nitm_images"
RATE_LIMIT_SECONDS = 1.0      # seconds between requests
DOWNLOAD_IMAGES = False       # set True to download images
MAX_RETRIES = 3
# ----------------------------

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})
retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[429,500,502,503,504])
session.mount("https://", HTTPAdapter(max_retries=retries))

def check_robots_ok(urls):
    """Check robots.txt using urllib.robotparser"""
    parsed = urlparse(BASE)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
    except Exception as e:
        print(f"[WARN] Could not read robots.txt ({robots_url}): {e}")
        # Fall back to permissive by default but warn
        return True

    for u in urls:
        path = urlparse(u).path
        allowed = rp.can_fetch(USER_AGENT, path)
        print(f"[robots.txt] path={path} allowed={allowed}")
        if not allowed:
            return False
    return True

def fetch_autocomplete(prefix):
    """Call autocomplete.php with given prefix; expect JSON (array)"""
    try:
        r = session.get(AUTOCOMPLETE, params={"term": prefix, "extraParams": 1}, timeout=20)
        r.raise_for_status()
        # Some sites return JSON array or array of objects. Try to parse robustly.
        try:
            return r.json()
        except Exception:
            # if not JSON, try to extract quoted items
            txt = r.text
            # attempt to find quoted suggestions
            items = re.findall(r'\"([^\"]+)\"', txt)
            return items
    except Exception as e:
        print(f"[WARN] autocomplete failed for prefix='{prefix}': {e}")
        return []

def normalize_name(s):
    if not s: return s
    return ' '.join(s.strip().split())

def get_all_scientific_names():
    """Build full set of names by probing autocomplete with many prefixes."""
    print("[*] Collecting plant names via autocomplete...")
    names = set()

    # prefixes: single letters and digits and some common bigrams to try to discover all entries
    prefixes = list("abcdefghijklmnopqrstuvwxyz0123456789")
    prefixes += ["aa","ab","ac","ad","al","an","ar","ba","be","bi","ca","ch","co","de","di","dr","ga","ha","ka","kh","ma","mu","na","ni","pa","ph","ra","re","sa","sh","ta","th","va"]

    for p in prefixes:
        items = fetch_autocomplete(p)
        # autocomplete may return list of strings or list of {label:...,value:...} dicts
        for it in items:
            if isinstance(it, dict):
                label = it.get("label") or it.get("value") or it.get("name") or str(it)
            else:
                label = it
            if not label:
                continue
            label = normalize_name(label)
            # small filter: ensure it looks like a binomial (two words) OR contains known characters
            if len(label) > 1:
                names.add(label)
        time.sleep(RATE_LIMIT_SECONDS)  # polite pacing

    print(f"[+] Found {len(names)} candidate names from autocomplete.")
    # Optionally return sorted list
    return sorted(names)

def post_search_for_name(name):
    """
    POST to search_results.php with keycat=1 (Plant Scientific Name).
    Response is the detail page HTML (per provided sample).
    """
    try:
        r = session.post(SEARCH_RESULTS, data={"keycat": 1, "keyword": name}, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[ERROR] search POST failed for '{name}': {e}")
        return None

# -- Parsers for the detail HTML (based on the Search Result.html you provided) --
def parse_species_html(html, base=BASE):
    soup = BeautifulSoup(html, "html.parser")

    data = {
        "plant_name": None,
        "vernacular_names": [],
        "synonyms": None,
        "author": None,
        "family": None,
        "description": None,
        "phenology": None,
        "locations": [],
        "pharmacology": None,
        "pharmacology_reference": None,
        "chemical_composition": None,
        "uses": [],
        "images": [],
        "raw_html_snippet": None
    }

    # plant name (h2)
    h2 = soup.find("h2")
    if h2:
        data["plant_name"] = normalize_name(h2.get_text())

    # collect rows
    rows = soup.find_all("tr")
    # Save a raw snippet for provenance
    body_div = soup.find("div", {"class": "container"})
    if body_div:
        data["raw_html_snippet"] = str(body_div)[:2000]  # limited length

    # The page used combined <td colspan=...> blocks for many fields.
    for tr in rows:
        t = tr.get_text(" ", strip=True)

        # vernacular
        if "Vernacular Name" in t:
            # the text looks like "Vernacular Name - Language : Blackeyed Susan (English) ,Coral pea..."
            # find the colon and split
            if ":" in t:
                after = t.split(":",1)[1]
                # split by comma but keep phrases with parentheses
                parts = [normalize_name(x) for x in after.split(",") if x.strip()]
                data["vernacular_names"].extend(parts)

        # synonym
        elif t.startswith("Synonym") or "Synonym(s)" in t:
            # "Synonym(s) : Not Available"
            if ":" in t:
                data["synonyms"] = normalize_name(t.split(":",1)[1])

        # author
        elif t.startswith("Author") or "Author" in t and len(t.split())<=4:
            # fallback: look for "Author :" pattern
            m = re.search(r'Author\s*:\s*(.+)', t)
            if m:
                data["author"] = normalize_name(m.group(1))

        # family
        elif "Family" in t:
            m = re.search(r'Family\s*:\s*(.+)', t)
            if m:
                data["family"] = normalize_name(m.group(1))

        # Basic description
        elif "Basic Description" in t or "Basic description" in t:
            # "Basic Description of Plant : A glabrous..."
            parts = t.split(":",1)
            if len(parts) > 1:
                data["description"] = normalize_name(parts[1])

        # Phenology
        elif "Phenology" in t:
            parts = t.split(":",1)
            if len(parts) > 1:
                data["phenology"] = normalize_name(parts[1])

        # Pharmacology block: pages typically have a big "Pharmacology:" followed by large text
        elif "Pharmacology" in t and ("Pharmacology:" in t or t.lower().startswith("pharmacology")):
            # take after 'Pharmacology:' or after the heading
            if "Pharmacology:" in t:
                data["pharmacology"] = normalize_name(t.split("Pharmacology:",1)[1])
            else:
                data["pharmacology"] = normalize_name(t)

            # link for View Reference present under same tr sometimes
            a = tr.find("a", href=True)
            if a:
                data["pharmacology_reference"] = urljoin(base, a["href"])

        # Chemical Composition section
        elif "Chemical Composition" in t or "Chemical composition" in t:
            parts = t.split(":",1)
            if len(parts) > 1:
                data["chemical_composition"] = normalize_name(parts[1])

    # Location table detection:
    # The sample has header row with "Place | District | State | Country | Soil | Vegitation | Source | Occurrence"
    # We attempt to find that row and then capture subsequent rows with 8 columns.
    location_headers = None
    for tr in rows:
        t = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(t) >= 8 and "Place" in t[0] and "District" in t[1]:
            location_headers = t[:8]
            break

    if location_headers:
        found = False
        for tr in rows:
            cells = tr.find_all("td")
            txts = [c.get_text(" ", strip=True) for c in cells]
            if len(txts) >= 8 and txts[0] == location_headers[0]:
                found = True
                continue
            if found and len(txts) >= 8:
                # Append until next section header likely occurs
                data["locations"].append({
                    "place": txts[0],
                    "district": txts[1],
                    "state": txts[2],
                    "country": txts[3],
                    "soil": txts[4],
                    "vegetation": txts[5],
                    "source": txts[6],
                    "occurrence": txts[7]
                })

    # Uses table: detect header row "Disease Name" and "Part Name"
    use_section = False
    for tr in rows:
        t = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        textjoined = " ".join(t)
        if "Disease Name" in textjoined and "Part Name" in textjoined:
            use_section = True
            continue
        if use_section:
            # many rows in the form <td colspan=4> disease </td><td colspan=4> part </td>
            # get the non-empty cells
            cells = [c.get_text(" ", strip=True) for c in tr.find_all("td") if c.get_text(" ", strip=True)]
            if len(cells) >= 2:
                disease = normalize_name(cells[0])
                part = normalize_name(cells[-1])
                if disease:
                    data["uses"].append({"disease": disease, "part_used": part})

    # Images: find image tags linking to PlantImage folder or assets/img/PlantImage
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue
        if "PlantImage" in src or "assets/img/PlantImage" in src:
            data["images"].append(urljoin(base, src))

    # Deduplicate lists
    data["vernacular_names"] = list(dict.fromkeys(data["vernacular_names"]))
    data["images"] = list(dict.fromkeys(data["images"]))
    data["uses"] = [dict(t) for t in {tuple(sorted(d.items())): d for d in data["uses"]}.values()]

    return data

def save_jsonl(record, fpath=OUTPUT_FILE):
    with open(fpath, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def download_image(url, dest_folder=IMAGES_DIR):
    try:
        os.makedirs(dest_folder, exist_ok=True)
        fname = os.path.basename(urlparse(url).path)
        dest_path = os.path.join(dest_folder, fname)
        if os.path.exists(dest_path):
            return dest_path
        r = session.get(url, stream=True, timeout=30)
        r.raise_for_status()
        with open(dest_path, "wb") as fh:
            for chunk in r.iter_content(1024*8):
                fh.write(chunk)
        return dest_path
    except Exception as e:
        print(f"[WARN] failed to download image {url}: {e}")
        return None

def main():
    # 1. robots check
    allowed = check_robots_ok([AUTOCOMPLETE, SEARCH_RESULTS])
    if not allowed:
        print("[ERROR] robots.txt disallows scraping the required endpoints. Aborting.")
        sys.exit(1)

    # 2. gather names
    names = get_all_scientific_names()
    if not names:
        print("[ERROR] no names discovered; aborting.")
        sys.exit(1)

    # For robustness: optionally dedupe and sort
    names = sorted(set(names))
    print(f"[INFO] total names to scrape: {len(names)}")

    # 3. iterate and scrape
    for name in tqdm(names, desc="Plants"):
        try:
            html = post_search_for_name(name)
            if not html:
                time.sleep(RATE_LIMIT_SECONDS)
                continue

            record = parse_species_html(html)
            # add metadata
            record["_harvested_name"] = name
            record["_source_search_url"] = SEARCH_RESULTS
            record["_retrieved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

            save_jsonl(record)

            # optionally download images
            if DOWNLOAD_IMAGES and record.get("images"):
                for url in record["images"]:
                    download_image(url)

            time.sleep(RATE_LIMIT_SECONDS)
        except KeyboardInterrupt:
            print("\n[INTERRUPT] Stopping early.")
            break
        except Exception as e:
            print(f"[ERROR] general error for '{name}': {e}")
            # continue to next name
            time.sleep(RATE_LIMIT_SECONDS)

    print("[DONE] scraping finished. Output:", OUTPUT_FILE)
    if DOWNLOAD_IMAGES:
        print("[DONE] images saved in:", IMAGES_DIR)

if __name__ == "__main__":
    main()

