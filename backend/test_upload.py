import requests

def test_upload():
    test_file_path = "test_invoice.txt"
    
    with open(test_file_path, "w") as f:
        f.write("INVOICE\nSupplier: Test Supplier Inc.\nTotal: $500.00")
        
    url = "http://localhost:8000/api/upload"
    
    with open(test_file_path, "rb") as f:
        files = {"file": ("test_invoice.txt", f, "text/plain")}
        print(f"Sending request to {url}...")
        response = requests.post(url, files=files)
        
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:")
        print(response.json())
    except:
        print("Response Text:")
        print(response.text)

if __name__ == "__main__":
    test_upload()
    
