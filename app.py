
# ----------------------------------
# RAG Imports
# ----------------------------------
from rag.retriever import retrieve
from rag.prompt_builder import build_context, build_prompt
# from rag.generator import generate, generate_answer
from rag.generator import generate_answer

from rag.safety import apply_safety

import streamlit as st
import json
import pandas as pd
import pickle
import os
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"


# ----------------------------------
# App Config
# ----------------------------------
st.set_page_config(
    page_title="🌱 PlantMatch – Native Plant AI",
    layout="centered"
)

# ----------------------------------
# Sidebar Dashboard
# ----------------------------------
st.sidebar.title("🌱 PlantMatch Dashboard")

mode = st.sidebar.radio(
    "Choose experience",
    [
        "🏡 Home & Biodiversity Plants",
        "🩺 Medicinal Plant Support",
        "🧠 AI Plant Expert (RAG)"
    ]
)


# ----------------------------------
# Load Core Dataset
# ----------------------------------
@st.cache_data
def load_data():
    with open("/home/kailas/Desktop/new_med_leaf/data/plant_ai_dataset_v2_native_state.json", "r", encoding="utf-8") as f:
        return pd.DataFrame(json.load(f))

df = load_data()

# ----------------------------------
# Load Plant Recommendation Model
# ----------------------------------
@st.cache_resource
def load_plant_model():
    with open("/home/kailas/Desktop/new_med_leaf/data/plant_recommendation_model.pkl", "rb") as f:
        return pickle.load(f)

plant_bundle = load_plant_model()
plant_model = plant_bundle["model"]
plant_encoder = plant_bundle["plant_type_encoder"]
climate_encoder = plant_bundle["climate_zone_encoder"]

# ----------------------------------
# Load Disease Model
# ----------------------------------
@st.cache_resource
def load_disease_model():
    with open("/home/kailas/Desktop/new_med_leaf/data/disease_support_model.pkl", "rb") as f:
        return pickle.load(f)

disease_bundle = load_disease_model()
disease_model = disease_bundle["model"]
disease_encoder = disease_bundle["disease_encoder"]
disease_df = disease_bundle["reference_df"]

# ============================================================
# 🏡 MODE 1 — HOME & BIODIVERSITY (Existing Flow)
# ============================================================
if mode == "🏡 Home & Biodiversity Plants":

    if "step" not in st.session_state:
        st.session_state.step = 0
        st.session_state.score = 0
        st.session_state.answers = {}

    def next_step():
        st.session_state.step += 1

    st.title("🌱 PlantMatch")
    st.caption("AI-powered • Native-first • Biodiversity-friendly")

    st.progress(st.session_state.step / 6)

    # STEP 0 – Intro
    if st.session_state.step == 0:
        st.markdown("""
        ### 🌍 One native plant can support **10–50× more life**
        than an exotic plant.
        """)
        if st.button("🚀 Start"):
            next_step()

    # STEP 1 – Location
    elif st.session_state.step == 1:
        states = sorted({s for states in df["suitable_states"].dropna() for s in states})
        state = st.selectbox("📍 Your state", states)
        st.session_state.answers["state"] = state
        st.session_state.score += 5
        if st.button("Next 👉"):
            next_step()

    # STEP 2 – Space
    elif st.session_state.step == 2:
        space = st.radio("🏡 Space available", [
            "Balcony / Indoor",
            "Small garden",
            "Large garden"
        ])
        st.session_state.answers["space"] = space
        st.session_state.score += 5
        if st.button("Next 👉"):
            next_step()

    # STEP 3 – Purpose
    elif st.session_state.step == 3:
        purpose = st.multiselect(
            "🎯 What do you want?",
            ["Carbon absorption", "Medicinal use", "Birds & butterflies", "Low maintenance"]
        )
        st.session_state.answers["purpose"] = purpose
        st.session_state.score += len(purpose) * 3
        if st.button("Next 👉"):
            next_step()

    # STEP 4 – Native Choice
    elif st.session_state.step == 4:
        choice = st.radio(
            "🌿 Which would you choose?",
            ["Native plant 🌱", "Exotic plant 🌴"]
        )
        if "Native" in choice:
            st.session_state.score += 20
            st.success("🏆 Native plants strengthen local ecosystems!")
        if st.button("Show My Plants 🌱"):
            next_step()

    # STEP 5 – ML Recommendation
    elif st.session_state.step == 5:
        st.header("🌱 AI-Recommended Plants")

        state = st.session_state.answers["state"]

        candidates = df[
            df["suitable_states"].apply(
                lambda x: state in x if isinstance(x, list) else False
            )
        ].copy()

        candidates["is_native"] = (candidates["origin_type"] == "native").astype(int)
        candidates["carbon_score"] = candidates["carbon_score"].fillna(0)
        candidates["plant_type"] = candidates["plant_type"].fillna("unknown")
        candidates["climate_zone"] = candidates["climate_zone"].fillna("unknown")

        candidates["plant_type_enc"] = plant_encoder.transform(candidates["plant_type"])
        candidates["climate_zone_enc"] = climate_encoder.transform(candidates["climate_zone"])

        X = candidates[[
            "is_native", "carbon_score",
            "plant_type_enc", "climate_zone_enc"
        ]]

        candidates["ml_score"] = plant_model.predict(X)

        for _, row in candidates.sort_values("ml_score", ascending=False).head(5).iterrows():
            st.markdown(f"""
            ### 🌿 {row['plant_name']}
            - Common name: {row['common_name']}
            - Type: {row['plant_type']}
            - Carbon score: 🌍 {row['carbon_score']}
            """)

            if isinstance(row["risk_notes"], str) and any(
                w in row["risk_notes"].lower() for w in ["toxic", "poison", "fatal"]
            ):
                st.error("⚠️ Toxic – avoid if children/pets are present")

        st.success(f"🌟 Your Eco Score: {st.session_state.score}")
        st.button("🔄 Restart", on_click=lambda: st.session_state.clear())
    # ============================================================
# 🧠 MODE 3 — AI PLANT EXPERT (RAG)
# ============================================================
elif mode == "🧠 AI Plant Expert (RAG)":

    st.title("🧠 AI Plant Expert")
    st.caption("Grounded • Native-first • Safety-aware")

    st.markdown("""
    Ask natural-language questions like:
    - *Which native medicinal plants are good for cough in Kerala?*
    - *Low-maintenance native plants for balcony gardening*
    - *Plants that help biodiversity and absorb carbon*
    """)

    query = st.text_input("💬 Ask your question")

    # State filter
    all_states = sorted({
        s for states in df["suitable_states"].dropna() for s in states
    })
    state = st.selectbox("📍 Filter by state (optional)", ["Any"] + all_states)

    native_only = st.checkbox("🌱 Prefer native plants only", value=True)

    top_k = st.slider("🔎 Number of plants to consider", 1, 4, 2)


    #top_k = st.slider("🔎 Number of plants to consider", 3, 8, 5)

    if st.button("Ask AI 🌿") and query:

        with st.spinner("🔍 Retrieving plant knowledge..."):
            plants = retrieve(
                query=query,
                top_k=top_k,
                state=None if state == "Any" else state,
                native_only=native_only
            )

        if not plants:
            st.warning("No matching plants found. Try adjusting filters.")
        else:
            with st.spinner("🧠 Generating grounded answer..."):
                # context = build_context(plants)
                # prompt = build_prompt(query, context)
                # answer = generate(prompt)
                # answer = apply_safety(answer)
                answer = generate_answer(query, plants)
                answer = apply_safety(answer)

                st.markdown("### 🌿 AI Answer")
                st.markdown(answer)

            # Optional: Show sources
            with st.expander("🔎 Plants used for this answer"):
                for p in plants:
                    st.markdown(f"""
                    **{p['plant_name']}**  
                    - Common name: {p.get('common_name', '—')}
                    - Native status: {p.get('origin_type')}
                    - Carbon score: {p.get('carbon_score', 0)}
                    """)



# ============================================================
# 🩺 MODE 2 — MEDICINAL PLANT SUPPORT (NEW)
# ============================================================
else:
    st.title("🩺 Medicinal Plant Support")
    st.caption("Traditional knowledge • Safety-first • Non-prescriptive")

    disease = st.selectbox(
        "Select a common health concern",
        sorted(disease_df["disease"].unique())
    )

    if disease:
        st.subheader("🌿 Plants traditionally used")

        enc = disease_encoder.transform([disease])[0]
        predicted = disease_model.predict([[enc]])

        results = disease_df[
            disease_df["plant_name"].isin(predicted)
        ].drop_duplicates("plant_name").head(6)

        for _, row in results.iterrows():
            st.markdown(f"""
            ### 🌿 {row['plant_name']}
            - Part used: {row['plant_part']}
            - Family: {row['family']}
            """)

            if row["toxicity"]:
                st.error("⚠️ Toxic plant – expert guidance required")

        st.warning("""
        ⚠️ This information is based on traditional knowledge.
        It is **not a medical prescription**.
        Please consult a qualified healthcare professional.
        """)
