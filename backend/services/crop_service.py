import os
import json
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import io

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
MODEL_DIR = os.path.join(PROJECT_ROOT, "models", "crop_disease_model")

MODEL_PATH = os.path.join(MODEL_DIR, "crop_disease_model.pth")
LABELS_PATH = os.path.join(MODEL_DIR, "crop_disease_class_labels.json")

class CropService:
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
                self.labels = {int(k): v for k, v in raw_labels.items()}

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
            print("Crop Disease Image Classification Model loaded successfully.")
        else:
            print("WARNING: Crop Disease Model weights missing!")

    def analyze_crop_image(self, image_bytes):
        if not self.model:
            self.load_model()
            if not self.model:
                return {"error": "Crop disease ML model unavailable."}

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            return {"error": "Invalid or corrupt plant image file. Please upload a clear image."}

        input_tensor = self.transform(image).unsqueeze(0)

        with torch.no_grad():
            outputs = self.model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)[0]
            top_prob, top_idx = torch.max(probabilities, dim=0)

        confidence = float(top_prob.item())
        predicted_class = self.labels.get(top_idx.item(), "Unknown_Condition")

        # Do not turn an uncertain or unsupported image into a disease diagnosis.
        if confidence < 0.40:
            supported_crops = sorted({
                label.split("_", 1)[0]
                for label in self.labels.values()
                if "_" in label
            })
            supported_crop_text = ", ".join(supported_crops)
            message = (
                "No reliable disease diagnosis is available. "
                f"This model supports disease classes for {supported_crop_text} only. "
            )
            if "onion" not in {crop_name.lower() for crop_name in supported_crops}:
                message += "Onion is not included in the model's trained crop classes. "
            message += (
                "A full-field image may not show leaf symptoms clearly; try a close-up "
                "image of a leaf from a supported crop. No disease or treatment "
                "recommendation is provided for this uncertain result."
            )
            return {
                "low_confidence": True,
                "message": message,
                "confidence_score": round(confidence * 100, 1)
            }

        # Format crop name and condition/disease
        parts = predicted_class.split("_")
        crop_name = parts[0]
        condition = " ".join(parts[1:])

        # Agricultural corrective treatment database derived from crop pathology dataset
        treatment_db = {
            "Tomato_Healthy": {
                "health_status": "Healthy",
                "recommended_action": "Maintain balanced nutrition and regular drip irrigation schedule.",
                "fertilizer": "NPK 19-19-19 (Foliar spray)",
                "pesticide": "None required (Preventative Neem oil spray recommended)",
                "organic_treatment": "Vermicompost top dressing",
                "severity": "None"
            },
            "Tomato_Early_Blight": {
                "health_status": "Fungal Infection (Alternaria solani)",
                "recommended_action": "Prune infected lower leaves immediately and avoid overhead watering.",
                "fertilizer": "Potassium Nitrate (KNO3) to build disease resistance",
                "pesticide": "Copper Oxychloride or Mancozeb spray",
                "organic_treatment": "Bio-fungicide Trichoderma viride or Neem cake soil application",
                "severity": "Moderate"
            },
            "Tomato_Late_Blight": {
                "health_status": "Severe Water-mold Infection (Phytophthora infestans)",
                "recommended_action": "Destroy severely blighted plant parts immediately and improve canopy aeration.",
                "fertilizer": "Calcium Nitrate + Micronutrient Spray",
                "pesticide": "Cymoxanil + Mancozeb or Metalaxyl spray",
                "organic_treatment": "Copper Hydroxide spray and Bacillus subtilis bio-pesticide",
                "severity": "High"
            },
            "Potato_Healthy": {
                "health_status": "Healthy",
                "recommended_action": "Maintain proper earthing-up and balanced soil moisture.",
                "fertilizer": "NPK 12-32-16",
                "pesticide": "None",
                "organic_treatment": "Organic Compost",
                "severity": "None"
            },
            "Potato_Early_Blight": {
                "health_status": "Fungal Spot Disease (Alternaria solani)",
                "recommended_action": "Remove dark target-spot leaves and maintain crop rotation.",
                "fertilizer": "High-Potassium Foliar Spray",
                "pesticide": "Propineb or Chlorothalonil fungicide",
                "organic_treatment": "Garlic extract + Neem oil solution",
                "severity": "Moderate"
            },
            "Potato_Late_Blight": {
                "health_status": "Destructive Blight (Phytophthora infestans)",
                "recommended_action": "Apply protective fungicide barrier immediately across crop field.",
                "fertilizer": "Potash (MOP) + Zinc Sulfate",
                "pesticide": "Dimethomorph or Metalaxyl-M fungicide",
                "organic_treatment": "Bordeaux mixture (1%) foliar spray",
                "severity": "High"
            },
            "Corn_Healthy": {
                "health_status": "Healthy",
                "recommended_action": "Continue split application of nitrogen during vegetative stage.",
                "fertilizer": "Urea (Top dressing)",
                "pesticide": "None",
                "organic_treatment": "Azospirillum Bio-fertilizer",
                "severity": "None"
            },
            "Corn_Common_Rust": {
                "health_status": "Fungal Rust Pustules (Puccinia sorghi)",
                "recommended_action": "Spray fungicides upon first appearance of pustules to protect upper leaves.",
                "fertilizer": "Balanced NPK + Micronutrient zinc",
                "pesticide": "Azoxystrobin or Tebuconazole fungicide",
                "organic_treatment": "Sulfur dust spray or Neem leaf solution",
                "severity": "Moderate"
            }
        }

        treatment = treatment_db.get(predicted_class, {
            "health_status": condition,
            "recommended_action": "Apply appropriate organic compost and inspect for localized pest issues.",
            "fertilizer": "NPK 19-19-19",
            "pesticide": "Neem Oil Spray",
            "organic_treatment": "Vermicompost & Bio-fertilizer",
            "severity": "Low"
        })

        return {
            "crop_name": crop_name,
            "condition": condition,
            "health_status": treatment["health_status"],
            "confidence_score": round(confidence * 100, 1),
            "severity_level": treatment["severity"],
            "recommended_action": treatment["recommended_action"],
            "recommended_fertilizer": treatment["fertilizer"],
            "recommended_pesticide": treatment["pesticide"],
            "organic_alternative": treatment["organic_treatment"],
            "disclaimer": "AI-generated results are advisory and may not replace professional agricultural diagnosis. Verify recommendations with a plant pathologist or agricultural expert."
        }

crop_service = CropService()
