import os
import joblib
import pandas as pd
import numpy as np

from .lazy_resource import LazyResource

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
MODEL_DIR = os.path.join(PROJECT_ROOT, "models", "fertilizer_model")

MODEL_PATH = os.path.join(MODEL_DIR, "fertilizer_model.pkl")
ENCODERS_PATH = os.path.join(MODEL_DIR, "label_encoders.pkl")

class FertilizerService:
    def __init__(self):
        self.model = None
        self.encoders = None
        self._model_resource = LazyResource("fertilizer recommendation model")

    def load_model(self):
        def initialize():
            if not os.path.isfile(MODEL_PATH):
                raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
            if not os.path.isfile(ENCODERS_PATH):
                raise FileNotFoundError(f"Label encoders not found: {ENCODERS_PATH}")

            model = joblib.load(MODEL_PATH)
            encoders = joblib.load(ENCODERS_PATH)
            if not isinstance(encoders, dict):
                raise ValueError(f"Invalid label encoders in {ENCODERS_PATH}")

            self.model = model
            self.encoders = encoders
            print("Fertilizer Recommendation Model loaded successfully.")
            return model, encoders

        self.model, self.encoders = self._model_resource.get(initialize)

    @property
    def initialization_status(self):
        return self._model_resource.status

    def recommend(self, soil_type, crop="Rice", N=50, P=40, K=35, pH=6.5, organic_matter=2.0, moisture=45, temperature=28, season="Kharif"):
        self.load_model()

        # Safe encoding helper
        def safe_encode(encoder, val, default_idx=0):
            val_str = str(val).strip()
            if val_str in encoder.classes_:
                return encoder.transform([val_str])[0]
            # Try case-insensitive lookup
            for i, cls in enumerate(encoder.classes_):
                if cls.lower() == val_str.lower():
                    return i
            return default_idx

        soil_encoded = safe_encode(self.encoders["soil_type"], soil_type)
        crop_encoded = safe_encode(self.encoders["crop"], crop)
        season_encoded = safe_encode(self.encoders["season"], season)

        features = np.array([[soil_encoded, crop_encoded, float(N), float(P), float(K), float(pH), float(organic_matter), float(moisture), float(temperature), season_encoded]])

        pred_idx = self.model.predict(features)[0]
        probs = self.model.predict_proba(features)[0]
        confidence = float(probs[pred_idx])

        fertilizer_name = self.encoders["recommended_fertilizer"].inverse_transform([pred_idx])[0]

        # Contextual agronomic guidance details learned from dataset
        guidance = {
            "Urea": {
                "dosage": "90 - 110 kg/hectare",
                "method": "Split application (Basal + Top Dressing during tillering)",
                "timing": "Early morning after light irrigation",
                "organic_alternative": "Neem-Coated Vermicompost or Azolla Bio-fertilizer",
                "reason": f"High nitrogen requirement identified for {crop} in {soil_type} with current N level ({N} mg/kg)."
            },
            "DAP": {
                "dosage": "75 - 90 kg/hectare",
                "method": "Band placement near seed line during sowing",
                "timing": "At the time of land preparation/sowing",
                "organic_alternative": "Bone Meal & Organic Compost",
                "reason": f"Phosphorus deficiency correction required for root development in {soil_type}."
            },
            "NPK 19-19-19": {
                "dosage": "80 - 100 kg/hectare",
                "method": "Foliar spray or soil application near root zone",
                "timing": "Vegetative stage and early flowering",
                "organic_alternative": "Enriched Panchagavya or Organic NPK Blend",
                "reason": f"Balanced primary nutrient boost (N-P-K) optimal for {crop} grown in {soil_type}."
            },
            "MOP (Muriate of Potash)": {
                "dosage": "50 - 65 kg/hectare",
                "method": "Soil incorporate before flowering/grain filling",
                "timing": "Pre-flowering stage",
                "organic_alternative": "Wood Ash & Seaweed Extract",
                "reason": f"Potassium reinforcement needed to enhance stress tolerance and yield quality in {soil_type}."
            },
            "Vermicompost": {
                "dosage": "2 - 3 tonnes/hectare",
                "method": "Incorporate thoroughly into upper topsoil layer",
                "timing": "10-15 days before sowing",
                "organic_alternative": "Farmyard Manure (FYM)",
                "reason": f"Low organic carbon level ({organic_matter}%) detected in {soil_type}. Vermicompost rebuilds soil microbiome."
            },
            "Organic Neem Cake": {
                "dosage": "250 - 300 kg/hectare",
                "method": "Soil application during tilling",
                "timing": "Basal application",
                "organic_alternative": "Mustard Oil Cake",
                "reason": f"Acidic/alkaline pH balance ({pH}) and soil pest suppression required in {soil_type}."
            },
            "Zinc Sulfate": {
                "dosage": "25 kg/hectare",
                "method": "Soil application mixed with dry soil or sand",
                "timing": "At sowing or early growth",
                "organic_alternative": "Chelated Organic Zinc Spray",
                "reason": f"Micronutrient supplementation required for heavy feeding crop ({crop}) in {soil_type}."
            }
        }

        info = guidance.get(fertilizer_name, {
            "dosage": "75 - 100 kg/hectare",
            "method": "Apply in bands near root zone and irrigate lightly",
            "timing": "Early vegetative growth stage",
            "organic_alternative": "Well-rotted Organic Compost",
            "reason": f"Dataset ML model recommended {fertilizer_name} based on learned multi-feature agricultural patterns."
        })

        return {
            "recommended_fertilizer": fertilizer_name,
            "confidence_score": round(confidence * 100, 1),
            "dosage": info["dosage"],
            "application_method": info["method"],
            "best_time": info["timing"],
            "organic_alternative": info["organic_alternative"],
            "recommendation_reason": info["reason"]
        }

fertilizer_service = FertilizerService()
