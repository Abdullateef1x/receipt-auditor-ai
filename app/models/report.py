from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class AuditReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: str
    original_filename: str
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    payment_method: Optional[str] = None
    audit_status: str                        # approved / flagged / rejected
    confidence: float
    recommendation: str
    anomalies_count: int
    report_pdf_url: str                      # R2 public URL
    created_at: datetime = Field(default_factory=datetime.utcnow)