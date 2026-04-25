"""
Upload multiple invoice formats via API to test extraction across file types.
"""
import requests
import json
import os
from dotenv import load_dotenv
from supabase import create_client

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_URL = "http://127.0.0.1:8000/api"

# Auth
sb = create_client(SUPABASE_URL, SUPABASE_KEY)
auth_res = sb.auth.sign_in_with_password({"email": "testbot@bot.com", "password": "1xpto1!"})
token = auth_res.session.access_token
headers = {"Authorization": f"Bearer {token}"}

# Files to test
test_files = [
    (r"C:\Users\lpbar\Downloads\invoices\invoice_skyfield_agtech.pdf", "application/pdf"),
    (r"C:\Users\lpbar\Downloads\invoices\Professional_Invoice_USD.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    (r"C:\Users\lpbar\Downloads\invoices\ChatGPT Image Apr 23, 2026, 08_36_09 PM.png", "image/png"),
]

all_results = []

for filepath, mime_type in test_files:
    fname = os.path.basename(filepath)
    print(f"\n{'='*60}")
    print(f"TESTING: {fname} ({mime_type})")
    print(f"{'='*60}")
    
    try:
        with open(filepath, "rb") as f:
            files = {"file": (fname, f, mime_type)}
            r = requests.post(f"{API_URL}/upload", files=files, headers=headers, timeout=120)
        
        result = r.json()
        success = result.get("success", False)
        
        print(f"  Status: {r.status_code}")
        print(f"  4.1 Extraction: {'PASS' if success else 'FAIL'}")
        
        if success and result.get("data"):
            data = result["data"]
            supplier = data.get("supplier", {})
            inv_info = data.get("invoice_info", {})
            line_items = data.get("line_items", [])
            totals = data.get("totals", {})
            bill_to = data.get("bill_to", {})
            
            tests = {
                "4.2 Supplier": bool(supplier and supplier.get("name")),
                "4.3 Invoice #": bool(inv_info and inv_info.get("invoice_number")),
                "4.4 Line Items": len(line_items) > 0,
                "4.5 Total Amount": bool(totals and totals.get("total_amount")),
                "4.6 Bill To": bool(bill_to and any(v for v in bill_to.values() if v)),
            }
            
            for test_name, passed in tests.items():
                status = "PASS" if passed else "FAIL"
                print(f"  {test_name}: {status}")
            
            print(f"  Supplier: {supplier.get('name')}")
            print(f"  Invoice#: {inv_info.get('invoice_number')}")
            print(f"  Items: {len(line_items)}")
            print(f"  Total: {totals.get('total_amount')} {inv_info.get('currency', 'USD')}")
            print(f"  Model: {result.get('model_used')}")
            
            # Auto-save
            save_r = requests.post(f"{API_URL}/save", json={"data": data}, headers=headers, timeout=30)
            save_ok = save_r.status_code == 200
            print(f"  4.7 Auto-Save: {'PASS' if save_ok else 'FAIL'} - id={save_r.json().get('invoice_id', 'N/A')}")
            
            passed_count = sum(1 for v in tests.values() if v) + (1 if save_ok else 0) + 1  # +1 for extraction
            all_results.append((fname, passed_count, 7))
        else:
            print(f"  ERROR: {result.get('error')}")
            all_results.append((fname, 0, 7))
            
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        all_results.append((fname, 0, 7))

# Final summary
print(f"\n{'='*60}")
print(f"MULTI-FORMAT TEST SUMMARY")
print(f"{'='*60}")
for fname, passed, total in all_results:
    status = "PASS" if passed >= 6 else "PARTIAL" if passed > 0 else "FAIL"
    print(f"  {status} {fname}: {passed}/{total} tests passed")

total_passed = sum(p for _, p, _ in all_results)
total_tests = sum(t for _, _, t in all_results)
print(f"\n  TOTAL: {total_passed}/{total_tests} tests passed across {len(all_results)} file formats")
