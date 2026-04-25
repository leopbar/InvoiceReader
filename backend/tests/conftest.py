"""
Shared fixtures for backend tests.
"""
import os
import sys
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ─── Fixtures for Pydantic schema tests ────────────────────────────
@pytest.fixture
def valid_invoice_data():
    """Minimal valid invoice data that passes all validators."""
    return {
        "supplier": {"name": "Acme Corp", "address": "123 Main St", "tax_id": "12-3456789"},
        "invoice_info": {
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-03-15",
            "due_date": "2024-04-15",
            "currency": "USD",
            "payment_terms": "Net 30",
        },
        "bill_to": {"company_name": "Client LLC", "city": "New York", "state": "NY"},
        "ship_to": {"company_name": "Client Warehouse"},
        "line_items": [
            {
                "description": "Widget A",
                "quantity": "10",
                "unit_price": "25.00",
                "total_price": "250.00",
            },
            {
                "description": "Widget B",
                "item_code": "WB-100",
                "quantity": "5",
                "unit_price": "50.00",
                "total_price": "250.00",
            },
        ],
        "totals": {
            "subtotal": "500.00",
            "tax_amount": "40.00",
            "total_amount": "540.00",
        },
        "notes": "Thank you for your business!",
    }


@pytest.fixture
def empty_invoice_data():
    """Invoice data where all fields are null/empty — should fail validation."""
    return {
        "supplier": {},
        "invoice_info": {},
        "bill_to": {},
        "ship_to": {},
        "line_items": [],
        "totals": {},
    }
