# backend/disease_model/train_disease_model.py

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import os
import time
import json

# Define the model
class PlantDiseaseModel(nn.Module):
    def __init__(self, num_classes=38):
        super(PlantDiseaseModel, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )

        # Calculate the flattened feature size dynamically
        with torch.no_grad():
            dummy = torch.randn(1, 3, 224, 224)
            out = self.conv(dummy)
            self.flatten_size = out.view(1, -1).shape[1]

        self.fc = nn.Linear(self.flatten_size, num_classes)

    def forward(self, x):
        x = self.conv(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

# Dataset location: put images in dataset/{class_name}/image.jpg
data_dir = "dataset"  # make sure this folder exists and is filled with subfolders for each class

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

dataset = datasets.ImageFolder(root=data_dir, transform=transform)
dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

num_classes = len(dataset.classes)
print(f"Detected {num_classes} classes.")

model = PlantDiseaseModel(num_classes=num_classes)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training loop
for epoch in range(5):  # Increase to 10-20 later for better results
    start_time = time.time()
    ...
    print(f"🕒 Time taken for epoch {epoch+1}: {time.time() - start_time:.2f} seconds")
    model.train()
    total_loss = 0

    print(f"\n🔁 Epoch {epoch + 1}/5 started...")
    
    for batch_idx, (images, labels) in enumerate(dataloader):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

        # Print progress every 10 batches
        if (batch_idx + 1) % 10 == 0 or (batch_idx + 1) == len(dataloader):
            print(f"  ✅ Batch {batch_idx + 1}/{len(dataloader)} - Current Loss: {loss.item():.4f}")

    print(f"✅ Epoch {epoch + 1} complete! Total Loss: {total_loss:.4f}")

# Save the model
save_path = "backend/disease_model/plant_disease_model.pt"
torch.save(model.state_dict(), save_path)
print(f"Model saved at {save_path}")

# ✅ Save model after training
torch.save(model.state_dict(), "backend/disease_model/plant_disease_model.pt")
print("Model saved to backend/disease_model/plant_disease_model.pt")

label_map = dataset.class_to_idx  # e.g. {'Apple___Black_rot': 0, ...}
idx_to_class = {v: k for k, v in label_map.items()}  # reverse it

with open("backend/disease_model/class_labels.json", "w") as f:
    json.dump(idx_to_class, f)

print("Class labels saved to backend/disease_model/class_labels.json")
