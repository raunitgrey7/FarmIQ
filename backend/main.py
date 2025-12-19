from fastapi import FastAPI, Request, UploadFile, File, Form, Body, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from io import BytesIO
from PIL import Image
import os
from uuid import uuid4
from datetime import datetime
import pandas as pd

# ✅ Service Imports
from backend.services.predictor import get_crop_tips, get_top_matching_crops
from backend.disease_model.predict_disease import router as disease_router, predict_image
from backend.services.weather import get_weather_data
# ✅ Community Imports
from backend.community import models as community_models
from backend.community import routes as community_routes
from backend.database.db import get_db

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Static & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.templates = templates

# ✅ Include Community & Disease Routes
app.include_router(disease_router)
app.include_router(community_routes.router)

# ✅ Create DB Tables
db = next(get_db())
community_models.Base.metadata.create_all(bind=db.bind)

# ✅ Load dataset for location lookup
PARQUET_PATH = "backend/data/all_crops.parquet"
if os.path.exists(PARQUET_PATH):
    try:
        district_df = pd.read_parquet(PARQUET_PATH)
        if "state" in district_df.columns:
            district_df["state"] = district_df["state"].astype(str).str.lower()
        if "district" in district_df.columns:
            district_df["district"] = district_df["district"].astype(str).str.lower()
        if "season" in district_df.columns:
            district_df["season"] = district_df["season"].astype(str).str.lower()
        print(f"✅ Loaded parquet for location lookup: {district_df.shape}")
    except Exception as e:
        print("⚠️ Failed to load parquet:", e)
        district_df = pd.DataFrame()
else:
    district_df = pd.DataFrame()
    print("⚠️ all_crops.parquet not found — location lookup disabled.")

def get_district_data(state: str, district: str, season: str, temperature: float):
    if district_df.empty:
        return None

    try:
        state_l = state.strip().lower()
        district_l = district.strip().lower()
        season_l = season.strip().lower()

        print(f"🔍 Looking for state={state}, district={district}, season={season}")
        rows = district_df[
            (district_df["state"] == state_l) &
            (district_df["district"] == district_l) &
            (district_df["season"] == season_l)
        ]

        if rows.empty:
            print("⚠️ No exact match found, trying fallback state+district only")
            rows = district_df[
                (district_df["state"] == state_l) &
                (district_df["district"] == district_l)
            ]

        if rows.empty:
            print("❌ Still no data found")
            return None

        row = rows.iloc[0]

        N = float(row.get("N", row.get("N_kg_ha", 0)))
        P = float(row.get("P", row.get("P_kg_ha", 0)))
        K = float(row.get("K", row.get("K_kg_ha", 0)))
        humidity = float(row.get("humidity", 0))  # not in dataset, keep fallback 0
        ph_val = float(row.get("ph", row.get("soil_ph", 0)))
        rainfall = float(row.get("rainfall", row.get("avg_rainfall_mm", 0)))

        return [N, P, K, float(temperature), ph_val, rainfall]
    except Exception as e:
        print("⚠️ get_district_data error:", e)
        return None

# ✅ Page Routes
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/home")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/crop")
def crop_page(request: Request):
    return templates.TemplateResponse("crop.html", {
        "request": request,
        "top_crops": None,
        "recommended_crop": None,
        "tips": None
    })

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse

@app.get("/market", response_class=HTMLResponse)
async def market_page(request: Request):
    return templates.TemplateResponse("market.html", {"request": request, "prices": None})

@app.post("/market", response_class=HTMLResponse)
async def get_market_data(request: Request, district: str = Form(...)):
    # Prototype Data for Saket/Delhi Presentation
    # Added "change" field here to fix the template error
    mock_data = [
        {"market": "Okhla Mandi", "commodity": "Tomato", "variety": "Desi", "min_price": 2800, "max_price": 3800, "modal_price": 3450, "date": "20 Dec 2024", "change": 8},
        {"market": "Mehrauli Mandi", "commodity": "Potato", "variety": "F.A.Q.", "min_price": 600, "max_price": 1200, "modal_price": 950, "date": "20 Dec 2024", "change": -2},
        {"market": "Okhla Mandi", "commodity": "Onion", "variety": "Red", "min_price": 4500, "max_price": 5500, "modal_price": 5100, "date": "20 Dec 2024", "change": 12},
        {"market": "Najafgarh", "commodity": "Wheat", "variety": "Dara", "min_price": 2300, "max_price": 2600, "modal_price": 2400, "date": "19 Dec 2024", "change": 4},
    ]
    
    # If the user enters anything related to Delhi, show the mock data
    prices = mock_data if "delhi" in district.lower() or "saket" in district.lower() else []

    return templates.TemplateResponse("market.html", {
        "request": request, 
        "prices": prices, 
        "district": district.title()
    })

@app.get("/soil", response_class=HTMLResponse)
def soil_page(request: Request):
    return templates.TemplateResponse("soil.html", {"request": request})

@app.get("/disease", response_class=HTMLResponse)
def disease_page(request: Request):
    return templates.TemplateResponse("disease.html", {"request": request})

@app.get("/weather", response_class=HTMLResponse)
def weather_page(request: Request):
    return templates.TemplateResponse("weather.html", {"request": request})

@app.get("/profit", response_class=HTMLResponse)
def profit_page(request: Request):
    return templates.TemplateResponse("profit.html", {"request": request})

@app.get("/instructions", response_class=HTMLResponse)
def instructions_page(request: Request):
    return templates.TemplateResponse("instructions.html", {"request": request})

@app.get("/community", response_class=HTMLResponse)
def community_page(request: Request):
    return templates.TemplateResponse("community.html", {"request": request})

@app.post("/crop", response_class=HTMLResponse)
async def predict_crop_form(
    request: Request,
    nitrogen: float = Form(...),
    phosphorus: float = Form(...),
    potassium: float = Form(...),
    temperature: float = Form(...),
    ph: float = Form(...),
    rainfall: float = Form(...)
):
    input_values = [nitrogen, phosphorus, potassium, temperature, ph, rainfall]
    top_crops = get_top_matching_crops(input_values)
    recommended_crop = top_crops[0]["crop"]
    tips = top_crops[0]["tips"]

    return templates.TemplateResponse("crop.html", {
        "request": request,
        "top_crops": top_crops,
        "recommended_crop": recommended_crop,
        "tips": tips
    })

# ✅ Crop Recommendation – JSON API Route
@app.post("/predict-json")
async def predict_crop_api(data: dict = Body(...)):
    try:
        input_values = [
            data["nitrogen"],
            data["phosphorus"],
            data["potassium"],
            data["temperature"],
            data["ph"],
            data["rainfall"]
        ]

        top_crops = get_top_matching_crops(input_values)
        recommended_crop = top_crops[0]["crop"]
        tips = top_crops[0]["tips"] or {}

        return {
            "recommended_crop": recommended_crop,
            "top_crops": [c["crop"] for c in top_crops],
            "tips": tips
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/predict")
async def predict_crop_alias(data: dict = Body(...)):
    return await predict_crop_api(data)

# ✅ New endpoint: Predict using location
@app.post("/predict-location")
async def predict_from_location(data: dict = Body(...)):
    try:
        state = str(data.get("state", "")).strip().lower()
        district = str(data.get("district", "")).strip().lower()
        season = str(data.get("season", "")).strip().lower()
        temperature = data.get("temperature")

        if not (state and district and season and (temperature is not None)):
            return JSONResponse(
                {"error": "Missing one of state / district / season / temperature"},
                status_code=400
            )

        input_values = get_district_data(state, district, season, temperature)
        if not input_values:
            return JSONResponse(
                {"error": f"No location data found for {state}-{district}-{season}"},
                status_code=404
            )

        top_crops = get_top_matching_crops(input_values)
        if not top_crops:
            return JSONResponse({"error": "No crops found"}, status_code=404)

        recommended_crop = top_crops[0]["crop"]
        tips = top_crops[0]["tips"]

        return {
            "recommended_crop": recommended_crop,
            "top_crops": top_crops,   # ✅ now contains [{crop, similarity, tips}, ...]
            "tips": tips
        }

    except Exception as e:
        print("❌ Error in /predict-location:", e)
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ✅ Locations API
@app.get("/locations")
async def get_locations(state: str = Query(None), district: str = Query(None)):
    if district_df.empty:
        return JSONResponse({"error": "No dataset loaded"}, status_code=500)

    try:
        if state is None and district is None:
            states = sorted(district_df["state"].dropna().unique().tolist())
            return {"states": states}

        if state is not None and district is None:
            districts = sorted(
                district_df[district_df["state"] == state.lower()]["district"].dropna().unique().tolist()
            )
            return {"districts": districts}

        if district is not None:
            seasons = sorted(
                district_df[district_df["district"] == district.lower()]["season"].dropna().unique().tolist()
            )
            return {"seasons": seasons}

        return {}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ✅ Updated Soil Type Prediction with Guided Field Test
@app.post("/predict_soil", response_class=HTMLResponse)
async def predict_soil(
    request: Request,
    ball: str = Form(...),
    ribbon: str = Form(...),
    texture: str = Form(...)
):
    # Get soil type from field test
    soil_type_usda, approx_percentages = get_soil_type_by_test(ball, ribbon, texture)
    
    # Map to Indian context
    soil_mapping = get_indian_soil_mapping(soil_type_usda)
    
    # Get crop recommendations
    crop_recommendations = recommend_crop_by_soil(soil_type_usda)
    
    # Get management tips
    management_tips = get_management_tips(soil_type_usda)
    
    return templates.TemplateResponse("soil.html", {
        "request": request,
        "soil_type_usda": soil_type_usda,
        "soil_type_local": soil_mapping["local_name"],
        "soil_description": soil_mapping["description"],
        "soil_class": soil_mapping["class"],
        "sand": approx_percentages["sand"],
        "silt": approx_percentages["silt"],
        "clay": approx_percentages["clay"],
        "kharif_crops": crop_recommendations["kharif"],
        "rabi_crops": crop_recommendations["rabi"],
        "management_tips": management_tips
    })

# ✅ Soil Test Logic (USDA Feel Method)
def get_soil_type_by_test(ball: str, ribbon: str, texture: str):
    """
    Determine soil type based on USDA feel test
    Returns: (USDA soil type, approximate percentages)
    """
    # Decision tree based on USDA field test
    if ball == "no":
        return "Sandy", {"sand": 85, "silt": 10, "clay": 5}
    
    # If ball forms, check ribbon length
    if ribbon == "none":
        if texture == "gritty":
            return "Sandy Loam", {"sand": 65, "silt": 20, "clay": 15}
        elif texture == "smooth":
            return "Silty Loam", {"sand": 25, "silt": 60, "clay": 15}
        else:  # sticky
            return "Clay Loam", {"sand": 30, "silt": 20, "clay": 50}
    
    elif ribbon == "short":
        if texture == "gritty":
            return "Sandy Clay Loam", {"sand": 55, "silt": 15, "clay": 30}
        elif texture == "smooth":
            return "Silty Clay Loam", {"sand": 10, "silt": 55, "clay": 35}
        else:  # sticky
            return "Clay Loam", {"sand": 30, "silt": 20, "clay": 50}
    
    elif ribbon == "medium":
        if texture == "gritty":
            return "Sandy Clay", {"sand": 45, "silt": 10, "clay": 45}
        elif texture == "smooth":
            return "Silty Clay", {"sand": 10, "silt": 45, "clay": 45}
        else:  # sticky
            return "Clay", {"sand": 20, "silt": 20, "clay": 60}
    
    else:  # long ribbon
        if texture == "smooth":
            return "Silty Clay", {"sand": 10, "silt": 45, "clay": 45}
        else:  # sticky or gritty
            return "Clay", {"sand": 20, "silt": 20, "clay": 60}

# ✅ Map USDA types to Indian context
def get_indian_soil_mapping(usda_type: str):
    mapping = {
        "Sandy": {
            "local_name": "Sandy Soil (Desert Soil)",
            "description": "Light, quick-draining soil. Low water retention, fertilizers wash out quickly.",
            "class": "sandy"
        },
        "Sandy Loam": {
            "local_name": "Sandy Loam Soil",
            "description": "Balanced soil with good drainage. Excellent for root vegetables and fruits.",
            "class": "sandy"
        },
        "Loam": {
            "local_name": "Loam Soil (Fertile)",
            "description": "Ideal agricultural soil. Excellent nutrient and moisture retention capacity.",
            "class": "loamy"
        },
        "Silty Loam": {
            "local_name": "Silty Loam",
            "description": "Soft and smooth soil. Good moisture retention, moderate aeration.",
            "class": "silty"
        },
        "Clay Loam": {
            "local_name": "Clay Loam Soil",
            "description": "Heavy soil with good moisture retention. Suitable for wheat and paddy.",
            "class": "clayey"
        },
        "Sandy Clay Loam": {
            "local_name": "Sandy Clay Loam",
            "description": "Medium-heavy soil. Mixture of sandy and clay characteristics.",
            "class": "clayey"
        },
        "Silty Clay Loam": {
            "local_name": "Silty Clay Loam",
            "description": "Heavy and sticky soil. Retains moisture for long periods.",
            "class": "clayey"
        },
        "Clay": {
            "local_name": "Black Soil (Cotton Soil)",
            "description": "Heavy, sticky soil. Develops cracks in summer. Famous for cotton cultivation.",
            "class": "clayey"
        },
        "Silty Clay": {
            "local_name": "Silty Black Soil",
            "description": "Very heavy soil with excellent moisture retention. Requires drainage management.",
            "class": "clayey"
        },
        "Sandy Clay": {
            "local_name": "Sandy Black Soil",
            "description": "Mixture of black and sandy soil. Moderate water retention capacity.",
            "class": "clayey"
        }
    }
    return mapping.get(usda_type, {
        "local_name": "Mixed Soil",
        "description": "Combination of different soil types",
        "class": "loamy"
    })

# ✅ Crop Recommendations for Indian Context
def recommend_crop_by_soil(soil_type: str):
    """
    Returns crop recommendations for Kharif and Rabi seasons
    """
    crop_map = {
        "Sandy": {
            "kharif": "Pearl Millet (Bajra), Groundnut, Pigeon Pea, Cluster Beans",
            "rabi": "Chickpea, Mustard, Barley, Peas"
        },
        "Sandy Loam": {
            "kharif": "Maize, Green Gram, Black Gram, Sesame",
            "rabi": "Wheat, Chickpea, Mustard, Flaxseed"
        },
        "Loam": {
            "kharif": "Paddy, Maize, Soybean, Cotton",
            "rabi": "Wheat, Chickpea, Mustard, Potato"
        },
        "Silty Loam": {
            "kharif": "Paddy, Pulses, Vegetables",
            "rabi": "Wheat, Chickpea, Lentil, Onion"
        },
        "Clay Loam": {
            "kharif": "Paddy, Cotton, Soybean",
            "rabi": "Wheat, Chickpea, Mustard, Lentil"
        },
        "Sandy Clay Loam": {
            "kharif": "Cotton, Groundnut, Pigeon Pea",
            "rabi": "Wheat, Barley, Chickpea, Mustard"
        },
        "Silty Clay Loam": {
            "kharif": "Paddy, Jute, Soybean",
            "rabi": "Wheat, Lentil, Chickpea, Spinach"
        },
        "Clay": {
            "kharif": "Cotton, Soybean, Paddy, Sugarcane",
            "rabi": "Wheat, Chickpea, Mustard, Barley"
        },
        "Silty Clay": {
            "kharif": "Paddy, Pulses, Vegetables",
            "rabi": "Wheat, Chickpea, Lentil, Radish"
        },
        "Sandy Clay": {
            "kharif": "Cotton, Groundnut, Sesame",
            "rabi": "Wheat, Chickpea, Barley, Mustard"
        }
    }
    return crop_map.get(soil_type, {
        "kharif": "Various crops can be cultivated",
        "rabi": "Various crops can be cultivated"
    })

# ✅ Soil Management Tips
def get_management_tips(soil_type: str):
    tips_map = {
        "Sandy": [
            "Use organic manure (compost) generously",
            "Adopt drip irrigation system",
            "Include leguminous crops in crop rotation",
            "Practice mulching to retain moisture"
        ],
        "Clay": [
            "Allow soil to dry after plowing",
            "Add organic matter (straw, compost)",
            "Practice raised bed cultivation",
            "Deep plowing for better aeration"
        ],
        "Loam": [
            "Regular application of organic manure",
            "Follow crop rotation practices",
            "Use balanced fertilizers",
            "Maintain soil fertility levels"
        ],
        "Silty": [
            "Plant cover crops (like green gram)",
            "Avoid over-irrigation",
            "Increase use of organic materials",
            "Cultivate on leveled land"
        ]
    }
    
    # Determine general soil category
    if "Sandy" in soil_type:
        return tips_map["Sandy"]
    elif "Clay" in soil_type:
        return tips_map["Clay"]
    elif "Silt" in soil_type:
        return tips_map["Silty"]
    else:
        return tips_map["Loam"]

# ✅ Disease Detection
@app.get("/detect-disease-ui", response_class=HTMLResponse)
async def disease_ui(request: Request):
    return templates.TemplateResponse("disease_detect.html", {"request": request})

@app.post("/detect_disease")
async def detect_disease(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")
        label = predict_image(image)
        return {"disease": label}
    except Exception as e:
        return {"error": str(e)}

# ✅ Weather API
@app.get("/test-weather")
async def test_weather():
    result = await get_weather_data(28.6139, 77.2090)  # Delhi test
    return JSONResponse(content=result)

@app.post("/weather")
async def get_weather(request: Request):
    try:
        data = await request.json()
        lat = data.get("lat")
        lon = data.get("lon")
        if not lat or not lon:
            return JSONResponse({"error": "Latitude or longitude missing"}, status_code=400)

        result = await get_weather_data(lat, lon)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

