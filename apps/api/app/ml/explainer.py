"""
SHAP explainability for the shipment delay model.
"""

import pandas as pd
import shap

_explainer = None


def get_explainer(model):
    global _explainer
    if _explainer is None:
        _explainer = shap.TreeExplainer(model)
    return _explainer


def explain_prediction(model, features_df: pd.DataFrame) -> dict:
    explainer = get_explainer(model)
    shap_values = explainer.shap_values(features_df)
    contributions = dict(zip(features_df.columns, shap_values[0]))
    return {k: round(float(v), 4) for k, v in contributions.items()}
