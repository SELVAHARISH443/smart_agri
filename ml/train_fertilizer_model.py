import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATASET_PATH = os.path.join(PROJECT_ROOT, "dataset", "fertilizer_recommendation.csv")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models", "fertilizer_model")
os.makedirs(MODEL_DIR, exist_ok=True)

def train_fertilizer_recommendation_model():
    print("==========================================================================")
    print("--- Retraining Fertilizer Recommender (Random Forest, 75/25 Split) ---")
    print("==========================================================================")

    df = pd.read_csv(DATASET_PATH)
    print(f"Loaded dataset with {len(df)} records.")

    # Encode categorical variables
    encoders = {}
    categorical_cols = ["soil_type", "crop", "season"]

    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        encoders[col] = le

    target_le = LabelEncoder()
    df["recommended_fertilizer"] = target_le.fit_transform(df["recommended_fertilizer"])
    encoders["recommended_fertilizer"] = target_le

    feature_cols = ["soil_type", "crop", "nitrogen", "phosphorus", "potassium", "ph", "organic_matter", "moisture", "temperature", "season"]
    X = df[feature_cols]
    y = df["recommended_fertilizer"]

    # 75% train (1875 samples) / 25% test (625 samples)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    test_acc = accuracy_score(y_test, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted")
    cm = confusion_matrix(y_test, y_pred).tolist()
    target_classes = list(target_le.classes_)
    clf_report_str = classification_report(y_test, y_pred, target_names=target_classes)

    importances = dict(zip(feature_cols, [round(float(val), 4) for val in model.feature_importances_]))

    metrics = {
        "model_name": "Random Forest Fertilizer Recommender",
        "dataset_split": "75% Train / 25% Test",
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "test_accuracy": round(float(test_acc), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "feature_importances": importances,
        "confusion_matrix": cm,
        "classification_report": clf_report_str,
        "classes": target_classes
    }

    print("\n==========================================================================")
    print("--- FERTILIZER MODEL FINAL EVALUATION RESULTS (25% TEST SET) ---")
    print("==========================================================================")
    print(f"Test Accuracy: {test_acc*100:.2f}%")
    print(f"Precision: {precision:.4f} | Recall: {recall:.4f} | F1: {f1:.4f}")
    print("\nCLASSIFICATION REPORT:\n")
    print(clf_report_str)
    print(f"Feature Importances: {importances}")

    # Save model and encoders
    joblib.dump(model, os.path.join(MODEL_DIR, "fertilizer_model.pkl"))
    joblib.dump(encoders, os.path.join(MODEL_DIR, "label_encoders.pkl"))

    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nFertilizer Model saved successfully to {MODEL_DIR}")

if __name__ == "__main__":
    train_fertilizer_recommendation_model()
