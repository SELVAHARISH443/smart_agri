import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
DATASET_PATH = os.path.join(PROJECT_ROOT, "dataset", "crop_season_dataset.csv")

class SeasonService:
    def __init__(self):
        self.df = None
        self.load_dataset()

    def load_dataset(self):
        if os.path.exists(DATASET_PATH):
            self.df = pd.read_csv(DATASET_PATH)
            print("Crop Season Dataset loaded successfully.")
        else:
            print("WARNING: Crop Season CSV not found!")

    def get_crop_season(self, crop_name, region=None):
        if self.df is None:
            self.load_dataset()
            if self.df is None:
                return {"error": "Crop season dataset unavailable."}

        crop_clean = crop_name.strip().lower()
        matches = self.df[self.df["crop"].str.lower() == crop_clean]

        if matches.empty:
            # Fuzzy fallback substring search
            matches = self.df[self.df["crop"].str.lower().str.contains(crop_clean)]

        if matches.empty:
            available_crops = sorted(list(self.df["crop"].unique()))
            return {
                "found": False,
                "message": f"Crop '{crop_name}' not found in season dataset.",
                "available_crops": available_crops
            }

        # Filter by state/region if supplied
        if region and region.strip():
            reg_clean = region.strip().lower()
            region_matches = matches[
                (matches["state"].str.lower().str.contains(reg_clean)) |
                (matches["region"].str.lower().str.contains(reg_clean))
            ]
            if not region_matches.empty:
                matches = region_matches

        records = matches.to_dict(orient="records")

        # Pick primary recommendation summary
        primary = records[0]

        return {
            "found": True,
            "crop": primary["crop"],
            "primary_season": primary["season"],
            "sowing_period": primary["sowing_month"],
            "harvesting_period": primary["harvesting_month"],
            "temperature_requirement": primary["temperature_range"],
            "rainfall_requirement": primary["rainfall_requirement"],
            "water_requirement": primary["water_requirement"],
            "suitable_soil_types": primary["suitable_soil_types"],
            "regional_records_count": len(records),
            "regional_breakdown": records
        }

    def list_available_crops(self):
        if self.df is None:
            self.load_dataset()
        if self.df is not None:
            return sorted(list(self.df["crop"].unique()))
        return []

season_service = SeasonService()
