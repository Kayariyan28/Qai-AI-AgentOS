from langchain.tools import tool
import numpy as np
import pandas as pd
import json
import warnings
from sklearn.datasets import make_classification, make_regression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC, SVR
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.metrics import accuracy_score, confusion_matrix, r2_score

# Silence sklearn warnings for cleaner logs
warnings.filterwarnings("ignore")

@tool
def build_ml_models(instructions: str) -> str:
    """
    Builds and evaluates 4 ML models on a synthetic dataset.
    Generates a dashboard with Accuracy Chart and Confusion Matrix.
    """
    try:
        # 1. Parse instructions / Defaults
        is_regression = "regression" in instructions.lower()
        n_samples = 400  # Increased for better stability
        n_features = 20  # Reduced/Adjusted
        
        # 2. Generate Data
        if is_regression:
            X, y = make_regression(n_samples=n_samples, n_features=n_features, noise=0.1, random_state=42)
            models = {
                "LinReg": LinearRegression(),
                "SVM": SVR(),
                "RF": RandomForestRegressor(n_estimators=10, random_state=42),
                "DT": DecisionTreeRegressor(random_state=42)
            }
        else:
            # Informative 15, Redundant 0, Repeated 0, Classes 2
            X, y = make_classification(n_samples=n_samples, n_features=n_features, n_classes=2, random_state=42)
            models = {
                "LogReg": LogisticRegression(),
                "SVM": SVC(probability=True, random_state=42),
                "RF": RandomForestClassifier(n_estimators=20, random_state=42),
                "DT": DecisionTreeClassifier(random_state=42)
            }
            
        # 3. Split Data
        X_train_raw, X_test_raw, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
        
        # Scale Data (Crucial for SVM/LogReg)
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train_raw)
        X_test = scaler.transform(X_test_raw)
        
        # 4. Train & Evaluate
        results = {"labels": [], "train_values": [], "test_values": []}
        best_model_name = None
        best_model_score = -1
        best_y_pred = None
        
        for name, model in models.items():
            model.fit(X_train, y_train)
            
            if is_regression:
                train_score = r2_score(y_train, model.predict(X_train))
                test_score = r2_score(y_test, model.predict(X_test))
            else:
                train_score = accuracy_score(y_train, model.predict(X_train))
                y_pred = model.predict(X_test)
                test_score = accuracy_score(y_test, y_pred)
                
                if test_score > best_model_score:
                    best_model_score = test_score
                    best_model_name = name
                    best_y_pred = y_pred

            results["labels"].append(name)
            results["train_values"].append(round(train_score, 2))
            results["test_values"].append(round(test_score, 2))
            
        # 5. Confusion Matrix (Best Model, Classification Only)
        matrix_data = {"grid": [], "labels": ["0", "1"]}
        if not is_regression and best_y_pred is not None:
            cm = confusion_matrix(y_test, best_y_pred)
            matrix_data["grid"] = cm.tolist() 
            
        # 6. Metadata Text
        summary = (f"Trained 4 Models on {n_samples} samples.\n"
                   f"Best Model: {best_model_name} (Acc: {best_model_score:.2f})")
                   
        # 7. Construct Payload
        payload = {
            "summary": summary,
            "accuracy_chart": {
                "title": "Train vs Validation Accuracy",
                "labels": results["labels"],
                "train": results["train_values"],
                "test": results["test_values"]
            },
            "confusion_matrix": {
                "title": f"Confusion Matrix ({best_model_name})",
                "labels": ["Class 0", "Class 1"],
                "grid": matrix_data["grid"]
            }
        }
        
        # 8. Pipeline Diagram Logic (Override if requested)
        if "pipeline" in instructions.lower() or "diagram" in instructions.lower():
            pipeline_payload = {
                "title": "ML Data Pipeline",
                "nodes": [
                    {"id": "n1", "label": f"Syn Data\n({n_samples}x{n_features})", "x": 40, "y": 200, "w": 120, "h": 60, "color": "blue"},
                    {"id": "n2", "label": "Scaler\n(Standard)", "x": 200, "y": 200, "w": 120, "h": 60, "color": "green"},
                    {"id": "n3", "label": "Split\n(75/25)", "x": 360, "y": 200, "w": 100, "h": 60, "color": "yellow"},
                    {"id": "n4", "label": f"Model: {best_model_name}\n({best_model_score:.2f})", "x": 500, "y": 200, "w": 130, "h": 60, "color": "red"}
                ],
                "edges": [
                    {"from": "n1", "to": "n2"},
                    {"from": "n2", "to": "n3"},
                    {"from": "n3", "to": "n4"}
                ]
            }
            return "GUI_PIPELINE_DIAGRAM:" + json.dumps(pipeline_payload)

        return "GUI_ML_DASHBOARD:" + json.dumps(payload)
        
    except Exception as e:
        import traceback
        return f"Error building models: {str(e)}\n{traceback.format_exc()}"
