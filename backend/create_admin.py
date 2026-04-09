import os
import sys

# Add parent dir to path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import supabase_admin

def setup_admin():
    if not supabase_admin:
        print("Error: SUPABASE_SERVICE_ROLE_KEY is missing from .env")
        return
        
    email = "lbarretti@gmail.com"
    password = "InvoiceAdmin2024!"
    
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
        print(f"\nAdmin Account Created!\nEmail: {email}\nPassword: {password}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Note: If error mentions relation 'user_roles' does not exist, remember to run the SQL in your Supabase SQL editor.")

if __name__ == "__main__":
    setup_admin()
