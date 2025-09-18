import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import os

# ✅ Paths
DATA_PATH = "backend/data/all_crops.parquet"   # merged dataset
MODEL_DIR = "backend/model"

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"❌ Dataset not found at {DATA_PATH}")

# ✅ Load dataset
df = pd.read_parquet(DATA_PATH)
print(f"✅ Loaded dataset: {df.shape}")

# ✅ Feature / label split
# Assumption: your dataset has columns ['N','P','K','temperature','humidity','ph','rainfall','label']
feature_cols = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
label_col = 'label'

X = df[feature_cols]
y = df[label_col]

# ✅ Train-test split & scaling
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

# ✅ Train Random Forest
model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
model.fit(X_train_scaled, y_train)

# ✅ Save model + scaler
os.makedirs(MODEL_DIR, exist_ok=True)

with open(os.path.join(MODEL_DIR, "crop_recommendation.pkl"), "wb") as f:
    pickle.dump(model, f)

with open(os.path.join(MODEL_DIR, "preprocessor.pkl"), "wb") as f:
    pickle.dump(scaler, f)

print("🎉 Model and Preprocessor saved successfully to 'backend/model/'")
