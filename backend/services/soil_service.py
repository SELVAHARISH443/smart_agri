import os
import json
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import io

from .fertilizer_service import fertilizer_service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
MODEL_DIR = os.path.join(PROJECT_ROOT, "models", "soil_model")

MODEL_PATH = os.path.join(MODEL_DIR, "soil_model.pth")
LABELS_PATH = os.path.join(MODEL_DIR, "soil_class_labels.json")

class SoilService:
    def __init__(self):
        self.model = None
        self.labels = {}
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        self.load_model()

    def load_model(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(LABELS_PATH):
            with open(LABELS_PATH, "r") as f:
                raw_labels = json.load(f)
                self.labels = {int(k): v.replace("_", " ") for k, v in raw_labels.items()}

            num_classes = len(self.labels)
            model = models.mobilenet_v2(weights=None)
            in_features = model.classifier[1].in_features
            model.classifier = nn.Sequential(
                nn.Dropout(0.3),
                nn.Linear(in_features, 128),
                nn.ReLU(),
                nn.Linear(128, num_classes)
            )
            model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
            model.eval()
            self.model = model
            print("Soil Image Classification Model loaded successfully.")
        else:
            print("WARNING: Soil Model weights or labels missing!")

    def analyze_soil_image(self, image_bytes, crop=None, N=None, P=None, K=None, pH=None):
        if not self.model:
            self.load_model()
            if not self.model:
                return {"error": "Soil ML model not loaded."}

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            return {"error": "Invalid or unreadable image file. Please upload a valid soil image."}

        input_tensor = self.transform(image).unsqueeze(0)

        with torch.no_grad():
            outputs = self.model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)[0]
            top_prob, top_idx = torch.max(probabilities, dim=0)

        confidence = float(top_prob.item())
        predicted_soil_type = self.labels.get(top_idx.item(), "Unknown Soil")

        top_predictions = [
            {
                "soil_type": self.labels.get(i, "Unknown Soil"),
                "confidence_score": round(float(prob.item()) * 100, 1)
            }
            for i, prob in enumerate(probabilities)
        ]
        top_predictions.sort(key=lambda item: item["confidence_score"], reverse=True)

        soil_profile_db = {
            "Black Soil": {"health_status": "Highly Fertile", "moisture_retention": "Very High", "organic_matter": 2.8, "default_pH": 7.5, "default_N": 65, "default_P": 45, "default_K": 55},
            "Red Soil": {"health_status": "Moderately Fertile", "moisture_retention": "Medium-Low", "organic_matter": 1.4, "default_pH": 6.2, "default_N": 40, "default_P": 30, "default_K": 35},
            "Sandy Soil": {"health_status": "Nutrient Deficient", "moisture_retention": "Low", "organic_matter": 0.8, "default_pH": 6.8, "default_N": 25, "default_P": 20, "default_K": 20},
            "Clay Soil": {"health_status": "Nutrient Rich", "moisture_retention": "Very High", "organic_matter": 2.2, "default_pH": 7.2, "default_N": 60, "default_P": 40, "default_K": 45},
            "Loamy Soil": {"health_status": "Optimal Fertility", "moisture_retention": "High", "organic_matter": 3.2, "default_pH": 6.6, "default_N": 75, "default_P": 50, "default_K": 50},
            "Laterite Soil": {"health_status": "Acidic / Leached", "moisture_retention": "Low", "organic_matter": 1.1, "default_pH": 5.2, "default_N": 35, "default_P": 25, "default_K": 30},
        }

        suitable_plants_db = {
            "Black Soil": ["Rice", "Wheat", "Cotton", "Sugarcane", "Groundnut"],
            "Red Soil": ["Millet", "Groundnut", "Pulses", "Sorghum", "Sunflower"],
            "Sandy Soil": ["Millet", "Groundnut", "Sorghum", "Cucumber", "Barley"],
            "Clay Soil": ["Rice", "Paddy", "Wheat", "Soybean", "Cotton"],
            "Loamy Soil": ["Rice", "Tomato", "Potato", "Maize", "Onion"],
            "Laterite Soil": ["Groundnut", "Pulses", "Millet", "Cashew", "Sunflower"],
        }

        profile = soil_profile_db.get(predicted_soil_type, {
            "health_status": "Standard Soil", "moisture_retention": "Medium", "organic_matter": 1.8, "default_pH": 6.5, "default_N": 50, "default_P": 35, "default_K": 35
        })
        suitable_plants = suitable_plants_db.get(predicted_soil_type, ["Rice", "Wheat", "Maize", "Groundnut"])

        final_crop = crop if crop and crop.strip() else "Rice"
        final_N = float(N) if N is not None and str(N).strip() != "" else profile["default_N"]
        final_P = float(P) if P is not None and str(P).strip() != "" else profile["default_P"]
        final_K = float(K) if K is not None and str(K).strip() != "" else profile["default_K"]
        final_pH = float(pH) if pH is not None and str(pH).strip() != "" else profile["default_pH"]

        is_advisory = (N is None and P is None and K is None and pH is None)

        fert_result = fertilizer_service.recommend(
            soil_type=predicted_soil_type,
            crop=final_crop,
            N=final_N,
            P=final_P,
            K=final_K,
            pH=final_pH,
            organic_matter=profile["organic_matter"]
        )

        low_confidence = confidence < 0.40
        message = (
            "Prediction is below 40% confidence, but the model output is still shown for review. A clearer soil image may improve classification."
            if low_confidence else
            "Model prediction generated using the trained soil classification model."
        )

        return {
            "predicted_soil_type": predicted_soil_type,
            "confidence_score": round(confidence * 100, 1),
            "low_confidence": low_confidence,
            "message": message,
            "top_predictions": top_predictions[:3],
            "suitable_plants": suitable_plants,
            "soil_health_status": profile["health_status"],
            "moisture_retention": profile["moisture_retention"],
            "organic_matter_pct": profile["organic_matter"],
            "is_advisory_result": is_advisory,
            "inputs_used": {
                "crop": final_crop,
                "nitrogen": final_N,
                "phosphorus": final_P,
                "potassium": final_K,
                "pH": final_pH
            },
            "fertilizer_recommendation": fert_result,
            "disclaimer": "AI-generated results are advisory and may not replace professional soil testing or agricultural diagnosis. For fertilizer or crop protection decisions, verify the recommendation with a qualified agricultural expert."
        }

soil_service = SoilService()
