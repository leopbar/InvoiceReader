"""
Upload a real invoice file via the API and verify the extraction results.
This simulates what the frontend does when a user uploads a file.
"""
import requests
import json
import os
from dotenv import load_dotenv
from supabase import create_client

# Load env for Supabase auth
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_URL = "http://127.0.0.1:8000/api"

# Step 1: Get auth token
print("=== Step 1: Authenticating as testbot@bot.com ===")
sb = create_client(SUPABASE_URL, SUPABASE_KEY)
auth_res = sb.auth.sign_in_with_password({"email": "testbot@bot.com", "password": "1xpto1!"})
token = auth_res.session.access_token
print(f"Auth: OK (token starts with {token[:20]}...)")
headers = {"Authorization": f"Bearer {token}"}

# Step 2: Upload the TXT invoice
invoice_path = r"C:\Users\lpbar\Downloads\invoices\invoice_ironclad_security.txt"
print(f"\n=== Step 2: Uploading {os.path.basename(invoice_path)} ===")

with open(invoice_path, "rb") as f:
    files = {"file": (os.path.basename(invoice_path), f, "text/plain")}
    r = requests.post(f"{API_URL}/upload", files=files, headers=headers, timeout=120)

print(f"Status: {r.status_code}")
result = r.json()

# Test 4.1: Extraction succeeded
success = result.get("success", False)
print(f"\n=== TEST RESULTS ===")
print(f"4.1 Extraction Succeeded: {'PASS' if success else 'FAIL'} - success={success}")

if success and result.get("data"):
    data = result["data"]
    
    # Test 4.2: Supplier info
    supplier = data.get("supplier", {})
    has_supplier = bool(supplier and supplier.get("name"))
    print(f"4.2 Supplier Info: {'PASS' if has_supplier else 'FAIL'} - name={supplier.get('name')}")
    
    # Test 4.3: Invoice number
    inv_info = data.get("invoice_info", {})
    has_inv_num = bool(inv_info and inv_info.get("invoice_number"))
    print(f"4.3 Invoice Number: {'PASS' if has_inv_num else 'FAIL'} - number={inv_info.get('invoice_number')}")
    
    # Test 4.4: Line items
    line_items = data.get("line_items", [])
    has_items = len(line_items) > 0
    print(f"4.4 Line Items: {'PASS' if has_items else 'FAIL'} - count={len(line_items)}")
    if has_items:
        for i, item in enumerate(line_items[:3]):
            print(f"     Item {i+1}: {item.get('description', 'N/A')} - qty={item.get('quantity')} x ${item.get('unit_price')} = ${item.get('total_price')}")
    
    # Test 4.5: Totals
    totals = data.get("totals", {})
    has_total = bool(totals and totals.get("total_amount"))
    print(f"4.5 Total Amount: {'PASS' if has_total else 'FAIL'} - total={totals.get('total_amount')}")
    
    # Test 4.6: Bill To address
    bill_to = data.get("bill_to", {})
    has_bill_to = bool(bill_to and any(bill_to.values()))
    print(f"4.6 Bill To: {'PASS' if has_bill_to else 'FAIL'} - company={bill_to.get('company_name')}")
    
    # Test 4.11: Notes
    notes = data.get("notes")
    has_notes = bool(notes)
    print(f"4.11 Notes: {'PASS' if has_notes else 'FAIL'} - notes={notes[:50] if notes else 'N/A'}...")
    
    # Test 4.12: Currency
    currency = inv_info.get("currency")
    has_currency = bool(currency)
    print(f"4.12 Currency: {'PASS' if has_currency else 'FAIL'} - currency={currency}")
    
    # Model info
    print(f"\nModel Used: {result.get('model_used')}")
    print(f"Attempts: {result.get('attempts')}")
    
    # Step 3: Auto-save to database
    print(f"\n=== Step 3: Saving to Database (simulating auto-save) ===")
    save_payload = {"data": data}
    r_save = requests.post(f"{API_URL}/save", json=save_payload, headers=headers, timeout=30)
    save_result = r_save.json()
    saved_ok = r_save.status_code == 200 and save_result.get("status") == "success"
    print(f"4.7 Auto-Save: {'PASS' if saved_ok else 'FAIL'} - status={save_result.get('status')}, id={save_result.get('invoice_id')}")
    
else:
    print(f"EXTRACTION FAILED: {result.get('error')}")
    print(f"Validation errors: {result.get('validation_errors')}")

# Print summary
print(f"\n=== SUMMARY ===")
print(f"All extraction tests completed. Check results above.")
