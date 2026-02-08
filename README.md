# AI-Enhanced Medicinal Plant Cultivation for Carbon Mitigation in India

## Project Description

The pharmaceutical industry contributes significantly to global greenhouse gas (GHG) emissions due to energy-intensive drug manufacturing, chemical processing, packaging, and long-distance transportation. This impact is especially high for common lifestyle-related health conditions such as cold, cough, indigestion, acidity, mild infections, and immunity-related issues.

India has a long history of managing many of these conditions using **medicinal plant–based treatments** rooted in Ayurveda, Siddha, and folk medicine. These treatments rely on locally grown medicinal plants that require minimal synthetic inputs and also act as **natural carbon sinks**.

### Importance of Native Medicinal Plants

Native medicinal plants play a crucial role in **biodiversity conservation and carbon mitigation**:

- Native plants interact with **many local species** such as insects, birds, pollinators, and soil microbes.
- These interactions strengthen **local ecosystems** and food chains.
- Native plants are well adapted to local climate and soil conditions and require **less water and fewer external inputs**.
- They contribute to **higher ecosystem-level carbon absorption**.

In contrast, **foreign or exotic plants**:
- Interact with fewer local species
- Provide limited support to native biodiversity
- Often show **lower long-term carbon sequestration capacity**

Promoting native medicinal plants therefore supports **low-carbon healthcare, biodiversity protection, and climate resilience**.

---

## Problem Statement

Although India has extensive public data on medicinal plants, there is no unified intelligent system that connects:

- Medicinal plant knowledge
- Carbon footprint mitigation
- Native vs foreign plant identification
- Practical decision-making for farmers and households

As a result:
- Farmers hesitate to adopt medicinal plant cultivation
- Individuals lack confidence in traditional remedies
- Dependence on carbon-intensive pharmaceutical products continues

---

## Project Goal

To develop an **AI-powered medicinal plant knowledge and recommendation system** that promotes:

- Low-carbon healthcare alternatives
- Native medicinal plant cultivation
- Carbon footprint mitigation through nature-based solutions

---

## System Architecture

User
↓
Streamlit Application (app.py)
↓
Curated Medicinal Plant Datasets
↓
Machine Learning Models
↓
RAG (Retriever + Context Builder)
↓
Response Generator + Safety Layer
↓
Final Output


---

## Machine Learning Models

### 1. Plant Recommendation Model
- **Model:** Random Forest Regressor
- **Purpose:** Rank plants based on sustainability and suitability
- **Features:**
  - Native status
  - Carbon score
  - Climate zone
  - Plant type
- **Dataset:** `plant_ai_dataset_v2_native_state.json`

### 2. Medicinal Plant Support Model
- **Model:** Random Forest Classifier
- **Purpose:** Suggest medicinal plants for common diseases
- **Dataset:** `plant_disease_support.json`
- **Safety:** Toxicity warnings included

---

## RAG (Retrieval-Augmented Generation)

The system uses a **RAG-based approach** to ensure factual correctness and avoid hallucinations.

### RAG Workflow
1. User submits a natural language query
2. Semantic retrieval using Sentence Transformers
3. Filtering by state and native preference
4. Context building from verified data
5. Grounded response generation
6. Safety disclaimer added

### Optional LLM
- Ollama with `phi3:mini` (lightweight and local)
- Used only for response phrasing
- Knowledge always comes from datasets

---

## Dataset Description

### 1. `bsi_medicinal_plants.json`
- **Source:** https://bsi.gov.in/page/en/medicinal-plant-database
- **Content:** 2000+ species, scientific names, family names

### 2. `bsi_medicinal_plants_with_wikipedia.json`
- **Source:** Wikipedia
- **Content:** Detailed plant descriptions and usage

### 3. `nitm_plants_all.jsonl`
- **Source:** https://nitmmedplantsdb.in/
- **Content:** Medicinal uses and plant parts

### 4. `plant_instruction_dataset_v2.jsonl`
- **Content:** 23,000+ instruction–response samples
- **Created from:** Above datasets
- **Status:** First-round validation and cleaning completed

---

## File Structure
├── app.py
├── data
│ ├── bsi_medicinal_plants.json
│ ├── bsi_medicinal_plants_with_wikipedia.json
│ ├── nitm_plants_all.jsonl
│ ├── plant_ai_dataset_v2_native_state.json
│ ├── plant_instruction_dataset_v2.jsonl
│ └── model files and scripts
└── rag
├── retriever.py
├── generator.py
├── prompt_builder.py
└── safety.py


---

## Installation Instructions

### Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

ollama pull phi3:mini/mistral(optional)

streamlit run app.py




