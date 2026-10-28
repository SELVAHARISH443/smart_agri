import os
import random
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFilter

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOIL_DIR = os.path.join(BASE_DIR, "soil")
CROP_DIR = os.path.join(BASE_DIR, "crop_disease")

# 1. Soil Classes and characteristic RGB color palettes
SOIL_CLASSES = {
    "Black_Soil": (35, 32, 30),
    "Clay_Soil": (110, 85, 60),
    "Laterite_Soil": (160, 60, 35),
    "Loamy_Soil": (75, 55, 40),
    "Red_Soil": (180, 70, 45),
    "Sandy_Soil": (210, 180, 130),
}

# 2. Crop Disease Classes and characteristics
CROP_DISEASE_CLASSES = {
    "Tomato_Healthy": {"base": (40, 140, 40), "spots": None},
    "Tomato_Early_Blight": {"base": (50, 120, 35), "spots": (100, 70, 30)},
    "Tomato_Late_Blight": {"base": (45, 100, 30), "spots": (50, 40, 30)},
    "Potato_Healthy": {"base": (35, 130, 45), "spots": None},
    "Potato_Early_Blight": {"base": (45, 110, 35), "spots": (90, 60, 20)},
    "Potato_Late_Blight": {"base": (40, 95, 30), "spots": (45, 35, 25)},
    "Corn_Healthy": {"base": (50, 160, 40), "spots": None},
    "Corn_Common_Rust": {"base": (55, 135, 35), "spots": (170, 80, 25)},
}

def create_synthetic_soil_image(color, width=224, height=224):
    """Generate a realistic textured soil image based on base color palette."""
    # Create base array with color variation
    r, g, b = color
    r_arr = np.random.normal(r, 12, (height, width))
    g_arr = np.random.normal(g, 10, (height, width))
    b_arr = np.random.normal(b, 10, (height, width))

    img_arr = np.stack([r_arr, g_arr, b_arr], axis=-1)
    img_arr = np.clip(img_arr, 0, 255).astype(np.uint8)

    img = Image.fromarray(img_arr)
    draw = ImageDraw.Draw(img)

    # Add specks/pebbles texture
    num_specks = random.randint(40, 90)
    for _ in range(num_specks):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        rad = random.randint(1, 4)
        shade = random.randint(-40, 40)
        speck_color = (
            max(0, min(255, r + shade)),
            max(0, min(255, g + shade)),
            max(0, min(255, b + shade))
        )
        draw.ellipse([x - rad, y - rad, x + rad, y + rad], fill=speck_color)

    return img.filter(ImageFilter.GaussianBlur(radius=0.5))

def create_synthetic_leaf_image(params, width=224, height=224):
    """Generate a realistic textured leaf image with optional disease spots."""
    base_rgb = params["base"]
    r, g, b = base_rgb

    # Leaf background shape simulation
    r_arr = np.random.normal(r, 8, (height, width))
    g_arr = np.random.normal(g, 15, (height, width))
    b_arr = np.random.normal(b, 8, (height, width))

    img_arr = np.stack([r_arr, g_arr, b_arr], axis=-1)
    img_arr = np.clip(img_arr, 0, 255).astype(np.uint8)

    img = Image.fromarray(img_arr)
    draw = ImageDraw.Draw(img)

    # Draw leaf veins
    draw.line([width // 2, 10, width // 2, height - 10], fill=(r + 20, g + 30, b + 20), width=3)
    for y in range(30, height - 30, 25):
        draw.line([width // 2, y, width // 2 - 40, y + 20], fill=(r + 15, g + 25, b + 15), width=2)
        draw.line([width // 2, y, width // 2 + 40, y + 20], fill=(r + 15, g + 25, b + 15), width=2)

    # Draw disease spots if applicable
    if params["spots"]:
        sr, sg, sb = params["spots"]
        num_spots = random.randint(8, 25)
        for _ in range(num_spots):
            cx = random.randint(20, width - 20)
            cy = random.randint(20, height - 20)
            rx = random.randint(5, 16)
            ry = random.randint(5, 16)
            spot_color = (
                max(0, min(255, sr + random.randint(-15, 15))),
                max(0, min(255, sg + random.randint(-15, 15))),
                max(0, min(255, sb + random.randint(-15, 15))),
            )
            draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=spot_color)

    return img.filter(ImageFilter.GaussianBlur(radius=0.4))

import shutil
import hashlib

def prepare_soil_dataset(num_per_class=120):
    """Generate clean 75% train / 25% test splits for soil image classification."""
    print("Generating & Reorganizing Soil Image Dataset (75% Train / 25% Test)...")
    if os.path.exists(SOIL_DIR):
        shutil.rmtree(SOIL_DIR)

    splits = {"train": 0.75, "test": 0.25}
    total_generated = 0
    all_hashes = set()

    for class_name, color in SOIL_CLASSES.items():
        train_count = int(num_per_class * splits["train"]) # 90
        test_count = num_per_class - train_count           # 30

        counts = {"train": train_count, "test": test_count}

        for split, count in counts.items():
            split_dir = os.path.join(SOIL_DIR, split, class_name)
            os.makedirs(split_dir, exist_ok=True)
            for i in range(count):
                while True:
                    img = create_synthetic_soil_image(color)
                    # Check unique bytes
                    img_bytes = img.tobytes()
                    h = hashlib.md5(img_bytes).hexdigest()
                    if h not in all_hashes:
                        all_hashes.add(h)
                        break
                img.save(os.path.join(split_dir, f"{class_name}_{split}_{i+1:04d}.jpg"))
                total_generated += 1

    print(f"Soil dataset generated in {SOIL_DIR}: {total_generated} images across 6 classes (75% Train / 25% Test)")

def prepare_crop_dataset(num_per_class=120):
    """Generate clean 75% train / 25% test splits for crop disease image classification."""
    print("Generating & Reorganizing Crop Disease Image Dataset (75% Train / 25% Test)...")
    if os.path.exists(CROP_DIR):
        shutil.rmtree(CROP_DIR)

    splits = {"train": 0.75, "test": 0.25}
    total_generated = 0
    all_hashes = set()

    for class_name, params in CROP_DISEASE_CLASSES.items():
        train_count = int(num_per_class * splits["train"]) # 90
        test_count = num_per_class - train_count           # 30

        counts = {"train": train_count, "test": test_count}

        for split, count in counts.items():
            split_dir = os.path.join(CROP_DIR, split, class_name)
            os.makedirs(split_dir, exist_ok=True)
            for i in range(count):
                while True:
                    img = create_synthetic_leaf_image(params)
                    img_bytes = img.tobytes()
                    h = hashlib.md5(img_bytes).hexdigest()
                    if h not in all_hashes:
                        all_hashes.add(h)
                        break
                img.save(os.path.join(split_dir, f"{class_name}_{split}_{i+1:04d}.jpg"))
                total_generated += 1

    print(f"Crop disease dataset generated in {CROP_DIR}: {total_generated} images across 8 classes (75% Train / 25% Test)")

def prepare_fertilizer_dataset(num_records=2500):
    """Generate a comprehensive, scientifically sound fertilizer dataset."""
    print(f"Generating Tabular Fertilizer Dataset ({num_records} records)...")

    soil_types = ["Black Soil", "Red Soil", "Sandy Soil", "Clay Soil", "Loamy Soil", "Laterite Soil"]
    crops = ["Rice", "Wheat", "Corn", "Cotton", "Groundnut", "Sugarcane", "Tomato", "Potato", "Banana", "Onion"]
    seasons = ["Kharif", "Rabi", "Zaid"]

    data = []
    for _ in range(num_records):
        st = random.choice(soil_types)
        cr = random.choice(crops)
        se = random.choice(seasons)

        N = random.randint(10, 140)
        P = random.randint(10, 100)
        K = random.randint(10, 80)
        pH = round(random.uniform(5.0, 8.5), 1)
        organic_matter = round(random.uniform(0.5, 4.0), 2)
        moisture = random.randint(15, 75)
        temperature = random.randint(18, 40)

        # Agronomical target logic with natural noise
        if N < 45 and P < 35:
            fertilizer = "NPK 19-19-19"
        elif N < 50:
            fertilizer = "Urea"
        elif P < 35:
            fertilizer = "DAP"
        elif K < 30:
            fertilizer = "MOP (Muriate of Potash)"
        elif pH < 5.8:
            fertilizer = "Organic Neem Cake"
        elif organic_matter < 1.2:
            fertilizer = "Vermicompost"
        elif cr in ["Rice", "Wheat"] and N > 80:
            fertilizer = "Zinc Sulfate"
        else:
            fertilizer = "NPK 19-19-19"

        # Occasional random variation for dataset noise
        if random.random() < 0.05:
            fertilizer = random.choice(["Urea", "DAP", "NPK 19-19-19", "Vermicompost", "Organic Neem Cake"])

        data.append({
            "soil_type": st,
            "crop": cr,
            "nitrogen": N,
            "phosphorus": P,
            "potassium": K,
            "ph": pH,
            "organic_matter": organic_matter,
            "moisture": moisture,
            "temperature": temperature,
            "season": se,
            "recommended_fertilizer": fertilizer
        })

    df = pd.DataFrame(data)
    csv_path = os.path.join(BASE_DIR, "fertilizer_recommendation.csv")
    df.to_csv(csv_path, index=False)
    print(f"Fertilizer dataset saved to {csv_path}")

def prepare_crop_season_dataset():
    """Generate a detailed crop-season dataset covering Indian regions and climate requirements."""
    print("Generating Crop Season Dataset...")
    records = [
        {
            "crop": "Rice",
            "state": "West Bengal",
            "region": "Eastern India",
            "season": "Kharif",
            "sowing_month": "June - July",
            "harvesting_month": "November - December",
            "temperature_range": "20°C - 38°C",
            "rainfall_requirement": "100 - 200 cm",
            "water_requirement": "High",
            "suitable_soil_types": "Clay Soil, Loamy Soil, Alluvial Soil"
        },
        {
            "crop": "Rice",
            "state": "Punjab",
            "region": "North India",
            "season": "Kharif",
            "sowing_month": "June",
            "harvesting_month": "October",
            "temperature_range": "25°C - 35°C",
            "rainfall_requirement": "100 - 150 cm",
            "water_requirement": "High",
            "suitable_soil_types": "Loamy Soil, Clay Soil"
        },
        {
            "crop": "Rice",
            "state": "Tamil Nadu",
            "region": "South India",
            "season": "Kharif / Samba",
            "sowing_month": "August - September",
            "harvesting_month": "January - February",
            "temperature_range": "22°C - 36°C",
            "rainfall_requirement": "90 - 140 cm",
            "water_requirement": "High",
            "suitable_soil_types": "Red Soil, Alluvial Soil, Clay Soil"
        },
        {
            "crop": "Wheat",
            "state": "Punjab",
            "region": "North India",
            "season": "Rabi",
            "sowing_month": "October - November",
            "harvesting_month": "March - April",
            "temperature_range": "10°C - 25°C",
            "rainfall_requirement": "50 - 75 cm",
            "water_requirement": "Medium",
            "suitable_soil_types": "Loamy Soil, Alluvial Soil"
        },
        {
            "crop": "Wheat",
            "state": "Uttar Pradesh",
            "region": "Central/North India",
            "season": "Rabi",
            "sowing_month": "November",
            "harvesting_month": "April",
            "temperature_range": "12°C - 26°C",
            "rainfall_requirement": "45 - 70 cm",
            "water_requirement": "Medium",
            "suitable_soil_types": "Alluvial Soil, Loamy Soil"
        },
        {
            "crop": "Wheat",
            "state": "Madhya Pradesh",
            "region": "Central India",
            "season": "Rabi",
            "sowing_month": "November",
            "harvesting_month": "March - April",
            "temperature_range": "15°C - 28°C",
            "rainfall_requirement": "40 - 65 cm",
            "water_requirement": "Medium",
            "suitable_soil_types": "Black Soil, Loamy Soil"
        },
        {
            "crop": "Cotton",
            "state": "Maharashtra",
            "region": "Deccan Plateau",
            "season": "Kharif",
            "sowing_month": "June - July",
            "harvesting_month": "November - December",
            "temperature_range": "21°C - 35°C",
            "rainfall_requirement": "50 - 100 cm",
            "water_requirement": "Medium",
            "suitable_soil_types": "Black Soil (Regur), Deep Loamy Soil"
        },
        {
            "crop": "Cotton",
            "state": "Gujarat",
            "region": "West India",
            "season": "Kharif",
            "sowing_month": "June",
            "harvesting_month": "December - January",
            "temperature_range": "22°C - 37°C",
            "rainfall_requirement": "60 - 100 cm",
            "water_requirement": "Medium",
            "suitable_soil_types": "Black Soil, Alluvial Soil"
        },
        {
            "crop": "Groundnut",
            "state": "Gujarat",
            "region": "Saurashtra",
            "season": "Kharif",
            "sowing_month": "June - July",
            "harvesting_month": "October - November",
            "temperature_range": "22°C - 32°C",
            "rainfall_requirement": "50 - 75 cm",
            "water_requirement": "Medium",
            "suitable_soil_types": "Sandy Soil, Loamy Soil, Red Soil"
        },
        {
            "crop": "Groundnut",
            "state": "Andhra Pradesh",
            "region": "Rayalaseema",
            "season": "Kharif",
            "sowing_month": "July",
            "harvesting_month": "November",
            "temperature_range": "24°C - 34°C",
            "rainfall_requirement": "50 - 80 cm",
            "water_requirement": "Medium",
            "suitable_soil_types": "Red Sandy Soil, Loamy Soil"
        },
        {
            "crop": "Tomato",
            "state": "Karnataka",
            "region": "South India",
            "season": "Rabi / Year-round",
            "sowing_month": "October - November",
            "harvesting_month": "February - March",
            "temperature_range": "18°C - 30°C",
            "rainfall_requirement": "60 - 100 cm",
            "water_requirement": "Medium",
            "suitable_soil_types": "Red Soil, Loamy Soil"
        },
        {
            "crop": "Potato",
            "state": "Uttar Pradesh",
            "region": "North India",
            "season": "Rabi",
            "sowing_month": "October",
            "harvesting_month": "January - February",
            "temperature_range": "15°C - 24°C",
            "rainfall_requirement": "40 - 60 cm",
            "water_requirement": "Medium",
            "suitable_soil_types": "Loamy Soil, Sandy Soil"
        },
        {
            "crop": "Maize",
            "state": "Karnataka",
            "region": "South India",
            "season": "Kharif",
            "sowing_month": "June - July",
            "harvesting_month": "September - October",
            "temperature_range": "21°C - 32°C",
            "rainfall_requirement": "50 - 100 cm",
            "water_requirement": "Medium",
            "suitable_soil_types": "Red Soil, Black Soil, Loamy Soil"
        },
        {
            "crop": "Sugarcane",
            "state": "Uttar Pradesh",
            "region": "North India",
            "season": "Perennial / Whole Year",
            "sowing_month": "October - November or February",
            "harvesting_month": "December - March",
            "temperature_range": "20°C - 38°C",
            "rainfall_requirement": "100 - 150 cm",
            "water_requirement": "Very High",
            "suitable_soil_types": "Deep Loamy Soil, Alluvial Soil"
        },
        {
            "crop": "Onion",
            "state": "Maharashtra",
            "region": "Nasik Belt",
            "season": "Rabi / Kharif",
            "sowing_month": "November - December",
            "harvesting_month": "April - May",
            "temperature_range": "15°C - 30°C",
            "rainfall_requirement": "60 - 75 cm",
            "water_requirement": "Medium",
            "suitable_soil_types": "Deep Red Soil, Black Soil, Loamy Soil"
        },
        {
            "crop": "Watermelon",
            "state": "Rajasthan",
            "region": "North-West India",
            "season": "Zaid",
            "sowing_month": "February - March",
            "harvesting_month": "May - June",
            "temperature_range": "25°C - 38°C",
            "rainfall_requirement": "30 - 50 cm",
            "water_requirement": "Medium",
            "suitable_soil_types": "Sandy Soil, Sandy Loam"
        },
        {
            "crop": "Cucumber",
            "state": "Haryana",
            "region": "North India",
            "season": "Zaid",
            "sowing_month": "February",
            "harvesting_month": "April - May",
            "temperature_range": "24°C - 35°C",
            "rainfall_requirement": "30 - 60 cm",
            "water_requirement": "Medium",
            "suitable_soil_types": "Sandy Loam, Loamy Soil"
        }
    ]

    df = pd.DataFrame(records)
    csv_path = os.path.join(BASE_DIR, "crop_season_dataset.csv")
    df.to_csv(csv_path, index=False)
    print(f"Crop season dataset saved to {csv_path}")

if __name__ == "__main__":
    prepare_soil_dataset()
    prepare_crop_dataset()
    prepare_fertilizer_dataset()
    prepare_crop_season_dataset()
    print("ALL DATASETS PREPARED SUCCESSFULLY!")
