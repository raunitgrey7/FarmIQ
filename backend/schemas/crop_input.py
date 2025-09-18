from pydantic import BaseModel

# ✅ Old input model (direct values)
class CropInput(BaseModel):
    nitrogen: float
    phosphorus: float
    potassium: float
    temperature: float
    humidity: float
    ph: float
    rainfall: float

# ✅ New input model (farmer-friendly)
class LocationInput(BaseModel):
    state: str
    district: str
    season: str
    temperature: float
