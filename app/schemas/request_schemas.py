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

"""
{
  "document_type": "PAYSLIP",
  "verdict": "INCONCLUSIVE",
  "forgery_score": 0.4099600454807219,
  "shap_feature": [
    {
      "feature": "bank_name_consistency",
      "contribution": 0.27
    },
    {
      "feature": "exif_anomaly",
      "contribution": -0.13
    },
    {
      "feature": "pan_format",
      "contribution": -0.03
    }
  ],
  "features": {
    "ela": 0,
    "exif_anomaly": 0,
    "fft": 0,
    "noise": 0,
    "cnn": 0,
    "resolution_dpi": 150,
    "logo_similarity": 0,
    "signature_similarity": 0,
    "copy_move": 0,
    "font_inconsistency_score": 0,
    "gross_earnings_validation": 0,
    "net_pay_validation": 0,
    "total_deductions_validation": 0,
    "pan_format": 0,
    "uan_format": 0,
    "ifsc_validation": 0,
    "bank_name_consistency": 1,
    "bank_account_no_consistency": 0,
    "employee_name_consistency": 0,
    "metadata_modified": 0,
    "joining_date_validation": 0,
    "days_worked_validation": 0,
    "hra_ratio_check": 0,
    "ytd_validation": 0,
    "type": "payslip"
  },
  "context": [
    {
      "feature": "bank_name_consistency",
      "reason": "The bank name printed on the document is inconsistent with standard bank registry names."
    }
  ],
  "individual_data": [
    {
      "field": "name",
      "value": "Nishant Patil"
    },
    {
      "field": "employee_id",
      "value": "MUM/2022/06"
    },
    {
      "field": "pan",
      "value": "GHAPP6217H"
    },
    {
      "field": "uan",
      "value": null
    }
  ]
}
"""