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
        "invoice_date": inv_info.get("invoice_date") or None,
        "due_date": inv_info.get("due_date") or None,
        "currency": inv_info.get("currency") or "USD",
        "subtotal": totals.get("subtotal"),
        "tax_amount": totals.get("tax_amount"),
        "discount": totals.get("discount"),
        "total_amount": totals.get("total_amount"),
        "payment_terms": inv_info.get("payment_terms"),
        "purchase_order": inv_info.get("purchase_order"),
        "notes": data.get("notes"),
        "original_filename": data.get("original_filename"),
        "status": "processed"
    }
    
    try:
        inv_res = supabase.table("invoices").insert(invoice_record).execute()
        if not inv_res.data:
            logger.error(f"Supabase Insert Error: {inv_res}")
            raise Exception("Failed to insert invoice record - no data returned.")
    except Exception as e:
        logger.error(f"Supabase Exception in save_invoice (invoices table): {str(e)}")
        raise e
        
    invoice_id = inv_res.data[0]["id"]
    
    # 3. Line Items
    line_items = data.get("line_items", [])
    if line_items:
        items_to_insert = []
        for item in line_items:
            # Ensure numeric fields are actually numbers or None
            try:
                qty = float(item.get("quantity")) if item.get("quantity") is not None else None
                u_price = float(item.get("unit_price")) if item.get("unit_price") is not None else None
                t_price = float(item.get("total_price")) if item.get("total_price") is not None else None
            except (ValueError, TypeError):
                qty, u_price, t_price = None, None, None

            items_to_insert.append({
                "invoice_id": invoice_id,
                "description": item.get("description"),
                "quantity": qty,
                "unit_price": u_price,
                "total_price": t_price,
                "item_code": item.get("item_code"),
                "unit": item.get("unit")
            })
        
        if items_to_insert:
            try:
                supabase.table("invoice_items").insert(items_to_insert).execute()
            except Exception as e:
                logger.error(f"Supabase Exception in save_invoice (invoice_items table): {str(e)}")
                # We don't necessarily want to fail the whole thing if just items fail, 
                # but for data integrity we might. Let's log it.
        
    # 4. Addresses
    addresses = []
    bill_to = data.get("bill_to", {})
    if bill_to and any(v for k, v in bill_to.items() if k != "invoice_id"):
        bill_to_record = {k: v for k, v in bill_to.items() if k not in ["invoice_id", "address_type"]}
        bill_to_record["invoice_id"] = invoice_id
        bill_to_record["address_type"] = "bill_to"
        addresses.append(bill_to_record)
        
    ship_to = data.get("ship_to", {})
    if ship_to and any(v for k, v in ship_to.items() if k != "invoice_id"):
        ship_to_record = {k: v for k, v in ship_to.items() if k not in ["invoice_id", "address_type"]}
        ship_to_record["invoice_id"] = invoice_id
        ship_to_record["address_type"] = "ship_to"
        addresses.append(ship_to_record)
        
    if addresses:
        try:
            supabase.table("invoice_addresses").insert(addresses).execute()
        except Exception as e:
            logger.error(f"Supabase Exception in save_invoice (invoice_addresses table): {str(e)}")
        
    return invoice_id

def get_processing_stats() -> dict:
    """Fetch the global processing stats from the database."""
    try:
        res = supabase.table("processing_stats").select("*").eq("id", "global").execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except Exception:
        pass
    return None

def update_processing_stats(stats: dict):
    """Upsert the global processing stats into the database."""
    try:
        stats["id"] = "global"
        supabase.table("processing_stats").upsert(stats).execute()
    except Exception:
        # If table doesn't exist yet or other error, just ignore
        pass

def delete_invoice_by_filename(filename: str):
    """Removes all data related to an invoice based on its original filename."""
    try:
        # 1. Find the invoice(s) with this filename
        res = supabase.table("invoices").select("id").eq("original_filename", filename).execute()
        if res.data:
            invoice_ids = [row["id"] for row in res.data]
            
            # 2. Delete children first (in case cascade is not set in DB)
            supabase.table("invoice_items").delete().in_("invoice_id", invoice_ids).execute()
            supabase.table("invoice_addresses").delete().in_("invoice_id", invoice_ids).execute()
            
            # 3. Delete the invoices
            supabase.table("invoices").delete().in_("id", invoice_ids).execute()
            logger.info(f"Successfully deleted {len(invoice_ids)} record(s) for {filename}")
    except Exception as e:
        logger.error(f"Error deleting invoice by filename {filename}: {e}")
        # Don't re-raise to avoid breaking the main workflow if cleanup fails
