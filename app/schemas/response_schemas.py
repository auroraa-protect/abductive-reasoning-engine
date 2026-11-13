from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class TokenMetrics(BaseModel):
    model_config = ConfigDict(extra="ignore")

    model: str = "unknown"
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    inference_calls: int = 1


class ExplainResponse(BaseModel):
    """
    Readable reasoning report output adhering to the 5-section abductive verification format.
    """
    model_config = ConfigDict(extra="ignore")

    case_id: str = Field(..., description="Verification case ID")
    status: str = Field(default="completed", description="Status: completed, partial, or failed")
    overall_assessment: Optional[str] = Field(default=None, description="Conclusion: MATCH, PARTIAL MATCH, MISMATCH, or INSUFFICIENT EVIDENCE")
    report: str = Field(..., description="Full human-readable abductive reasoning report")
    token_usage: Optional[TokenMetrics] = Field(default=None, description="Token usage and latency metrics")
    sections: Optional[Dict[str, str]] = Field(default_factory=dict, description="Parsed individual report sections")


# Backward compatibility aliases
ExplanationResponse = ExplainResponse
BusinessVerificationResponse = ExplainResponse
AnalysisResponse = ExplainResponse
