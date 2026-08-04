from app.model.enum_model import Severity
from pydantic import BaseModel


class Finding(BaseModel):
    severity: Severity
    title: str
    summary: str
    explanation: str
    recommendation: str