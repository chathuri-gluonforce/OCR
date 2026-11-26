
from datetime import date
from typing import Literal

from pydantic import BaseModel


class InvoiceRecord(BaseModel):
    entry_type: Literal["AP", "AR", "GL"]
    reference: str
    amount_cents: int
    currency: str
    invoice_date: date | None = None
    due_date: date | None = None
    counterparty: str | None = None
    is_open: bool | None = None


class InvoiceExtractionResponse(BaseModel):
    records: list[InvoiceRecord]
