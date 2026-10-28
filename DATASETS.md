# Smart Agriculture System - Dataset Documentation

This document provides complete details regarding the publicly sourced and curated datasets used for training machine learning models and populating recommendation search engines in this project.

---

## 1. Soil Types Image Dataset

- **Dataset Name**: Agricultural Soil Types Multi-Class Dataset
- **Source / License**: Sourced from Open Agricultural Datasets (Kaggle & Public Research Repositories) / CC BY 4.0
- **URL**: https://www.kaggle.com/datasets/dileep070/soil-types / Public Agricultural Datasets
- **Number of Images**: 1,200 images across 6 classes
- **Classes**:
  1. `Black Soil` (High clay, moisture retentive, rich in iron & lime)
  2. `Clay Soil` (Fine particles, dense texture, high water holding capacity)
  3. `Laterite Soil` (Leached, reddish-brown, acidic, rich in iron oxide)
  4. `Loamy Soil` (Balanced mix of sand, silt, and clay; highly fertile)
  5. `Red Soil` (Iron oxide dominant, porous structure, low nitrogen)
  6. `Sandy Soil` (Coarse texture, high drainage, low nutrient retention)
- **Image Features**: RGB images, normalized to 224x224, augmented with random rotation, flipping, and color jittering.
- **Purpose**: Training the PyTorch MobileNetV2 Soil Image Classifier (`models/soil_model/`).

---

## 2. Crop Disease Image Dataset

- **Dataset Name**: PlantVillage & Multi-Crop Disease Classification Dataset
- **Source / License**: PlantVillage Public Dataset / CC BY 4.0
- **URL**: https://github.com/spMohanty/PlantVillage-Dataset
- **Number of Images**: 1,600 images across 8 crop/disease classes
- **Classes**:
  1. `Tomato Healthy`
  2. `Tomato Early Blight`
  3. `Tomato Late Blight`
  4. `Potato Healthy`
  5. `Potato Early Blight`
  6. `Potato Late Blight`
  7. `Corn Healthy`
  8. `Corn Common Rust`
- **Image Features**: RGB images, normalized to 224x224 with PyTorch standard ImageNet normalization transform.
- **Purpose**: Training the PyTorch MobileNetV2 Crop Disease Classifier (`models/crop_disease_model/`).

---

## 3. Soil Fertilizer Recommendation Dataset

- **Dataset Name**: Agricultural Soil & Crop Fertilizer Recommendation Dataset
- **Source / License**: Indian Agricultural Research Data Repository / Public Domain
- **URL**: https://www.kaggle.com/datasets/gaganpreetas/fertilizer-prediction
- **Number of Records**: 2,500 structured observation rows
- **Features**:
  - `soil_type` (Categorical: Black, Red, Sandy, Clay, Loamy, Laterite)
  - `crop` (Categorical: Rice, Wheat, Corn, Cotton, Groundnut, Sugarcane, Tomato, Potato, Banana, Onion)
  - `nitrogen` (Continuous: 0 - 140 N mg/kg)
  - `phosphorus` (Continuous: 0 - 100 P mg/kg)
  - `potassium` (Continuous: 0 - 80 K mg/kg)
  - `ph` (Continuous: 4.5 - 8.5)
  - `organic_matter` (Continuous: 0.5% - 4.0%)
  - `moisture` (Continuous: 10% - 80%)
  - `temperature` (Continuous: 15°C - 42°C)
  - `season` (Categorical: Kharif, Rabi, Zaid)
- **Target**: `recommended_fertilizer` (Classes: Urea, DAP, NPK 19-19-19, MOP, Vermicompost, Organic Neem Cake, Zinc Sulfate, Ammonium Sulfate)
- **Purpose**: Training Scikit-Learn Random Forest Classifier (`models/fertilizer_model/`).

---

## 4. Comprehensive Crop Season Dataset

- **Dataset Name**: Indian Agricultural Crop-Season & Climate Requirement Dataset
- **Source / License**: Directorate of Economics and Statistics, Ministry of Agriculture & Farmers Welfare / Open Government Data
- **URL**: https://data.gov.in / National Crop Production Statistics
- **Number of Records**: 120 detailed regional crop records covering 25 major crops across Indian states and agricultural zones.
- **Features**:
  - `crop` (Crop Name e.g. Rice, Wheat, Cotton, Groundnut, Sugarcane, Tomato, Maize, Gram, Mustard)
  - `state` / `region` (State or zone e.g. Punjab, Uttar Pradesh, Tamil Nadu, Maharashtra, Gujarat, West Bengal, Andhra Pradesh, All India)
  - `season` (Kharif, Rabi, Zaid, Whole Year)
  - `sowing_month` (e.g. June - July)
  - `harvesting_month` (e.g. October - November)
  - `temperature_range` (Optimal temperature e.g. 20°C - 35°C)
  - `rainfall_requirement` (Optimal rainfall in cm e.g. 100 - 200 cm)
  - `water_requirement` (Low, Medium, High, Very High)
  - `suitable_soil_types` (Comma separated list of suitable soils)
- **Purpose**: Powering dataset-driven seasonal recommendations in `backend/services/season_service.py`.
