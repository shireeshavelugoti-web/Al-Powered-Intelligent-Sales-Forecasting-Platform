from pathlib import Path
import joblib
import pandas as pd


FEATURES = (
    "company_growth",
    "industry_match",
    "technology_alignment",
    "business_need",
    "engagement_level",
)

MODEL_PATH = (
    Path(__file__).resolve().parents[1] / "ml" / "conversion_model.joblib"
)

def calculate_score(data):

    # The inputs are each rated from 0 to 10. Normalize their sum to 0–100
    # so priorities and API responses use the documented score scale.
    total_score = round(sum(data[feature] for feature in FEATURES) / 50 * 100)

    if total_score >= 80:
        priority = "High"

    elif total_score >= 50:
        priority = "Medium"

    else:
        priority = "Low"

    return  total_score, priority


def predict_conversion_probability(data):

    if not MODEL_PATH.exists():
        return None, "model_not_trained"

    model = joblib.load(MODEL_PATH)
    features = pd.DataFrame(
        [{feature: data[feature] for feature in FEATURES}],
        columns=FEATURES,
    )

    probability = model.predict_proba(features)[0][1]

    return round(float(probability) * 100, 2), (
        "trained_scikit_learn_model"
    )
