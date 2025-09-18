import json
import pandas as pd
import pickle
from pathlib import Path
from sklearn.metrics.pairwise import euclidean_distances

# ✅ Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "backend" / "data" / "all_crops.parquet"
MODEL_PATH = BASE_DIR / "backend" / "model" / "crop_recommendation.pkl"
SCALER_PATH = BASE_DIR / "backend" / "model" / "preprocessor.pkl"

# ✅ Load dataset
try:
    crop_df = pd.read_parquet(DATA_PATH)
    print("✅ Loaded Parquet dataset:", crop_df.shape)
except FileNotFoundError:
    print("❌ Parquet dataset not found.")
    crop_df = pd.DataFrame()

# ✅ Load model and scaler
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

with open(SCALER_PATH, "rb") as f:
    scaler = pickle.load(f)

# ✅ Feature columns
feature_cols = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
label_col = 'label'

# ✅ Crop care tips
def get_crop_tips(crop_name: str):
    tips_dict = {
        "rice": {"sowing_season": "June to August","watering": "Regular, avoid waterlogging","fertilizer": "Urea, DAP, Potash","pest_control": "Neem oil, Tricyclazole","harvest": "After 110–120 days"},
        "wheat": {"sowing_season": "November to December","watering": "Irrigate at 21-day interval","fertilizer": "NPK mix, Zinc Sulphate","pest_control": "Chlorpyrifos, neem spray","harvest": "After 120–140 days"},
        "maize": {"sowing_season": "June to July","watering": "Moderate irrigation at key stages","fertilizer": "Nitrogen-rich fertilizers early","pest_control": "Trichogramma for stem borers","harvest": "90–100 days"},
        "cotton": {"sowing_season": "April to May","watering": "Weekly irrigation","fertilizer": "Potassium and nitrogen rich","pest_control": "Bt spray, neem oil","harvest": "150–180 days"},
        "mango": {"sowing_season": "July to August","watering": "Irrigate every 2–3 weeks","fertilizer": "NPK + FYM","pest_control": "Mango hopper control","harvest": "4–5 months from flowering"},
        "banana": {"sowing_season": "April to May","watering": "Twice a week","fertilizer": "Potassium-rich mix","pest_control": "Spray monocrotophos","harvest": "11–12 months"},
        "coffee": {"sowing_season": "June to August","watering": "Irrigate at dry spell","fertilizer": "NPK + compost","pest_control": "Spray copper oxychloride","harvest": "9–11 months"}
    }
    return tips_dict.get(crop_name.lower(), {})

# ✅ Suggest top crops
def get_top_matching_crops(user_input: list, top_n=5):
    if crop_df_scaled.empty:
        return []

    # Ensure proper DataFrame input
    input_df = pd.DataFrame([user_input], columns=feature_cols).fillna(0)
    input_scaled = scaler.transform(input_df)

    # Copy dataset so we don’t mutate the global DataFrame
    df_copy = crop_df_scaled.copy()

    data_scaled = df_copy[feature_cols].values
    distances = euclidean_distances(data_scaled, input_scaled).flatten()
    df_copy["distance"] = distances

    top_matches = df_copy.nsmallest(top_n, "distance")

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

