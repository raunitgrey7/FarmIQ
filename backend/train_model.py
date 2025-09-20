import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import os

from sklearn.ensemble import HistGradientBoostingClassifier

model = HistGradientBoostingClassifier(
    max_iter=100,     # number of boosting rounds
    max_depth=15,     # limit depth to control memory
    random_state=42
)



# ✅ Paths
DATA_PATH = "backend/data/all_crops.parquet"   # merged dataset
MODEL_DIR = "backend/model"

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"❌ Dataset not found at {DATA_PATH}")

# ✅ Load dataset
df = pd.read_parquet(DATA_PATH)
print(f"✅ Loaded dataset: {df.shape}")

df = pd.read_parquet("backend/data/all_crops.parquet")

# Rename columns to match feature_cols
df = df.rename(columns={
    "N_kg_ha": "N",
    "P_kg_ha": "P",
    "K_kg_ha": "K",
    "avg_temp_C": "temperature",
    "avg_rainfall_mm": "rainfall",
    "soil_ph": "ph",
    "crop": "label"   # if you're using crop as target
})

print("✅ Columns after renaming:", df.columns.tolist())

# ✅ Feature / label split
# Assumption: your dataset has columns ['N','P','K','temperature','humidity','ph','rainfall','label']
feature_cols = ['N', 'P', 'K', 'temperature', 'ph', 'rainfall']
label_col = 'label'
df_small = df.sample(n=300000, random_state=42)
X = df[feature_cols]
y = df[label_col]

# ✅ Train-test split & scaling
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

# ✅ Train Random Forest
model = HistGradientBoostingClassifier(max_iter=100, max_depth=15, random_state=42)
model.fit(X_train_scaled, y_train)

# ✅ Save model + scaler
os.makedirs(MODEL_DIR, exist_ok=True)

with open(os.path.join(MODEL_DIR, "crop_recommendation.pkl"), "wb") as f:
    pickle.dump(model, f)

with open(os.path.join(MODEL_DIR, "preprocessor.pkl"), "wb") as f:
    pickle.dump(scaler, f)

print("🎉 Model and Preprocessor saved successfully to 'backend/model/'")
