"""
Tests for backend.extraction.schemas — Pydantic models, validators, edge cases.
"""
import pytest
from decimal import Decimal
from datetime import date
from pydantic import ValidationError

from backend.extraction.schemas import (
    Supplier, Address, InvoiceInfo, InvoiceItem, Totals,
    Invoice, InvoiceWithMetadata, ExtractionResult,
)


# ─── Supplier ──────────────────────────────────────────────────────
class TestSupplier:
    def test_all_none(self):
        s = Supplier()
        assert s.name is None
        assert s.email is None

    def test_full(self):
        s = Supplier(name="Acme", address="123 Main", tax_id="99", phone="555", email="a@b.c")
        assert s.name == "Acme"


# ─── Address ───────────────────────────────────────────────────────
class TestAddress:
    def test_defaults(self):
        a = Address()
        assert a.company_name is None

    def test_partial(self):
        a = Address(city="NYC", state="NY")
        assert a.city == "NYC"
        assert a.address_line is None


# ─── InvoiceInfo ───────────────────────────────────────────────────
class TestInvoiceInfo:
    def test_date_parsing_valid(self):
        info = InvoiceInfo(invoice_date="2024-03-15")
        assert info.invoice_date == date(2024, 3, 15)

    def test_date_parsing_none_string(self):
        """The custom validator should convert 'None' string to actual None."""
        info = InvoiceInfo(invoice_date="None")
        assert info.invoice_date is None

    def test_date_parsing_empty_string(self):
        info = InvoiceInfo(invoice_date="")
        assert info.invoice_date is None

    def test_date_parsing_null_string(self):
        info = InvoiceInfo(invoice_date="null")
        assert info.invoice_date is None

    def test_date_parsing_actual_none(self):
        info = InvoiceInfo(invoice_date=None)
        assert info.invoice_date is None

    def test_invalid_date_format(self):
        """A truly bad date string (not caught by our validator) should fail Pydantic."""
        with pytest.raises(ValidationError):
            InvoiceInfo(invoice_date="not-a-date")

    def test_default_currency(self):
        info = InvoiceInfo()
        assert info.currency == "USD"


# ─── InvoiceItem ───────────────────────────────────────────────────
class TestInvoiceItem:
    def test_valid_with_description(self):
        item = InvoiceItem(description="Widget", quantity=10, unit_price=5)
        assert item.description == "Widget"

    def test_valid_with_item_code_only(self):
        item = InvoiceItem(item_code="WG-001", quantity=1)
        assert item.item_code == "WG-001"

    def test_fails_without_description_or_code(self):
        """Must have at least one of description or item_code."""
        with pytest.raises(ValidationError, match="description or an item code"):
            InvoiceItem(quantity=10)

    def test_decimal_fields(self):
        item = InvoiceItem(description="A", quantity="10.5", unit_price="3.99")
        assert isinstance(item.quantity, Decimal)
        assert item.quantity == Decimal("10.5")


# ─── Totals ────────────────────────────────────────────────────────
class TestTotals:
    def test_all_none(self):
        t = Totals()
        assert t.total_amount is None

    def test_decimal_conversion(self):
        t = Totals(subtotal="123.45", total_amount="543.21")
        assert t.subtotal == Decimal("123.45")


# ─── Invoice (main model) ─────────────────────────────────────────
class TestInvoice:
    def test_valid_invoice(self, valid_invoice_data):
        inv = Invoice(**valid_invoice_data)
        assert inv.supplier.name == "Acme Corp"
        assert inv.invoice_info.invoice_number == "INV-2024-001"
        assert len(inv.line_items) == 2

    def test_empty_invoice_fails_validation(self, empty_invoice_data):
        """An invoice with absolutely nothing should fail the model_validator."""
        with pytest.raises(ValidationError, match="No supplier name, invoice number, or total amount"):
            Invoice(**empty_invoice_data)

    def test_invoice_passes_with_only_total_amount(self):
        """If we have only total_amount, validation should pass."""
        inv = Invoice(totals={"total_amount": "100.00"})
        assert inv.totals.total_amount == Decimal("100.00")

    def test_invoice_passes_with_only_supplier_name(self):
        inv = Invoice(supplier={"name": "Vendor X"})
        assert inv.supplier.name == "Vendor X"

    def test_invoice_passes_with_only_invoice_number(self):
        inv = Invoice(invoice_info={"invoice_number": "INV-999"})
        assert inv.invoice_info.invoice_number == "INV-999"

    def test_null_subobjects_are_converted(self):
        """The ensure_object validator should convert None -> {} for sub-objects.
        Since all fields are None and line_items only has a description,
        the model_validator should still raise because there's no supplier name,
        invoice number, or total amount — but the NULL conversion itself should work."""
        with pytest.raises(ValidationError, match="No supplier name"):
            Invoice(
                supplier=None,
                invoice_info=None,
                bill_to=None,
                ship_to=None,
                totals=None,
                line_items=[{"description": "test"}],
            )
    def test_null_ship_to_does_not_crash(self):
        """This was a real production bug — ship_to=None from OpenAI."""
        inv = Invoice(
            supplier={"name": "Test Vendor"},
            ship_to=None,
        )
        assert inv.ship_to is not None  # Should be an empty Address object

    def test_null_bill_to_does_not_crash(self):
        inv = Invoice(
            supplier={"name": "Test Vendor"},
            bill_to=None,
        )
        assert inv.bill_to is not None

    def test_null_totals_does_not_crash(self):
        inv = Invoice(
            supplier={"name": "Test Vendor"},
            totals=None,
        )
        assert inv.totals is not None


# ─── InvoiceWithMetadata ──────────────────────────────────────────
class TestInvoiceWithMetadata:
    def test_inherits_from_invoice(self, valid_invoice_data):
        data = {**valid_invoice_data, "metadata": {"file_type": "pdf"}}
        inv = InvoiceWithMetadata(**data)
        assert inv.metadata["file_type"] == "pdf"
        assert inv.supplier.name == "Acme Corp"

    def test_default_metadata_is_empty_dict(self, valid_invoice_data):
        inv = InvoiceWithMetadata(**valid_invoice_data)
        assert inv.metadata == {}


# ─── ExtractionResult ─────────────────────────────────────────────
class TestExtractionResult:
    def test_success(self, valid_invoice_data):
        r = ExtractionResult(
            success=True,
            data=valid_invoice_data,
            attempts=1,
            model_used="gemini_cheap",
        )
        assert r.success is True
        assert r.error is None

    def test_failure(self):
        r = ExtractionResult(
            success=False,
            error="LLM quota exceeded",
            attempts=3,
        )
        assert r.success is False
        assert r.error == "LLM quota exceeded"
