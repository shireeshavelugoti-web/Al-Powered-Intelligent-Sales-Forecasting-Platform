from .. services.scoring_service import (
    predict_conversion_probability
)

def predict_lead(data):
    probability, source = predict_conversion_probability(data)

    return {
        "conversation_probability": probability,
        "model_source":source
    }