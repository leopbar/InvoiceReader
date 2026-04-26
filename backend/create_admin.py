"""
Admin Bootstrap Script for InvoiceReader

This script creates the initial admin user in the Supabase authentication system 
and assigns them the 'admin' role in the 'user_roles' table.

SECURITY:
Credentials are read from environment variables to avoid hardcoding secrets in source code.
Ensure you have set the following in your 'backend/.env' file:
- ADMIN_EMAIL
- ADMIN_PASSWORD (minimum 8 characters)

Usage:
    cd backend
    python create_admin.py
"""
import os
import sys

# Add parent dir to path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import supabase_admin

def setup_admin():
    """
    Reads admin credentials from environment variables and bootstraps the initial admin user.
    """
    if not supabase_admin:
        print("Error: SUPABASE_SERVICE_ROLE_KEY is missing from .env")
        return
        
    # Read credentials from environment variables
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    
    # Validation
    if not email or not password:
        print("\n[!] ERROR: Missing Admin Credentials")
        print("Please add ADMIN_EMAIL and ADMIN_PASSWORD to your 'backend/.env' file.")
        return

    if len(password) < 8:
        print("\n[!] ERROR: Weak Password")
        print("ADMIN_PASSWORD must be at least 8 characters long.")
        return
    
    print(f"Creating admin user: {email}...")
    try:
        # 1. Create auth user
        user_res = supabase_admin.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        
        user_id = user_res.user.id
        print(f"User created in auth.users with ID: {user_id}")
        
        # 2. Add to user_roles
        # Note: Needs user_roles table to exist:
        # CREATE TABLE user_roles (user_id UUID PRIMARY KEY, email TEXT, role TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());
        supabase_admin.table('user_roles').insert({
            'user_id': user_id,
            'email': email,
            'role': 'admin'
        }).execute()
        
        print("Successfully assigned 'admin' role in user_roles table.")
        print(f"\nAdmin Account Created!")
        print(f"Email: {email}")
        print("Password: [SECURE] (Loaded from environment variable)")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        print("\nNote: If error mentions relation 'user_roles' does not exist, remember to run the SQL in your Supabase SQL editor.")

if __name__ == "__main__":
    setup_admin()
