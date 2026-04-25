from decimal import Decimal
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import date

class Supplier(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class Address(BaseModel):
    company_name: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None

class InvoiceInfo(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = "USD"
    payment_terms: Optional[str] = None
    purchase_order: Optional[str] = None

    @field_validator("invoice_date", "due_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if v in ["", "null", "None", None]:
            return None
        return v

class InvoiceItem(BaseModel):
    description: Optional[str] = None
    item_code: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None

    @model_validator(mode="after")
    def validate_item(self) -> "InvoiceItem":
        if not self.description and not self.item_code:
            raise ValueError("Invoice item must have either a description or an item code.")
        return self

class Totals(BaseModel):
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None

class Invoice(BaseModel):
    supplier: Supplier = Field(default_factory=Supplier)
    invoice_info: InvoiceInfo = Field(default_factory=InvoiceInfo)
    bill_to: Address = Field(default_factory=Address)
    ship_to: Address = Field(default_factory=Address)
    line_items: List[InvoiceItem] = Field(default_factory=list)
    totals: Totals = Field(default_factory=Totals)
    notes: Optional[str] = None

    @field_validator("supplier", "invoice_info", "bill_to", "ship_to", "totals", mode="before")
    @classmethod
    def ensure_object(cls, v):
        if v is None:
            return {}
        return v

    @model_validator(mode="after")
    def validate_invoice(self) -> "Invoice":
        if not self.supplier.name and not self.invoice_info.invoice_number and not self.totals.total_amount:
            raise ValueError("Invoice extraction failed: No supplier name, invoice number, or total amount found.")
        return self

class InvoiceWithMetadata(Invoice):
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExtractionResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    validation_errors: Optional[List[Dict[str, Any]]] = None
    attempts: int = 0
    model_used: Optional[str] = None
    token_stats: Optional[Dict[str, int]] = None
    saved: bool = False
    save_error: Optional[str] = None
    invoice_id: Optional[str] = None
