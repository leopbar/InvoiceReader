import os
import logging
import traceback
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from backend.file_processor import process_file
from backend.gemini_service import extract_invoice_data
from backend.supabase_service import save_invoice
from backend.database import supabase, supabase_admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("invoice_reader")

environment = os.environ.get("ENVIRONMENT", "production")

if environment == "production":
    app = FastAPI(title="Invoice Reader API", docs_url=None, redoc_url=None)
else:
    app = FastAPI(title="Invoice Reader API")

# CORS: broaden origins for local development
_cors_origins_raw = os.environ.get("CORS_ORIGINS", "*")
if _cors_origins_raw == "*":
    CORS_ORIGINS = ["*"]
else:
    CORS_ORIGINS = [origin.strip() for origin in _cors_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True if CORS_ORIGINS != ["*"] else False, # Credentials cannot be used with "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug middleware to log all requests
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Incoming request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        print(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        print(f"Request failed: {str(e)}")
        raise e

# Max upload size: 10 MB
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

# Authentication Dependency
def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized: Missing or invalid Bearer token")
    token = authorization.split(" ")[1]
    
    try:
        user_res = supabase.auth.get_user(token)
        if not user_res or not user_res.user:
            raise HTTPException(status_code=401, detail="Unauthorized: Invalid token")
        return user_res.user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")

# Require Admin check
def verify_admin(user = Depends(verify_token)):
    if not supabase_admin:
        logger.error("supabase_admin client is not configured. Check SUPABASE_SERVICE_ROLE_KEY in .env")
        raise HTTPException(status_code=500, detail="Internal admin client configuration missing")
        
    try:
        role_res = supabase_admin.table("user_roles").select("role").eq("user_id", user.id).execute()
        
        if not role_res.data or role_res.data[0]["role"] != "admin":
            raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
            
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying admin role: {traceback.format_exc()}")
        raise HTTPException(status_code=403, detail="Forbidden: Admin access verification failed")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Invoice Reader API"}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/me")
def get_me(user = Depends(verify_token)):
    try:
        # We skip RLS by using supabase_admin to check for the user's role
        role_res = supabase_admin.table("user_roles").select("role").eq("user_id", user.id).execute()
        role = role_res.data[0]["role"] if role_res.data else "user"
        return {"id": user.id, "email": user.email, "role": role}
    except Exception as e:
        logger.error(f"Error fetching user role: {str(e)}")
        # Default to user role if check fails
        return {"id": user.id, "email": user.email, "role": "user"}

@app.post("/api/upload")
async def upload_invoice(file: UploadFile = File(...), user = Depends(verify_token)):
    try:
        # Read file with size limit enforcement
        file_bytes = await file.read()
        if len(file_bytes) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE // (1024*1024)} MB.")
        
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        
        filename = file.filename
        
        extracted = process_file(file_bytes, filename)
        text = extracted.get("text")
        image_base64 = extracted.get("image_base64")
        
        if not text and not image_base64:
            raise HTTPException(status_code=400, detail="Could not extract text or image from file.")
            
        invoice_json = extract_invoice_data(text=text, image_base64=image_base64)
        
        invoice_json["metadata"] = {
            "original_filename": filename,
            "file_type": extracted.get("file_type")
        }
        
        return invoice_json
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading invoice: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

class SaveInvoiceRequest(BaseModel):
    data: dict

@app.post("/api/save")
def save_extracted_invoice(request: SaveInvoiceRequest, user = Depends(verify_token)):
    try:
        data = request.data
        invoice_id = save_invoice(data)
        
        metadata = data.get("metadata", {})
        if metadata:
            supabase.table("invoices").update({
                "original_filename": metadata.get("original_filename"),
                "file_type": metadata.get("file_type")
            }).eq("id", invoice_id).execute()
            
        return {"status": "success", "invoice_id": invoice_id}
    except Exception as e:
        logger.error(f"Error saving invoice: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/invoices")
def list_invoices(user = Depends(verify_token)):
    try:
        res = supabase.table("invoices").select("*, suppliers(*), invoice_addresses(*)").execute()
        return {"invoices": res.data}
    except Exception as e:
        logger.error(f"Error listing invoices: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

class DeleteInvoicesRequest(BaseModel):
    invoice_ids: list[str]

@app.post("/api/invoices/delete")
def delete_invoices(request: DeleteInvoicesRequest, user = Depends(verify_token)):
    try:
        if not request.invoice_ids:
            return {"status": "success", "deleted": 0}
            
        res = supabase.table("invoices").delete().in_("id", request.invoice_ids).execute()
        return {"status": "success", "deleted": len(request.invoice_ids)}
    except Exception as e:
        logger.error(f"Error deleting invoices: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/invoices/{id}")
def get_invoice(id: str, user = Depends(verify_token)):
    try:
        inv_res = supabase.table("invoices").select("*, suppliers(*)").eq("id", id).execute()
        if not inv_res.data:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        invoice = inv_res.data[0]
        
        items_res = supabase.table("invoice_items").select("*").eq("invoice_id", id).execute()
        invoice["items"] = items_res.data
        
        addr_res = supabase.table("invoice_addresses").select("*").eq("invoice_id", id).execute()
        invoice["addresses"] = addr_res.data
        
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invoice: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# ================= USER MANAGEMENT ENDPOINTS ================= #

class UserCreate(BaseModel):
    email: str
    password: str
    role: str

@app.get("/api/users")
def get_all_users(admin_user = Depends(verify_admin)):
    if not supabase_admin:
        raise HTTPException(status_code=500, detail="Admin client not configured")
    try:
        res = supabase_admin.table("user_roles").select("*").execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users")
def create_new_user(user_data: UserCreate, admin_user = Depends(verify_admin)):
    if not supabase_admin:
        raise HTTPException(status_code=500, detail="Admin client not configured")
    try:
        new_user = supabase_admin.auth.admin.create_user({
            "email": user_data.email,
            "password": user_data.password,
            "email_confirm": True
        })
        new_uid = new_user.user.id
        
        supabase_admin.table("user_roles").insert({
            "user_id": new_uid,
            "email": user_data.email,
            "role": user_data.role
        }).execute()
        
        return {"status": "success", "user_id": new_uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/users/{target_id}")
def delete_system_user(target_id: str, admin_user = Depends(verify_admin)):
    if target_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    if not supabase_admin:
        raise HTTPException(status_code=500, detail="Admin client not configured")
        
    try:
        supabase_admin.auth.admin.delete_user(target_id)
        # Manual cleanup just in case ON DELETE CASCADE is not set
        supabase_admin.table("user_roles").delete().eq("user_id", target_id).execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)
