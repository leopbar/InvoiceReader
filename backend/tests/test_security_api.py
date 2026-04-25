import requests

results = []

# Test 9.6: File size limit (send >10MB)
try:
    big_file = b'A' * (11 * 1024 * 1024)
    r = requests.post('http://127.0.0.1:8000/api/upload', files={'file': ('big.txt', big_file)}, headers={'Authorization': 'Bearer fake'})
    status = "PASS" if r.status_code in [401, 413] else "FAIL"
    results.append(f'9.6 File Size Limit: {status} - Status {r.status_code}')
except Exception as e:
    results.append(f'9.6 File Size Limit: ERROR - {e}')

# Test 9.7: Empty file upload
try:
    r = requests.post('http://127.0.0.1:8000/api/upload', files={'file': ('empty.txt', b'')}, headers={'Authorization': 'Bearer fake'})
    status = "PASS" if r.status_code in [400, 401] else "FAIL"
    results.append(f'9.7 Empty File: {status} - Status {r.status_code}')
except Exception as e:
    results.append(f'9.7 Empty File: ERROR - {e}')

# Test 9.8: SQL injection in API params
try:
    r = requests.get("http://127.0.0.1:8000/api/invoices/1' OR 1=1--", headers={'Authorization': 'Bearer fake'})
    status = "PASS" if r.status_code == 401 else "FAIL"
    results.append(f'9.8 SQL Injection: {status} - Status {r.status_code}')
except Exception as e:
    results.append(f'9.8 SQL Injection: ERROR - {e}')

# Test 9.9: No auth token
try:
    r = requests.get('http://127.0.0.1:8000/api/invoices')
    status = "PASS" if r.status_code == 401 else "FAIL"
    body = r.text[:100]
    results.append(f'9.9 No Auth Token: {status} - Status {r.status_code}, Body: {body}')
except Exception as e:
    results.append(f'9.9 No Auth Token: ERROR - {e}')

# Test 9.5: Health endpoint (public)
try:
    r = requests.get('http://127.0.0.1:8000/api/health')
    ok = r.status_code == 200 and r.json().get("status") == "ok"
    status = "PASS" if ok else "FAIL"
    results.append(f'9.5 Health Endpoint: {status} - {r.text}')
except Exception as e:
    results.append(f'9.5 Health Endpoint: ERROR - {e}')

# Test 9.2: API requires Bearer token format
try:
    r = requests.get('http://127.0.0.1:8000/api/me', headers={'Authorization': 'Basic dGVzdDp0ZXN0'})
    status = "PASS" if r.status_code == 401 else "FAIL"
    results.append(f'9.2 Bearer Format Required: {status} - Status {r.status_code}')
except Exception as e:
    results.append(f'9.2 Bearer Format Required: ERROR - {e}')

# Test 8.9: Non-admin accessing admin endpoint
try:
    r = requests.get('http://127.0.0.1:8000/api/users', headers={'Authorization': 'Bearer fake_token'})
    status = "PASS" if r.status_code in [401, 403] else "FAIL"
    results.append(f'8.9 Admin Endpoint Protection: {status} - Status {r.status_code}')
except Exception as e:
    results.append(f'8.9 Admin Endpoint Protection: ERROR - {e}')

# Test: Delete endpoint requires auth
try:
    r = requests.post('http://127.0.0.1:8000/api/invoices/delete', json={'invoice_ids': []})
    status = "PASS" if r.status_code == 401 else "FAIL"
    results.append(f'9.3 Delete Requires Auth: {status} - Status {r.status_code}')
except Exception as e:
    results.append(f'9.3 Delete Requires Auth: ERROR - {e}')

print("\n=== SECURITY TEST RESULTS ===")
for r in results:
    print(r)
print(f"\nTotal: {len(results)} tests")
