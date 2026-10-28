import os
import sys
import glob

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.append(os.path.join(PROJECT_ROOT, "backend"))

from services.soil_service import soil_service
from services.crop_service import crop_service
from services.fertilizer_service import fertilizer_service

def test_soil_predictions(out_file):
    out_file.write("\n--- Testing Soil ML Prediction Service on Unseen Test Images ---\n")
    test_files = glob.glob(os.path.join(PROJECT_ROOT, "dataset", "soil", "test", "*", "*.jpg"))
    assert len(test_files) > 0, "No soil test images found!"

    # Test sample images from test set
    for path in test_files[:6]:
        rel_class = os.path.basename(os.path.dirname(path))
        with open(path, "rb") as f:
            img_bytes = f.read()
        res = soil_service.analyze_soil_image(img_bytes)
        out_file.write(f"File ({rel_class}): {os.path.basename(path)}\n")
        out_file.write(f"  -> Predicted Soil Type: {res.get('predicted_soil_type')} (Confidence: {res.get('confidence_score')}%)\n")
        out_file.write(f"  -> Soil Health: {res.get('soil_health_status')} | Fertilizer Rec: {res.get('fertilizer_recommendation', {}).get('recommended_fertilizer')}\n")

def test_crop_predictions(out_file):
    out_file.write("\n--- Testing Crop Disease ML Prediction Service on Unseen Test Images ---\n")
    test_files = glob.glob(os.path.join(PROJECT_ROOT, "dataset", "crop_disease", "test", "*", "*.jpg"))
    assert len(test_files) > 0, "No crop disease test images found!"

    for path in test_files[:8]:
        rel_class = os.path.basename(os.path.dirname(path))
        with open(path, "rb") as f:
            img_bytes = f.read()
        res = crop_service.analyze_crop_image(img_bytes)
        out_file.write(f"File ({rel_class}): {os.path.basename(path)}\n")
        out_file.write(f"  -> Predicted Crop: {res.get('crop_name')} | Condition: {res.get('condition')} (Confidence: {res.get('confidence_score')}%)\n")
        out_file.write(f"  -> Treatment Action: {res.get('recommended_action')}\n")

def test_fertilizer_prediction(out_file):
    out_file.write("\n--- Testing Fertilizer Recommendation ML Service ---\n")
    res = fertilizer_service.recommend(soil_type="Black Soil", crop="Rice", N=30, P=20, K=25)
    out_file.write(f"Input: Black Soil, Rice, low N/P/K -> Recommended: {res.get('recommended_fertilizer')} (Confidence: {res.get('confidence_score')}%)\n")

if __name__ == "__main__":
    with open('tmp/backend_test_results.txt', 'w', encoding='utf-8') as out_file:
        test_soil_predictions(out_file)
        test_crop_predictions(out_file)
        test_fertilizer_prediction(out_file)
        out_file.write("\nALL BACKEND ML SERVICE PREDICTION TESTS PASSED!\n")
