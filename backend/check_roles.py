import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import supabase_admin

try:
    res = supabase_admin.table('user_roles').select('*').execute()
    print("USER ROLES FROM DB:")
    for role in res.data:
        print(role)
except Exception as e:
    print(f"Error: {e}")
