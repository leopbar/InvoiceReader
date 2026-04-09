from backend.database import supabase

def save_invoice(data: dict) -> str:
    # 1. Supplier
    supplier_data = data.get("supplier", {})
    supplier_name = supplier_data.get("name")
    
    supplier_id = None
    if supplier_name:
        # Check if supplier exists
        supp_res = supabase.table("suppliers").select("id").eq("name", supplier_name).execute()
        if supp_res.data and len(supp_res.data) > 0:
            supplier_id = supp_res.data[0]["id"]
        else:
            # Insert new supplier
            new_supp = supabase.table("suppliers").insert({
                "name": supplier_name,
                "address": supplier_data.get("address"),
                "email": supplier_data.get("email"),
                "phone": supplier_data.get("phone"),
                "tax_id": supplier_data.get("tax_id")
            }).execute()
            if new_supp.data:
                supplier_id = new_supp.data[0]["id"]
            
    # 2. Invoice
    inv_info = data.get("invoice_info", {})
    totals = data.get("totals", {})
    
    invoice_record = {
        "supplier_id": supplier_id,
        "invoice_number": inv_info.get("invoice_number"),
        "invoice_date": inv_info.get("invoice_date"),
        "due_date": inv_info.get("due_date"),
        "currency": inv_info.get("currency") or "USD",
        "subtotal": totals.get("subtotal"),
        "tax_amount": totals.get("tax_amount"),
        "discount": totals.get("discount"),
        "total_amount": totals.get("total_amount"),
        "payment_terms": inv_info.get("payment_terms"),
        "purchase_order": inv_info.get("purchase_order"),
        "notes": data.get("notes"),
        "status": "processed"
    }
    
    inv_res = supabase.table("invoices").insert(invoice_record).execute()
    if not inv_res.data:
        raise Exception("Failed to insert invoice")
        
    invoice_id = inv_res.data[0]["id"]
    
    # 3. Line Items
    line_items = data.get("line_items", [])
    if line_items:
        items_to_insert = []
        for item in line_items:
            items_to_insert.append({
                "invoice_id": invoice_id,
                "description": item.get("description"),
                "quantity": item.get("quantity"),
                "unit_price": item.get("unit_price"),
                "total_price": item.get("total_price"),
                "item_code": item.get("item_code"),
                "unit": item.get("unit")
            })
        supabase.table("invoice_items").insert(items_to_insert).execute()
        
    # 4. Addresses
    addresses = []
    bill_to = data.get("bill_to", {})
    if bill_to and any(bill_to.values()):
        bill_to["invoice_id"] = invoice_id
        bill_to["address_type"] = "bill_to"
        addresses.append(bill_to)
        
    ship_to = data.get("ship_to", {})
    if ship_to and any(ship_to.values()):
        ship_to["invoice_id"] = invoice_id
        ship_to["address_type"] = "ship_to"
        addresses.append(ship_to)
        
    if addresses:
        supabase.table("invoice_addresses").insert(addresses).execute()
        
    return invoice_id
