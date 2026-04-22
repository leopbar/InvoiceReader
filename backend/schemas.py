from pydantic import BaseModel, Field
from typing import Optional, List

class SupplierInfo(BaseModel):
    name: Optional[str] = Field(None, description="Company name of the supplier/vendor")
    address: Optional[str] = Field(None, description="Full address")
    email: Optional[str] = Field(None, description="Email if present")
    phone: Optional[str] = Field(None, description="Phone if present")
    tax_id: Optional[str] = Field(None, description="Tax ID / VAT number / EIN")

class InvoiceInfo(BaseModel):
    invoice_number: Optional[str] = Field(None, description="Invoice number/ID")
    invoice_date: Optional[str] = Field(None, description="Date issued in YYYY-MM-DD format")
    due_date: Optional[str] = Field(None, description="Payment due date in YYYY-MM-DD format")
    currency: Optional[str] = Field(None, description="Currency code like USD, EUR, GBP")
    payment_terms: Optional[str] = Field(None, description="Payment terms like Net 30")
    purchase_order: Optional[str] = Field(None, description="PO number if present")

class AddressInfo(BaseModel):
    company_name: Optional[str] = Field(None, description="Company name")
    address_line: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    zip_code: Optional[str] = Field(None, description="ZIP/Postal code")
    country: Optional[str] = Field(None, description="Country")

class LineItem(BaseModel):
    description: Optional[str] = Field(None, description="Item description")
    quantity: Optional[float] = Field(None, description="Quantity")
    unit: Optional[str] = Field(None, description="Unit of measure")
    unit_price: Optional[float] = Field(None, description="Price per unit")
    total_price: Optional[float] = Field(None, description="Total price for this line")
    item_code: Optional[str] = Field(None, description="SKU/Item code if present")

class Totals(BaseModel):
    subtotal: Optional[float] = Field(None, description="Subtotal before tax")
    tax_amount: Optional[float] = Field(None, description="Tax amount")
    discount: Optional[float] = Field(None, description="Discount amount")
    total_amount: Optional[float] = Field(None, description="Final total amount")

class InvoiceData(BaseModel):
    supplier: Optional[SupplierInfo] = None
    invoice_info: Optional[InvoiceInfo] = None
    bill_to: Optional[AddressInfo] = None
    ship_to: Optional[AddressInfo] = None
    line_items: Optional[List[LineItem]] = None
    totals: Optional[Totals] = None
    notes: Optional[str] = Field(None, description="Additional notes, terms, or bank details")
