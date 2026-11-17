from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TokenMetrics(BaseModel):
    model_config = ConfigDict(extra="ignore")

    model: str = "unknown"
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    inference_calls: int = 1


class ReportSections(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    business_understanding: str = Field(alias="BUSINESS UNDERSTANDING", min_length=1)
    evidence_matching: str = Field(alias="EVIDENCE MATCHING", min_length=1)
    possible_explanations: str = Field(alias="POSSIBLE EXPLANATIONS", min_length=1)
    additional_information_required: str = Field(
        alias="ADDITIONAL INFORMATION REQUIRED",
        min_length=1,
    )
    overall_assessment: str = Field(alias="OVERALL ASSESSMENT", min_length=1)


class ExplainResponse(BaseModel):
    """
    Structured inference response containing the complete five-section report.
    """
    model_config = ConfigDict(extra="ignore")

    status: str = Field(default="completed", description="Status: completed, partial, or failed")
    overall_assessment: str = Field(
        description="Conclusion: MATCH, PARTIAL MATCH, MISMATCH, or INSUFFICIENT EVIDENCE"
    )
    report: str = Field(..., description="Full human-readable abductive reasoning report")
    token_usage: Optional[TokenMetrics] = Field(default=None, description="Token usage and latency metrics")
    sections: ReportSections = Field(
        description="Complete report sections keyed by their standard headings"
    )


# Backward compatibility aliases
ExplanationResponse = ExplainResponse
BusinessVerificationResponse = ExplainResponse
AnalysisResponse = ExplainResponse
