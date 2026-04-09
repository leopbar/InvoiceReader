-- Run this entire script in the Supabase SQL Editor on your dashboard.
-- Creating tables programmatically with the "anon_key" is blocked for security reasons.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT,
    address TEXT,
    email TEXT,
    phone TEXT,
    tax_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID REFERENCES suppliers(id),
    invoice_number TEXT,
    invoice_date DATE,
    due_date DATE,
    currency TEXT DEFAULT 'USD',
    subtotal DECIMAL,
    tax_amount DECIMAL,
    discount DECIMAL,
    total_amount DECIMAL,
    payment_terms TEXT,
    purchase_order TEXT,
    notes TEXT,
    original_filename TEXT,
    file_type TEXT,
    raw_extracted_text TEXT,
    status TEXT DEFAULT 'processed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create invoice_items table
CREATE TABLE IF NOT EXISTS invoice_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT,
    quantity DECIMAL,
    unit_price DECIMAL,
    total_price DECIMAL,
    item_code TEXT,
    unit TEXT
);

-- 4. Create invoice_addresses table
CREATE TABLE IF NOT EXISTS invoice_addresses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE,
    address_type TEXT CHECK (address_type IN ('bill_to', 'ship_to')),
    company_name TEXT,
    address_line TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    country TEXT
);

-- 5. Enable Row Level Security (RLS) on all tables
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_addresses ENABLE ROW LEVEL SECURITY;

-- 6. Create Open Policies (For Initial Development Only)
CREATE POLICY "Allow all operations for everyone" ON suppliers FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations for everyone" ON invoices FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations for everyone" ON invoice_items FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations for everyone" ON invoice_addresses FOR ALL USING (true) WITH CHECK (true);

-- 7. Create User Roles table for Auth (Admin/User mgmt)
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS and simple policy for user_roles
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all operations for everyone" ON user_roles FOR ALL USING (true) WITH CHECK (true);
