import json
import pandas as pd
import pickle
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import euclidean_distances

# ✅ Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = BASE_DIR / "backend" / "data" / "all_crops.parquet"

# ✅ Load dataset
try:
    crop_df = pd.read_parquet(DATA_PATH)
    print("✅ Loaded Parquet dataset:", crop_df.shape)
except FileNotFoundError:
    print("❌ Parquet dataset not found.")
    crop_df = pd.DataFrame()

# ✅ Column mapping: user input → dataset columns
# Order of user_input = [N, P, K, temperature, ph, rainfall]
feature_mapping = {
    "N": "N_kg_ha",
    "P": "P_kg_ha",
    "K": "K_kg_ha",
    "temperature": "avg_temp_C",
    "ph": "soil_ph",
    "rainfall": "avg_rainfall_mm"
}

# ✅ Build aligned feature list (dataset column names)
dataset_feature_cols = list(feature_mapping.values())
label_col = "crop"

# ✅ Initialize scaler and scale dataset
if not crop_df.empty:
    try:
        scaler = StandardScaler()
        crop_features = crop_df[dataset_feature_cols].fillna(0)
        scaled_values = scaler.fit_transform(crop_features)

        crop_df_scaled = crop_df.copy()
        crop_df_scaled[dataset_feature_cols] = scaled_values
    except Exception as e:
        print("❌ Failed to scale dataset:", e)
        scaler = StandardScaler()
        crop_df_scaled = pd.DataFrame(columns=dataset_feature_cols + [label_col])
else:
    scaler = StandardScaler()
    crop_df_scaled = pd.DataFrame(columns=dataset_feature_cols + [label_col])

print("✅ Columns after renaming:", crop_df.columns.tolist())


# ✅ Crop care tips
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
        "maize": {
            "sowing_season": "June to July",
            "watering": "Moderate irrigation at key stages",
            "fertilizer": "Nitrogen-rich fertilizers early",
            "pest_control": "Trichogramma for stem borers",
            "harvest": "90–100 days"
        },
        "cotton": {
            "sowing_season": "April to May",
            "watering": "Weekly irrigation",
            "fertilizer": "Potassium and nitrogen rich",
            "pest_control": "Bt spray, neem oil",
            "harvest": "150–180 days"
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
        "coffee": {
            "sowing_season": "June to August",
            "watering": "Irrigate at dry spell",
            "fertilizer": "NPK + compost",
            "pest_control": "Spray copper oxychloride",
            "harvest": "9–11 months"
        }
    }
    return tips_dict.get(crop_name.lower(), {})


# ✅ Suggest top crops
def get_top_matching_crops(user_input: list, top_n=5):
    if crop_df_scaled.empty:
        print("❌ Dataset empty")
        return []

    try:
        # Map user input → dataset column names
        input_dict = {
            "N_kg_ha": user_input[0],
            "P_kg_ha": user_input[1],
            "K_kg_ha": user_input[2],
            "avg_temp_C": user_input[3],
            "soil_ph": user_input[4],
            "avg_rainfall_mm": user_input[5]
        }
        print("🔍 User input mapped:", input_dict)

        input_df = pd.DataFrame([input_dict], columns=dataset_feature_cols).fillna(0)
        print("✅ Input DataFrame:", input_df.to_dict(orient="records"))

        input_scaled = scaler.transform(input_df)
        print("✅ Scaled input:", input_scaled)

        df_copy = crop_df_scaled.copy()
        data_scaled = df_copy[dataset_feature_cols].values
        distances = euclidean_distances(data_scaled, input_scaled).flatten()
        df_copy["distance"] = distances

        top_matches = df_copy.nsmallest(top_n, "distance")

        results = []
        for _, row in top_matches.iterrows():
            crop_name = row[label_col]
            tips = get_crop_tips(crop_name)
            results.append({
                "crop": crop_name,
                "similarity": round(100 - row["distance"] * 100, 2),
                "tips": tips
            })

        print("✅ Top results:", results)
        return results

    except Exception as e:
        print("❌ get_top_matching_crops error:", e)
        return []

