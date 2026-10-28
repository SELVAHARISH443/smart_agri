import os
import pandas as pd

from .lazy_resource import LazyResource

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
DATASET_PATH = os.path.join(PROJECT_ROOT, "dataset", "crop_season_dataset.csv")

class SeasonService:
    def __init__(self):
        self.df = None
        self._dataset_resource = LazyResource("crop season dataset")

    def load_dataset(self):
        def initialize():
            if not os.path.isfile(DATASET_PATH):
                raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

            dataset = pd.read_csv(DATASET_PATH)
            required_columns = {
                "crop", "season", "sowing_month", "harvesting_month",
                "temperature_range", "rainfall_requirement",
                "water_requirement", "suitable_soil_types", "state", "region",
            }
            missing_columns = required_columns.difference(dataset.columns)
            if missing_columns:
                raise ValueError(
                    f"Dataset is missing required columns: {', '.join(sorted(missing_columns))}"
                )

            self.df = dataset
            print("Crop Season Dataset loaded successfully.")
            return dataset

        return self._dataset_resource.get(initialize)

    @property
    def initialization_status(self):
        return self._dataset_resource.status

    def get_crop_season(self, crop_name, region=None):
        self.load_dataset()

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
        dataset = self.load_dataset()
        return sorted(list(dataset["crop"].unique()))

season_service = SeasonService()
