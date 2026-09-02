from typing import Dict, Union

from pydantic import BaseModel, ConfigDict, Field


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
    model_config = ConfigDict(extra="forbid") # Forbid extra fields in the request payload

    document_type: str = Field(..., description="Document type")
    shap_feature: list[shap_features]
    context: list[context_features]
    individual_data: list[individual_data]
