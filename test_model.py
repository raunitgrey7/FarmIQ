import pickle
import numpy as np

with open("backend/model/crop_recommendation.pkl", "rb") as f:
    model = pickle.load(f)

with open("backend/model/preprocessor.pkl", "rb") as f:
    scaler = pickle.load(f)

samples = [
    [90, 42, 43, 25.5, 80, 6.5, 200],  # rice or maize
    [10, 10, 10, 15.0, 20, 4.5, 50],   # possibly mustard or pulses
    [100, 100, 100, 35.0, 90, 7.5, 300],  # maybe sugarcane or jute
]

for i, sample in enumerate(samples, 1):
    scaled = scaler.transform([sample])
    pred = model.predict(scaled)
    print(f"Test Case {i}: {sample} -> 🌱 {pred[0]}")
