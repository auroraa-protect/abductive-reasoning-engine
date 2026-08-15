from typing import Dict, Union

from pydantic import BaseModel, Field


class shap_features(BaseModel):
    feature: str = Field(..., description="Feature name")
    contribution: float = Field(..., description="SHAP contribution. Positive increases fraud score, negative decreases fraud score.")

class context_features(BaseModel):
    feature: str = Field(..., description="Feature name")
    reason: str = Field(..., description="Reason for validation result")


class individual_data(BaseModel):
    field: str = Field(..., description="Field name")
    value: Union[str, None] = Field(..., description="Field value")


class ExplainRequest(BaseModel):
    document_type: str = Field(..., description="Document type")
    verdict: str = Field(..., description="ML model verdict")
    forgery_score: float = Field(..., ge=0.0, le=1.0, description="Forgery probability between 0 and 1.")

    shap_feature: list[shap_features]

    features: Dict[str, Union[int, float, str, bool, None]]

    context: list[context_features]

    individual_data: list[individual_data]