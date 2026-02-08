def build_context(plants, max_chars=750):
    blocks = []

    for p in plants:
        blocks.append(f"""
        Plant: {p['plant_name']}
        Native: {p.get('origin_type')}
        Uses: {str(p.get('medicinal_uses', ''))[:120]}
        Safety: {str(p.get('risk_notes', ''))[:80]}
        """)


    context = "\n".join(blocks)
    return context[:max_chars]


# def build_prompt(query, context):
#     return f"""
# You are an expert in Indian medicinal plants and sustainability.

# Rules:
# - Prefer native Indian plants
# - Avoid hallucinations
# - Mention safety if relevant
# - Do NOT give medical prescriptions

# Context:
# {context}

# User question:
# {query}

# Answer clearly and responsibly:
# """
def build_prompt(query, context):
    return f"""
Answer the question using ONLY the context.
Prefer native plants.
Mention safety briefly if needed.
Do not give medical advice.

Context:
{context}

Question:
{query}

Answer:
"""
