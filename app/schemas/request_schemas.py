from typing import Optional, Union, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class BusinessProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    business_name: Optional[str] = None
    business_type: Optional[str] = None
    industry: Optional[str] = None
    business_activity: Optional[str] = None
    business_age_years: Optional[float] = None
    declared_monthly_turnover: Optional[float] = None
    declared_monthly_production: Optional[float] = None
    declared_production_capacity: Optional[float] = None
    number_of_employees: Optional[int] = None


class PurchaseItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_name: str
    quantity: float
    unit: str
    unit_price: Optional[float] = None
    total_amount: Optional[float] = None


class PurchaseBill(BaseModel):
    model_config = ConfigDict(extra="ignore")

    supplier_name: Optional[str] = None
    invoice_date: Optional[str] = None
    items: List[PurchaseItem] = Field(default_factory=list)
    total_amount: Optional[float] = None


class PurchaseEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bills: List[PurchaseBill] = Field(default_factory=list)


class InventoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    estimated_value: Optional[float] = None


class ImageObservation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    object: str
    estimated_count: Optional[int] = None
    confidence: Optional[float] = None


class InventoryImageAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    observed_objects: List[ImageObservation] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)
    analysis_confidence: Optional[float] = None


class InventoryEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    declared_inventory: List[InventoryItem] = Field(default_factory=list)
    image_analysis: List[InventoryImageAnalysis] = Field(default_factory=list)


class ProductionEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    production_records: List[Dict[str, Any]] = Field(default_factory=list)
    raw_material_consumption: List[Dict[str, Any]] = Field(default_factory=list)
    finished_goods: List[Dict[str, Any]] = Field(default_factory=list)


class SalesEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sales_bills: List[Dict[str, Any]] = Field(default_factory=list)
    customer_details: List[Dict[str, Any]] = Field(default_factory=list)
    sales_summary: Optional[Dict[str, Any]] = None


class VideoAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    duration_seconds: Optional[float] = None
    observed_activities: List[str] = Field(default_factory=list)
    observed_machinery: List[str] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)
    analysis_confidence: Optional[float] = None


class PhysicalEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    video_analysis: List[VideoAnalysis] = Field(default_factory=list)
    machinery_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    premises_analysis: List[Dict[str, Any]] = Field(default_factory=list)


class FinancialEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    bank_transactions: List[Dict[str, Any]] = Field(default_factory=list)
    electricity_bills: List[Dict[str, Any]] = Field(default_factory=list)
    gst_records: List[Dict[str, Any]] = Field(default_factory=list)


class AdditionalEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    documents: List[Dict[str, Any]] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)


class ExplainRequest(BaseModel):
    """
    Flexible input request for business verification.
    Accepts natural language text, declared vs observed summaries, or structured multi-category evidence.
    """
    model_config = ConfigDict(extra="ignore")

    # Flexible natural language / text input support
    text: Optional[str] = Field(default=None, description="Free-form natural language business and evidence information")
    declared_information: Optional[Union[Dict[str, Any], str]] = Field(default=None, description="Declared claims or profile text")
    observed_evidence: Optional[Union[Dict[str, Any], str]] = Field(default=None, description="Observed documentary, financial, and physical evidence text")

    # Structured fields (optional, backwards-compatible with full JSON payloads)
    business_profile: Optional[BusinessProfile] = None
    purchase_evidence: Optional[PurchaseEvidence] = None
    inventory_evidence: Optional[InventoryEvidence] = None
    production_evidence: Optional[ProductionEvidence] = None
    sales_evidence: Optional[SalesEvidence] = None
    physical_evidence: Optional[PhysicalEvidence] = None
    financial_evidence: Optional[FinancialEvidence] = None
    additional_evidence: Optional[AdditionalEvidence] = None


# Alias for flexible naming
BusinessVerificationRequest = ExplainRequest
