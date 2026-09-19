from flask import Flask, render_template, request, jsonify
import json
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


app = Flask(__name__)


# ============================================================
# LOAD SCIENTIFIC KNOWLEDGE
# ============================================================

with open("data/knowledge.json", "r", encoding="utf-8") as f:
    knowledge = json.load(f)


# ============================================================
# RAG VECTOR DATABASE
# ============================================================

documents = []

for item in knowledge:

    text = (
        item["topic"] + " "
        + item["condition"] + " "
        + item["action"] + " "
        + item["reason"] + " "
        + " ".join(item["metrics"])
    )

    documents.append(text)


vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2)
)

vectors = vectorizer.fit_transform(documents)


# ============================================================
# ECOLOGICAL SCORE
# ============================================================

def calculate_score(data):

    soil_ph = float(data.get("soil_ph", 7))
    carbon = float(data.get("carbon", 1))
    moisture = float(data.get("moisture", 40))
    rainfall = float(data.get("rainfall", 800))
    temperature = float(data.get("temperature", 25))

    species = float(data.get("species", 50))
    habitat = float(data.get("habitat", 50))

    pollution = float(data.get("pollution", 20))
    deforestation = float(data.get("deforestation", 20))

    # Soil score
    ph_score = max(
        0,
        100 - abs(soil_ph - 6.5) * 20
    )

    carbon_score = min(
        100,
        carbon * 50
    )

    moisture_score = min(
        100,
        moisture * 1.5
    )

    soil_score = (
        ph_score * 0.3
        + carbon_score * 0.35
        + moisture_score * 0.35
    )

    # Climate score
    rainfall_score = min(
        100,
        rainfall / 10
    )

    temperature_score = max(
        0,
        100 - max(0, temperature - 25) * 6
    )

    climate_score = (
        rainfall_score * 0.45
        + temperature_score * 0.55
    )

    # Biodiversity
    biodiversity_score = (
        species * 0.55
        + habitat * 0.45
    )

    # Human pressure
    human_pressure = 100 - (
        pollution * 0.5
        + deforestation * 0.5
    )

    human_pressure = max(
        0,
        min(100, human_pressure)
    )

    final_score = (
        soil_score * 0.30
        + climate_score * 0.20
        + biodiversity_score * 0.35
        + human_pressure * 0.15
    )

    return round(final_score, 2)


# ============================================================
# RISK ENGINE
# ============================================================

def detect_risks(data):

    risks = []

    ph = float(data.get("soil_ph", 7))
    carbon = float(data.get("carbon", 1))
    moisture = float(data.get("moisture", 40))
    rainfall = float(data.get("rainfall", 800))
    temperature = float(data.get("temperature", 25))

    species = float(data.get("species", 50))
    habitat = float(data.get("habitat", 50))

    pollution = float(data.get("pollution", 20))
    deforestation = float(data.get("deforestation", 20))

    if carbon < 1:
        risks.append({
            "title": "Carbon depletion",
            "severity": "High",
            "metrics": "Soil carbon + moisture"
        })

    if moisture < 30 and temperature > 30:
        risks.append({
            "title": "Compound drought stress",
            "severity": "Critical",
            "metrics": "Moisture + temperature"
        })

    if species < 30 and habitat < 30:
        risks.append({
            "title": "Biodiversity collapse risk",
            "severity": "High",
            "metrics": "Species richness + habitat diversity"
        })

    if deforestation > 60 and habitat < 40:
        risks.append({
            "title": "Habitat fragmentation",
            "severity": "High",
            "metrics": "Deforestation + habitat diversity"
        })

    if pollution > 60 and rainfall < 500:
        risks.append({
            "title": "Pollution concentration risk",
            "severity": "High",
            "metrics": "Pollution + water availability"
        })

    if ph < 5.5 or ph > 8.5:
        risks.append({
            "title": "Soil pH stress",
            "severity": "Medium",
            "metrics": "Soil pH + plant growth"
        })

    return risks


# ============================================================
# RAG RETRIEVAL
# ============================================================

def retrieve_knowledge(query, top_k=3):

    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(
        query_vector,
        vectors
    )[0]

    indexes = np.argsort(scores)[::-1][:top_k]

    results = []

    for index in indexes:

        if scores[index] > 0:

            item = knowledge[index].copy()

            item["similarity"] = round(
                float(scores[index]),
                3
            )

            results.append(item)

    return results


# ============================================================
# SMART RECOMMENDATION ENGINE
# ============================================================

def generate_recommendations(data):

    query_parts = []

    carbon = float(data.get("carbon", 1))
    moisture = float(data.get("moisture", 40))
    temperature = float(data.get("temperature", 25))
    species = float(data.get("species", 50))
    habitat = float(data.get("habitat", 50))
    pollution = float(data.get("pollution", 20))
    deforestation = float(data.get("deforestation", 20))

    if carbon < 1:
        query_parts.append(
            "low soil carbon soil moisture soil biodiversity"
        )

    if moisture < 30:
        query_parts.append(
            "low soil moisture drought vegetation"
        )

    if species < 30:
        query_parts.append(
            "low species richness biodiversity habitat"
        )

    if habitat < 30:
        query_parts.append(
            "low habitat diversity fragmentation"
        )

    if deforestation > 50:
        query_parts.append(
            "deforestation habitat connectivity"
        )

    if pollution > 50:
        query_parts.append(
            "pollution water quality biodiversity"
        )

    if temperature > 32:
        query_parts.append(
            "temperature heat stress vegetation"
        )

    if not query_parts:
        query_parts.append(
            "environment biodiversity soil climate"
        )

    query = " ".join(query_parts)

    return retrieve_knowledge(query, 5)


# ============================================================
# WHAT-IF SIMULATION
# ============================================================

def simulate_intervention(data, intervention):

    before = calculate_score(data)

    new_data = data.copy()

    if intervention == "cover_crop":

        new_data["carbon"] = float(
            new_data["carbon"]
        ) + 0.35

        new_data["moisture"] = float(
            new_data["moisture"]
        ) + 8

        new_data["species"] = float(
            new_data["species"]
        ) + 5

    elif intervention == "native_strip":

        new_data["species"] = float(
            new_data["species"]
        ) + 12

        new_data["habitat"] = float(
            new_data["habitat"]
        ) + 15

    elif intervention == "forest_corridor":

        new_data["habitat"] = float(
            new_data["habitat"]
        ) + 20

        new_data["species"] = float(
            new_data["species"]
        ) + 10

        new_data["deforestation"] = max(
            0,
            float(new_data["deforestation"]) - 12
        )

    elif intervention == "buffer_zone":

        new_data["pollution"] = max(
            0,
            float(new_data["pollution"]) - 15
        )

        new_data["habitat"] = float(
            new_data["habitat"]
        ) + 5

    elif intervention == "water_conservation":

        new_data["moisture"] = float(
            new_data["moisture"]
        ) + 15

        new_data["species"] = float(
            new_data["species"]
        ) + 4

    after = calculate_score(new_data)

    return {
        "before": before,
        "after": after,
        "change": round(after - before, 2),
        "new_profile": new_data
    }


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# ANALYZE
# ============================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.json

    score = calculate_score(data)

    risks = detect_risks(data)

    recommendations = generate_recommendations(
        data
    )

    if score >= 75:
        status = "Healthy Ecosystem"

    elif score >= 50:
        status = "Moderate Ecological Stress"

    else:
        status = "High Ecological Pressure"

    return jsonify({

        "score": score,

        "status": status,

        "risks": risks,

        "recommendations": recommendations

    })


# ============================================================
# SIMULATE
# ============================================================

@app.route("/simulate", methods=["POST"])
def simulate():

    data = request.json

    intervention = data.get(
        "intervention"
    )

    result = simulate_intervention(
        data,
        intervention
    )

    return jsonify(result)


# ============================================================
# CHAT
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():

    data = request.json

    message = data.get(
        "message",
        ""
    )

    results = retrieve_knowledge(
        message,
        3
    )

    if not results:

        return jsonify({
            "answer":
            "I could not find strong scientific evidence for that query.",
            "sources": []
        })

    best = results[0]

    answer = (
        f"Recommended action: {best['action']}\n\n"
        f"Scientific reasoning: {best['reason']}\n\n"
        f"Impacted metrics: "
        f"{', '.join(best['metrics'])}\n\n"
        f"Expected time horizon: {best['time']}\n\n"
        f"Evidence source: {best['source']}"
    )

    return jsonify({

        "answer": answer,

        "sources": results

    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )