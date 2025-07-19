from fastapi import FastAPI, Request, UploadFile, File, Form, Body, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from io import BytesIO
from PIL import Image
import os
from uuid import uuid4
from datetime import datetime
import humanize
# ✅ Service Imports
from backend.services.predictor import get_crop_tips, get_top_matching_crops
from backend.disease_model.predict_disease import router as disease_router, predict_image
from backend.services.weather import get_weather_data
# ✅ Community Imports
from backend.community import models as community_models
from backend.community import routes as community_routes  # ✅ Importing the router
from backend.database.db import get_db


from sqlalchemy.orm import Session
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
app.templates = templates  # Required for community templates

# ✅ Include Community & Disease Routes
app.include_router(disease_router)
app.include_router(community_routes.router)  # ✅ This enables /community/delete/{id}

# ✅ Create DB Tables
db = next(get_db())
community_models.Base.metadata.create_all(bind=db.bind)




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

@app.post("/crop", response_class=HTMLResponse)
async def predict_crop_form(
    request: Request,
    nitrogen: float = Form(...),
    phosphorus: float = Form(...),
    potassium: float = Form(...),
    temperature: float = Form(...),
    humidity: float = Form(...),
    ph: float = Form(...),
    rainfall: float = Form(...)
):
    input_values = [nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall]
    top_crops = get_top_matching_crops(input_values)
    recommended_crop = top_crops[0]["crop"]
    tips = top_crops[0]["tips"]

    return templates.TemplateResponse("crop.html", {
        "request": request,
        "top_crops": top_crops,
        "recommended_crop": recommended_crop,
        "tips": tips
    })

@app.get("/soil")
def soil_page(request: Request):
    return templates.TemplateResponse("soil.html", {
        "request": request,
        "soil_type": None,
        "recommended_crop": None,
        "recommendation_description": None,
        "sand": None,
        "silt": None,
        "clay": None
    })

@app.get("/disease")
def disease_page(request: Request):
    return templates.TemplateResponse("disease.html", {"request": request})

@app.get("/instructions")
def instruction_page(request: Request):
    return templates.TemplateResponse("instructions.html", {"request": request})

@app.get("/weather")
def weather_page(request: Request):
    return templates.TemplateResponse("weather.html", {"request": request})

@app.get("/profit")
def profit_page(request: Request):
    return templates.TemplateResponse("profit.html", {"request": request})

@app.get("/problem")
def problems_page(request: Request):
    return templates.TemplateResponse("problem.html", {"request": request})

# ✅ Crop Recommendation – JSON API Route (Used by JS)
@app.post("/predict-json")
async def predict_crop_api(data: dict = Body(...)):
    try:
        input_values = [
            data["nitrogen"],
            data["phosphorus"],
            data["potassium"],
            data["temperature"],
            data["humidity"],
            data["ph"],
            data["rainfall"]
        ]

        top_crops = get_top_matching_crops(input_values)
        recommended_crop = top_crops[0]["crop"]
        tips = top_crops[0]["tips"] or {}

        return {
            "recommended_crop": recommended_crop,
            "tips": tips
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ✅ Duplicate for JS compatibility
@app.post("/predict")
async def predict_crop_alias(data: dict = Body(...)):
    return await predict_crop_api(data)

# ✅ Soil Type Prediction + Recommendation
@app.post("/predict_soil", response_class=HTMLResponse)
async def predict_soil(request: Request, sand: float = Form(...), silt: float = Form(...), clay: float = Form(...)):
    soil_type = get_soil_type(sand, silt, clay)
    recommended_crop, description = recommend_crop_by_soil(soil_type)

    return templates.TemplateResponse("soil.html", {
        "request": request,
        "soil_type": soil_type,
        "recommended_crop": recommended_crop,
        "recommendation_description": description,
        "sand": sand,
        "silt": silt,
        "clay": clay
    })

# ✅ Soil Logic
def get_soil_type(sand, silt, clay):
    if sand > silt and sand > clay:
        return "Sandy"
    elif clay > sand and clay > silt:
        return "Clayey"
    elif silt > sand and silt > clay:
        return "Silty"
    else:
        return "Loamy"

def recommend_crop_by_soil(soil_type: str):
    soil_crop_map = {
        "Sandy": ("Carrots", "Sandy soil drains quickly and suits root crops like carrots."),
        "Clayey": ("Rice", "Clayey soil retains water and is good for rice."),
        "Silty": ("Lettuce", "Silty soil holds moisture and is great for leafy vegetables like lettuce."),
        "Loamy": ("Wheat", "Loamy soil is balanced and supports cereals like wheat."),
    }
    return soil_crop_map.get(soil_type, ("Maize", "Suitable for a variety of crops including maize."))

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

# ✅ Crop Problem Detection (Form POST)
@app.post("/detect_problem")
async def detect_problem(request: Request, issue: str = Form(...)):
    advice = {
        "Yellowing leaves": (
            "🧪 <strong>Cause:</strong> Most commonly due to nitrogen deficiency or poor nutrient absorption.<br>"
            "<strong>Symptoms:</strong> Older leaves turn pale yellow while veins may remain green. Growth slows down.<br>"
            "<strong>Solution:</strong> Apply nitrogen-rich fertilizers like urea or well-rotted compost. Ensure soil pH is between 6.0–7.0. "
            "Use foliar sprays for faster results. Avoid overwatering, which can leach nutrients."
        ),
        "Wilting": (
            "💧 <strong>Cause:</strong> Water imbalance — either underwatering, overwatering, or root damage from pathogens like Fusarium or Pythium.<br>"
            "<strong>Symptoms:</strong> Leaves droop, especially during the day. In severe cases, plants collapse.<br>"
            "<strong>Solution:</strong> Check soil moisture. Water only when the top 2–3 cm of soil feels dry. "
            "If roots are rotting, remove affected plants and treat soil with fungicides. Improve drainage with sand or raised beds."
        ),
        "Spots on leaves": (
            "🦠 <strong>Cause:</strong> Fungal (e.g. leaf spot, anthracnose) or bacterial infections due to high humidity and poor airflow.<br>"
            "<strong>Symptoms:</strong> Brown, black, or yellow spots on leaf surface, often with halos or concentric rings.<br>"
            "<strong>Solution:</strong> Remove infected leaves. Apply copper-based fungicides or neem oil weekly. "
            "Water early in the morning to reduce leaf wetness. Avoid overcrowding and ensure good air circulation."
        ),
        "Stunted growth": (
            "🌱 <strong>Cause:</strong> Nutrient deficiencies (phosphorus, potassium), pest infestations, or compacted soil.<br>"
            "<strong>Symptoms:</strong> Plants remain small, with pale or discolored leaves and reduced yield.<br>"
            "<strong>Solution:</strong> Use DAP or compost for phosphorus. Check root zone for nematodes or aphids. "
            "Loosen soil before planting and rotate crops annually to improve soil health."
        ),
        "Pest infestation": (
            "🐛 <strong>Cause:</strong> Attack by aphids, caterpillars, borers, or mites that feed on plant sap or tissue.<br>"
            "<strong>Symptoms:</strong> Holes in leaves, sticky residue (honeydew), webbing, or visible insects.<br>"
            "<strong>Solution:</strong> Use neem oil or organic insecticides every 7–10 days. "
            "Introduce natural enemies like ladybugs or parasitic wasps. Remove weeds and infected debris regularly."
        ),
        "Leaf curling": (
            "🔍 <strong>Cause:</strong> Viral diseases, aphids, or boron deficiency can cause distorted leaves.<br>"
            "<strong>Symptoms:</strong> Leaves curl inward or twist, with discoloration or brittleness.<br>"
            "<strong>Solution:</strong> Remove and destroy infected parts. Apply neem oil for insects. "
            "Use virus-resistant seed varieties and maintain field hygiene. Add boron supplements if soil test confirms deficiency."
        ),
        "Root rot": (
            "🚱 <strong>Cause:</strong> Caused by waterlogging and fungi like Rhizoctonia or Pythium.<br>"
            "<strong>Symptoms:</strong> Yellowing leaves, mushy roots, foul smell from soil, and plant toppling.<br>"
            "<strong>Solution:</strong> Improve drainage and avoid excess watering. Use Trichoderma or fungicide-treated seeds. "
            "Grow crops on raised beds or ridges during monsoon."
        ),
        "Powdery mildew": (
            "🍶 <strong>Cause:</strong> Fungal infection due to dry days and humid nights.<br>"
            "<strong>Symptoms:</strong> White powdery coating on leaves, stems, or buds that spreads fast.<br>"
            "<strong>Solution:</strong> Mix 1 tablespoon baking soda + 1 tsp liquid soap in 1 liter of water and spray weekly. "
            "Alternatively, use sulfur-based fungicides. Remove infected leaves and ensure adequate spacing."
        ),
        "Fruit drop": (
            "🌡️ <strong>Cause:</strong> Sudden temperature shifts, moisture stress, and over-fertilization with nitrogen.<br>"
            "<strong>Symptoms:</strong> Immature fruits fall off before ripening. Flowers may also drop.<br>"
            "<strong>Solution:</strong> Maintain consistent soil moisture. Mulch soil to prevent evaporation. "
            "Avoid excess nitrogen during flowering. Use borax if boron deficiency is suspected."
        ),
        "Discoloration of stem": (
            "🧫 <strong>Cause:</strong> Bacterial or fungal stem infections (like wilt or blight), or nutrient deficiencies.<br>"
            "<strong>Symptoms:</strong> Brown or black streaks on stem, oozing sap, wilting above the infection point.<br>"
            "<strong>Solution:</strong> Prune infected stems. Disinfect tools after use. "
            "Apply Bordeaux mixture or systemic fungicides. Practice crop rotation and proper spacing."
        ),
        "Holes in leaves": (
            "🐞 <strong>Cause:</strong> Insect feeding by beetles, loopers, caterpillars, or grasshoppers.<br>"
            "<strong>Symptoms:</strong> Irregular holes or notches in leaves, especially near edges.<br>"
            "<strong>Solution:</strong> Inspect plants early morning. Hand-pick pests. Spray neem, garlic-chili solution, or bio-pesticides. "
            "Install pheromone or light traps to monitor and reduce pest numbers."
        ),
        "Cracked fruits": (
            "🌧️ <strong>Cause:</strong> Irregular watering — especially sudden rainfall after dry spells.<br>"
            "<strong>Symptoms:</strong> Visible cracks in ripening fruits (like tomatoes, pomegranates).<br>"
            "<strong>Solution:</strong> Water plants evenly. Use mulch to retain consistent moisture. "
            "Pick mature fruits early. Grow crack-resistant varieties when possible."
        ),
        "Flower drop": (
            "🌬️ <strong>Cause:</strong> Environmental stress (heat, wind), nutrient imbalance, or pollination failure.<br>"
            "<strong>Symptoms:</strong> Flowers fall off without forming fruits.<br>"
            "<strong>Solution:</strong> Provide shade nets during extreme heat. Avoid overuse of nitrogen. "
            "Encourage bees or pollinate manually by shaking flowers gently in morning hours."
        ),
        "Leaf burn": (
            "🔥 <strong>Cause:</strong> Fertilizer burn or sun scorch.<br>"
            "<strong>Symptoms:</strong> Brown or scorched edges on leaves, sometimes entire leaf dies off.<br>"
            "<strong>Solution:</strong> Flush soil with clean water if over-fertilized. Move pots or use shade net to reduce sunlight. "
            "Use slow-release fertilizers and avoid midday watering on leaves."
        ),
        "Mold on soil": (
            "🌫️ <strong>Cause:</strong> Excessive humidity, poor air circulation, and overwatering.<br>"
            "<strong>Symptoms:</strong> White or gray fuzzy growth on soil surface.<br>"
            "<strong>Solution:</strong> Scrape off mold, reduce watering, and increase sunlight exposure. "
            "Mix dry compost or cinnamon in topsoil. Ensure pots or beds have drainage holes."
        )
    }

    tip = advice.get(issue, "📌 <strong>No specific advice found.</strong> Please consult a local expert or agricultural extension officer.")

    return templates.TemplateResponse("problem.html", {
        "request": request,
        "tip": tip
    })


