import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

def evaluate_all():
    print("==================================================")
    print("      EVALUATING ALL TRAINED MACHINE LEARNING MODELS")
    print("==================================================")

    model_paths = {
        "Soil Classifier": os.path.join(MODELS_DIR, "soil_model", "metrics.json"),
        "Crop Disease Classifier": os.path.join(MODELS_DIR, "crop_disease_model", "metrics.json"),
        "Fertilizer Recommender": os.path.join(MODELS_DIR, "fertilizer_model", "metrics.json"),
    }

    summary = {}
    for name, path in model_paths.items():
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                summary[name] = data
                print(f"\nModel: {name}")
                print(f"  - Accuracy:  {data.get('test_accuracy', 0)*100:.2f}%")
                print(f"  - Precision: {data.get('precision', 0):.4f}")
                print(f"  - Recall:    {data.get('recall', 0):.4f}")
                print(f"  - F1-Score:  {data.get('f1_score', 0):.4f}")
        else:
            print(f"\nModel: {name} - Metrics file not found at {path}")

    summary_path = os.path.join(MODELS_DIR, "evaluation_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nUnified evaluation summary exported to {summary_path}")

if __name__ == "__main__":
    evaluate_all()
