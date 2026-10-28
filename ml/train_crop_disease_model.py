import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATASET_DIR = os.path.join(PROJECT_ROOT, "dataset", "crop_disease")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models", "crop_disease_model")
os.makedirs(MODEL_DIR, exist_ok=True)

data_transforms = {
    'train': transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'test': transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
}

def train_crop_disease_classifier(epochs=10, batch_size=16, lr=0.001):
    print("===================================================================")
    print("--- Retraining Crop Disease Classifier on 75/25 Train/Test Split ---")
    print("===================================================================")

    image_datasets = {
        x: datasets.ImageFolder(os.path.join(DATASET_DIR, x), data_transforms[x])
        for x in ['train', 'test']
    }

    dataloaders = {
        x: DataLoader(image_datasets[x], batch_size=batch_size, shuffle=(x == 'train'), num_workers=0)
        for x in ['train', 'test']
    }

    class_names = image_datasets['train'].classes
    num_classes = len(class_names)
    print(f"Crop/Disease Classes ({num_classes}): {class_names}")
    print(f"Training samples (75%): {len(image_datasets['train'])} | Test samples (25%): {len(image_datasets['test'])}")

    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)

    for param in model.parameters():
        param.requires_grad = False

    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, 128),
        nn.ReLU(),
        nn.Linear(128, num_classes)
    )

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.classifier.parameters(), lr=lr)

    best_test_acc = 0.0

    for epoch in range(epochs):
        for phase in ['train', 'test']:
            if phase == 'train':
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / len(image_datasets[phase])
            epoch_acc = running_corrects.double() / len(image_datasets[phase])

            if phase == 'test' and epoch_acc >= best_test_acc:
                best_test_acc = epoch_acc.item()
                torch.save(model.state_dict(), os.path.join(MODEL_DIR, "crop_disease_model.pth"))

            if phase == 'test':
                print(f"Epoch {epoch+1:02d}/{epochs:02d} | Train Loss: {tr_loss:.4f} Acc: {tr_acc:.4f} || Test Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}")
            else:
                tr_loss = epoch_loss
                tr_acc = epoch_acc

    # Final Evaluation on 25% Test Set
    model.load_state_dict(torch.load(os.path.join(MODEL_DIR, "crop_disease_model.pth")))
    model.eval()

    all_preds = []
    all_labels = []
    total_test_loss = 0.0

    with torch.no_grad():
        for inputs, labels in dataloaders['test']:
            inputs = inputs.to(device)
            labels_dev = labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels_dev)
            _, preds = torch.max(outputs, 1)
            total_test_loss += loss.item() * inputs.size(0)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())

    final_test_loss = total_test_loss / len(image_datasets['test'])
    test_acc = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(all_labels, all_preds, average='weighted')
    cm = confusion_matrix(all_labels, all_preds).tolist()
    clf_report_str = classification_report(all_labels, all_preds, target_names=class_names)

    metrics = {
        "model_name": "MobileNetV2 Crop Disease Classifier",
        "dataset_split": "75% Train / 25% Test",
        "train_samples": len(image_datasets['train']),
        "test_samples": len(image_datasets['test']),
        "test_loss": round(float(final_test_loss), 4),
        "test_accuracy": round(float(test_acc), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "confusion_matrix": cm,
        "classification_report": clf_report_str,
        "classes": class_names
    }

    print("\n===================================================================")
    print("--- CROP DISEASE MODEL FINAL EVALUATION RESULTS (25% TEST SET) ---")
    print("===================================================================")
    print(f"Test Loss: {final_test_loss:.4f}")
    print(f"Test Accuracy: {test_acc*100:.2f}%")
    print(f"Precision: {precision:.4f} | Recall: {recall:.4f} | F1 Score: {f1:.4f}")
    print("\nCLASSIFICATION REPORT:\n")
    print(clf_report_str)

    with open(os.path.join(MODEL_DIR, "crop_disease_class_labels.json"), "w") as f:
        json.dump({i: cls for i, cls in enumerate(class_names)}, f, indent=2)

    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nCrop Disease Model saved successfully to {MODEL_DIR}")

if __name__ == "__main__":
    train_crop_disease_classifier()
