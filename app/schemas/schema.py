from pydantic import BaseModel
from typing import Optional


class InvoiceData(BaseModel):
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    line_items: Optional[list[dict]] = None
    tax: Optional[float] = None
    payment_method: Optional[str] = None