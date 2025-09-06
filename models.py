# =============================================================================
# PYDANTIC MODELS
# =============================================================================

# Document models
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta


class DocumentResponse(BaseModel):
    id: str
    filename: str
    business_name: Optional[str] = None
    upload_time: datetime
    status: str
    document_type: Optional[str] = None
    processing_time: Optional[float] = None
    classification_confidence: Optional[float] = None


class AnalysisResult(BaseModel):
    id: str
    document_id: str
    success: bool
    document_type: Optional[str]
    classification_confidence: Optional[float]
    processing_time_seconds: Optional[float]
    raw_markdown: Optional[str]
    structured_data: Optional[dict]
    error: Optional[str]
    created_at: datetime

# Company models


class CompanySearchRequest(BaseModel):
    query: str
    filter_type: str = "company"
    max_results: Optional[int] = 10


class CompanySearchResponse(BaseModel):
    success: bool
    results: List[Dict[str, str]]
    total_found: int
    error_message: Optional[str] = None


class CompanyDataResponse(BaseModel):
    success: bool
    company_id: str
    rc_sections: Dict[str, Any]
    extraction_timestamp: str
    error_message: Optional[str] = None

# Credit report models


class CreditRequestCreate(BaseModel):
    company_identifier: str
    identifier_type: str = "name"  # name, cin, pan, gstin
    request_type: str = "plus"     # plus, cam
    notes: Optional[str] = None


class CreditRequestResponse(BaseModel):
    id: str
    user_id: str
    company_id: Optional[str]
    company_identifier: str
    identifier_type: str
    status: str
    request_type: str
    priority: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class CreditReportResponse(BaseModel):
    id: str
    request_id: str
    company_id: str
    report_type: str
    score: Optional[int]
    grade: Optional[str]
    recommended_limit: Optional[float]
    risk_category: Optional[str]
    report_data: Optional[Dict[str, Any]]
    generated_at: datetime
    expires_at: Optional[datetime]


class CompanyResponse(BaseModel):
    id: str
    name: str
    cin: Optional[str]
    pan: Optional[str]
    gstin: Optional[str]
    address: Optional[str]
    website: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    industry: Optional[str]
    incorporated_date: Optional[datetime]
    status: str
    created_at: datetime

# User models


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    company_name: Optional[str]
    phone: Optional[str]
    created_at: datetime
    updated_at: datetime
