from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Invoice Reader API")

class InvoiceRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Invoice Reader API"}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/parse")
def parse_invoice(request: InvoiceRequest):
    # Placeholder for actual invoice parsing logic
    return {"parsed": True, "original_text": request.text}
