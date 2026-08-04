from pydantic import BaseModel
from app.schemas.findings_schemas import Finding

class ExplanationResponse(BaseModel):
    findings: list[Finding]