import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import os

# ✅ Load dataset safely
DATA_PATH = "/backend/data/Crop_recommendation.csv"
MODEL_DIR = "/backend/model"

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"❌ CSV file not found at {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

# ✅ Split features and label
X = df.drop('label', axis=1)
y = df['label']

# ✅ Train-test split and scale features
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

# ✅ Train Random Forest model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)

# ✅ Create model folder and save model
os.makedirs(MODEL_DIR, exist_ok=True)

with open(os.path.join(MODEL_DIR, "crop_recommendation.pkl"), "wb") as f:
    pickle.dump(model, f)

with open(os.path.join(MODEL_DIR, "preprocessor.pkl"), "wb") as f:
    pickle.dump(scaler, f)

print("✅ Model and Preprocessor saved successfully to 'backend/model/'")
