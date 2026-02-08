# import subprocess

# def generate(prompt):
#     try:
#         result = subprocess.run(
#             ["ollama", "run", "mistral"],
#             input=prompt,
#             text=True,
#             capture_output=True,
#             timeout=120
#         )

#         if result.returncode != 0:
#             return f"❌ Ollama error:\n{result.stderr}"

#         if not result.stdout.strip():
#             return "⚠️ Ollama returned empty output."

#         return result.stdout.strip()

#     except Exception as e:
#         return f"❌ Exception while calling Ollama: {e}"
import subprocess

MODEL_NAME = "phi3:mini"   # 🔴 change only this if needed

# def generate(prompt):
#     try:
#         result = subprocess.run(
#             ["ollama", "run", MODEL_NAME],
#             input=prompt,
#             text=True,
#             capture_output=True,
#             timeout=60   # 🔴 reduce timeout
#         )

#         if result.returncode != 0:
#             return f"❌ Ollama error:\n{result.stderr}"

#         if not result.stdout.strip():
#             return "⚠️ Model returned empty output."

#         return result.stdout.strip()

#     except subprocess.TimeoutExpired:
#         return "⚠️ Model took too long to respond. Try a shorter question."

#     except Exception as e:
#         return f"❌ Exception while calling Ollama: {e}"
def generate_answer(query, plants):
    lines = []

    lines.append(f"Based on your question: **{query}**, here are relevant plants:\n")

    for p in plants:
        lines.append(f"### 🌿 {p['plant_name']}")
        lines.append(f"- Common name: {p.get('common_name', '—')}")
        lines.append(f"- Native status: {p.get('origin_type', 'unknown')}")
        lines.append(f"- Medicinal use: {p.get('medicinal_uses', 'Traditional use')}")
        lines.append(f"- Carbon score: {p.get('carbon_score', 0)}")

        risk = p.get("risk_notes", "")
        if isinstance(risk, str) and any(w in risk.lower() for w in ["toxic", "poison"]):
            lines.append("⚠️ **Safety warning:** This plant may be toxic.")

        lines.append("")  # spacing

    return "\n".join(lines)

