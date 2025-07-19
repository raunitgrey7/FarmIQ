from fastapi import FastAPI, Request, UploadFile, File, Form, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from io import BytesIO
from PIL import Image
from fastapi import FastAPI
       
# ✅ Service Imports
from backend.services.predictor import get_crop_tips, get_top_matching_crops
from backend.disease_model.predict_disease import router as disease_router, predict_image
from backend.services.weather import get_weather_data

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


# ✅ Routers
app.include_router(disease_router)

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
        "Yellowing leaves": "🧪 Check nitrogen levels. Try using urea or compost.",
        "Wilting": "💧 Ensure proper watering. Avoid over-irrigation and check for root rot.",
        "Spots on leaves": "🦠 Possible fungal infection. Use neem spray or copper-based fungicides.",
        "Stunted growth": "🌱 Could be due to phosphorus deficiency. Use compost or DAP.",
        "Pest infestation": "🐛 Use natural insecticides or introduce pest predators like ladybugs."
    }

    tip = advice.get(issue, "Consult a local expert or agricultural extension officer.")

    return templates.TemplateResponse("problem.html", {
        "request": request,
        "tip": tip
    })

