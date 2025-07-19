from fastapi import APIRouter, UploadFile, File
from PIL import Image
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import json
from pathlib import Path
import gdown
import os

MODEL_PATH = "backend/disease_model/plant_disease_model.pt"

if not os.path.exists(MODEL_PATH):
    print("Downloading model...")
    url = "https://drive.google.com/uc?id=YOUR_FILE_ID"
    gdown.download(url, MODEL_PATH, quiet=False)



router = APIRouter()

# 👇 1. Define the model architecture used in training
class PlantDiseaseModel(nn.Module):
    def __init__(self, num_classes=38):
        super(PlantDiseaseModel, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )
        self.fc = nn.Linear(32 * 56 * 56, num_classes)  # ✅ Not a Sequential

    def forward(self, x):
        x = self.conv(x)
        x = x.view(x.size(0), -1)  # Flatten
        x = self.fc(x)
        return x

# 👇 2. Load model with weights
model_path = Path(__file__).parent / "plant_disease_model.pt"
model = PlantDiseaseModel(num_classes=15)  # Set your actual number of classes
model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
model.eval()

# 👇 3. Load class labels
labels_path = Path(__file__).parent / "class_labels.json"
with open(labels_path) as f:
    class_labels = json.load(f)

# 👇 4. Image transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# 👇 5. Prediction endpoint
@router.post("/predict-disease")
async def predict_disease(file: UploadFile = File(...)):
    try:
        image = Image.open(file.file).convert("RGB")
        img_tensor = transform(image).unsqueeze(0)

        with torch.no_grad():
            output = model(img_tensor)
            predicted_idx = torch.argmax(output, dim=1).item()
            predicted_class = class_labels[str(predicted_idx)]

        return {"predicted_disease": predicted_class}
    except Exception as e:
        return {"error": str(e)}


def predict_image(image: Image.Image):
    img_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        output = model(img_tensor)
        predicted_idx = torch.argmax(output, dim=1).item()
        predicted_class = class_labels[str(predicted_idx)]

    return predicted_class

