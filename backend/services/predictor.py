import json
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import euclidean_distances

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CSV_PATH = BASE_DIR / "backend" / "data" / "crop_recommendation.csv"
TIPS_PATH = BASE_DIR / "backend" / "data" / "crop_tips.json"

# ✅ Load dataset
try:
    crop_df = pd.read_csv(CSV_PATH)
    print("✅ Loaded crop CSV:", crop_df.shape)
except FileNotFoundError:
    print("❌ CSV not found.")
    crop_df = pd.DataFrame()

# ✅ Fit scaler dynamically from feature columns only
if not crop_df.empty:
    feature_cols = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
    label_col = 'label'

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(crop_df[feature_cols])

    crop_df_scaled = pd.DataFrame(X_scaled, columns=feature_cols)
    crop_df_scaled[label_col] = crop_df[label_col].values
else:
    crop_df_scaled = pd.DataFrame()

# ✅ Get crop care tips
def get_crop_tips(crop_name: str):
    tips_dict = {
        "rice": {
            "sowing_season": "June to August",
            "watering": "Regular, avoid waterlogging",
            "fertilizer": "Urea, DAP, Potash",
            "pest_control": "Neem oil, Tricyclazole",
            "harvest": "After 110–120 days"
        },
        "wheat": {
            "sowing_season": "November to December",
            "watering": "Irrigate at 21-day interval",
            "fertilizer": "NPK mix, Zinc Sulphate",
            "pest_control": "Chlorpyrifos, neem spray",
            "harvest": "After 120–140 days"
        },
        "jute": {
            "sowing_season": "March to May",
            "watering": "Frequent light irrigation",
            "fertilizer": "Organic compost, Nitrogen-rich fertilizers",
            "pest_control": "Use neem extract or cypermethrin",
            "harvest": "After 100–120 days (when bottom leaves shed)"
        },
        "maize": {
            "sowing_season": "June to July",
            "watering": "Moderate irrigation at key stages",
            "fertilizer": "Nitrogen-rich fertilizers early",
            "pest_control": "Trichogramma for stem borers",
            "harvest": "Ready in 90–100 days"
        },
        "cotton": {
            "sowing_season": "April to May",
            "watering": "Weekly irrigation",
            "fertilizer": "Potassium and nitrogen rich",
            "pest_control": "Bt spray, neem oil",
            "harvest": "150–180 days"
        },
        "coconut": {
            "sowing_season": "June to September",
            "watering": "Water every 3–5 days",
            "fertilizer": "FYM + NPK",
            "pest_control": "Control rhinoceros beetle, mite",
            "harvest": "After 6–7 years (regular)"
        },
        "papaya": {
            "sowing_season": "March to April",
            "watering": "Twice a week",
            "fertilizer": "Organic compost, NPK",
            "pest_control": "Neem extract, copper oxychloride",
            "harvest": "8–10 months"
        },
        "orange": {
            "sowing_season": "June to July",
            "watering": "Irrigate every 7–10 days",
            "fertilizer": "FYM + micronutrients",
            "pest_control": "Oil spray for aphids",
            "harvest": "8–12 months"
        },
        "apple": {
            "sowing_season": "January to March",
            "watering": "Water every 10–12 days",
            "fertilizer": "FYM, boron, urea",
            "pest_control": "Spray insecticides, pruning",
            "harvest": "6–7 months from flowering"
        },
        "muskmelon": {
            "sowing_season": "February to March",
            "watering": "Regular light irrigation",
            "fertilizer": "Organic manure, DAP",
            "pest_control": "Neem oil, sulfur dust",
            "harvest": "2–3 months"
        },
        "watermelon": {
            "sowing_season": "January to March",
            "watering": "Every 4–5 days",
            "fertilizer": "Balanced NPK",
            "pest_control": "Copper-based fungicides",
            "harvest": "75–90 days"
        },
        "grapes": {
            "sowing_season": "November to January",
            "watering": "2–3 times/week",
            "fertilizer": "Phosphorus, zinc, FYM",
            "pest_control": "Mite and mealybug spray",
            "harvest": "6–8 months"
        },
        "mango": {
            "sowing_season": "July to August",
            "watering": "Irrigate every 2–3 weeks",
            "fertilizer": "NPK + FYM",
            "pest_control": "Mango hopper control",
            "harvest": "4–5 months from flowering"
        },
        "banana": {
            "sowing_season": "April to May",
            "watering": "Twice a week",
            "fertilizer": "Potassium-rich mix",
            "pest_control": "Spray monocrotophos",
            "harvest": "11–12 months"
        },
        "pomegranate": {
            "sowing_season": "February to March",
            "watering": "Weekly",
            "fertilizer": "NPK + boron",
            "pest_control": "Neem oil, copper spray",
            "harvest": "5–7 months"
        },
        "lentil": {
            "sowing_season": "October to November",
            "watering": "Every 20 days",
            "fertilizer": "Phosphorus-rich",
            "pest_control": "Neem oil, pyrethrum",
            "harvest": "3.5–4 months"
        },
        "blackgram": {
            "sowing_season": "July to August",
            "watering": "Once a week",
            "fertilizer": "Organic manure, DAP",
            "pest_control": "Neem + Trichoderma",
            "harvest": "3 months"
        },
        "mungbean": {
            "sowing_season": "March to April",
            "watering": "Every 7–10 days",
            "fertilizer": "NPK mix",
            "pest_control": "Neem oil",
            "harvest": "60–75 days"
        },
        "mothbeans": {
            "sowing_season": "June to July",
            "watering": "Drought tolerant",
            "fertilizer": "Low fertilizer needs",
            "pest_control": "Organic sprays",
            "harvest": "65–70 days"
        },
        "pigeonpeas": {
            "sowing_season": "June to July",
            "watering": "At flowering & pod filling",
            "fertilizer": "NPK and Rhizobium",
            "pest_control": "Chlorpyrifos",
            "harvest": "5–6 months"
        },
        "kidneybeans": {
            "sowing_season": "March to May",
            "watering": "Twice a week",
            "fertilizer": "Phosphorus and nitrogen",
            "pest_control": "Neem oil",
            "harvest": "100–120 days"
        },
        "chickpea": {
            "sowing_season": "October to November",
            "watering": "At flowering & pod stage",
            "fertilizer": "Zinc, phosphorus",
            "pest_control": "Bt spray",
            "harvest": "3.5–4 months"
        },
        "coffee": {
            "sowing_season": "June to August",
            "watering": "Irrigate at dry spell",
            "fertilizer": "NPK + compost",
            "pest_control": "Spray copper oxychloride",
            "harvest": "9–11 months"
        }
    }

    return tips_dict.get(crop_name.lower())


# ✅ Suggest top crops based on user input
def get_top_matching_crops(user_input: list, top_n=5):
    if crop_df_scaled.empty:
        return []

    input_scaled = scaler.transform([user_input])
    data_scaled = crop_df_scaled[feature_cols].values

    distances = euclidean_distances(data_scaled, input_scaled).flatten()
    crop_df_scaled["distance"] = distances

    top_matches = crop_df_scaled.nsmallest(top_n, "distance")

    results = []
    for _, row in top_matches.iterrows():
        crop_name = row["label"]
        tips = get_crop_tips(crop_name)
        results.append({
            "crop": crop_name,
            "similarity": round(100 - row["distance"] * 100, 2),
            "tips": tips
        })
    return results
