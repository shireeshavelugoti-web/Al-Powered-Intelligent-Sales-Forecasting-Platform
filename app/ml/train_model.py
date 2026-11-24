import sys
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)


FEATURES = [
    "company_growth",
    "industry_match",
    "technology_alignment",
    "business_need",
    "engagement_level"
]

TARGET = "converted"


def train_model(csv_path):

    data = pd.read_csv(csv_path)

    X = data[FEATURES]

    y = data[TARGET]

    if y.nunique() != 2:
        raise ValueError(
            "Dataset must contain both converted and not converted leads."
        )

    if y.value_counts().min() < 2:
        raise ValueError(
            "At least two records per outcome class are required."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=5,
        class_weight="balanced",
        random_state=42
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    print("Model Accuracy:", accuracy * 100, "%")

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    output_path = (
        Path(__file__).resolve().parent
        / "conversion_model.joblib"
    )

    joblib.dump(model, output_path)

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, predictions, average="binary", zero_division=0
    )
    report = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset": str(Path(csv_path)),
        "feature_names": FEATURES,
        "training_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
        "meets_milestone_2_accuracy_target": bool(accuracy >= 0.85),
    }
    report_path = output_path.with_suffix(".metrics.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"\nModel saved successfully: {output_path}")
    print(f"Evaluation report saved: {report_path}")


if __name__ == "__main__":

    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python -m app.ml.train_model dataset/historical_leads.csv"
        )

    train_model(sys.argv[1])
