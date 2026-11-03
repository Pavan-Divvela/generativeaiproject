-- Schema for Aadhaar, PAN, and Passport Process Helper

CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL, -- aadhaar, pan, passport
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    mode TEXT NOT NULL, -- Online, In-Person, Hybrid
    fee TEXT NOT NULL,
    timeline TEXT NOT NULL,
    official_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS acceptable_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL, -- aadhaar, pan, passport, universal
    proof_type TEXT NOT NULL, -- PoI (Identity), PoA (Address), PoB (Date of Birth), PoR (Relationship), Non-ECR
    document_name TEXT NOT NULL,
    issuer TEXT,
    notes TEXT,
    is_popular INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS discrepancy_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_type TEXT NOT NULL,
    affected_docs TEXT NOT NULL,
    severity TEXT NOT NULL, -- Low, Medium, High
    explanation TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    affidavit_required INTEGER DEFAULT 0,
    gazette_required INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS faqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    tags TEXT
);

CREATE INDEX IF NOT EXISTS idx_services_category ON services(category);
CREATE INDEX IF NOT EXISTS idx_docs_category_proof ON acceptable_documents(category, proof_type);
CREATE INDEX IF NOT EXISTS idx_faqs_category ON faqs(category);

-- Authentication & User Management
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'citizen',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_saved_checklists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    service_code TEXT NOT NULL,
    service_title TEXT NOT NULL,
    items_checked INTEGER DEFAULT 0,
    total_items INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, service_code)
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(token);
CREATE INDEX IF NOT EXISTS idx_user_checklists_user ON user_saved_checklists(user_id);
