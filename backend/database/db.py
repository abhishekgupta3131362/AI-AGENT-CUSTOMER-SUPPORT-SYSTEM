import sqlite3
import json
from pathlib import Path
from backend.config import Config

def get_db_connection():
    """Returns a SQLite connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(str(Config.DATABASE_PATH), timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn

def init_db():
    """Initializes tables in the SQLite database if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Customers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            tier TEXT DEFAULT 'Standard',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Orders Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            items TEXT NOT NULL,
            total_amount REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            status TEXT NOT NULL,
            shipping_carrier TEXT,
            tracking_number TEXT,
            estimated_delivery TEXT,
            order_date TEXT NOT NULL,
            is_refundable INTEGER DEFAULT 1,
            platform TEXT DEFAULT 'ApexTech',
            courier_hub TEXT DEFAULT 'Main Logistics Hub',
            payment_method TEXT DEFAULT 'Prepaid',
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # Ensure backward-compatible migrations for existing SQLite databases
    for col_def in [
        ("platform", "TEXT DEFAULT 'ApexTech'"),
        ("courier_hub", "TEXT DEFAULT 'Main Logistics Hub'"),
        ("payment_method", "TEXT DEFAULT 'Prepaid'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE orders ADD COLUMN {col_def[0]} {col_def[1]}")
        except sqlite3.OperationalError:
            pass # Column already exists
    
    # 3. Support Tickets Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            customer_id TEXT,
            customer_email TEXT,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT DEFAULT 'MEDIUM',
            status TEXT DEFAULT 'OPEN',
            assigned_agent TEXT DEFAULT 'AI Agent',
            resolution_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)
    
    # 4. Chat Sessions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            customer_id TEXT,
            customer_name TEXT,
            sentiment_score REAL DEFAULT 0.0,
            sentiment_label TEXT DEFAULT 'Neutral',
            csat_rating INTEGER,
            csat_feedback TEXT,
            is_human_takeover INTEGER DEFAULT 0,
            active_human_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 5. Chat Messages Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            sender_name TEXT,
            content TEXT NOT NULL,
            tool_calls TEXT,
            sentiment_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
        )
    """)
    
    # 6. Knowledge Documents Table (Chunked & Vector Indexed)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            chunk_index INTEGER DEFAULT 0,
            embedding TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 7. Hotel Rooms Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotel_rooms (
            id TEXT PRIMARY KEY,
            room_type TEXT NOT NULL,
            price_per_night REAL NOT NULL,
            max_guests INTEGER DEFAULT 2,
            available_count INTEGER DEFAULT 5,
            amenities TEXT,
            description TEXT
        )
    """)

    # 8. Hotel Reservations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotel_reservations (
            id TEXT PRIMARY KEY,
            guest_name TEXT NOT NULL,
            room_id TEXT NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            status TEXT DEFAULT 'CONFIRMED',
            special_requests TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES hotel_rooms(id)
        )
    """)

    # 9. SaaS Error Codes & Troubleshooting Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saas_error_docs (
            code TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            severity TEXT DEFAULT 'MEDIUM',
            cause TEXT NOT NULL,
            solution TEXT NOT NULL,
            code_sample TEXT
        )
    """)

    # Safe column additions for existing databases
    for col_def in [
        ("chat_sessions", "sentiment_score REAL DEFAULT 0.0"),
        ("chat_sessions", "sentiment_label TEXT DEFAULT 'Neutral'"),
        ("chat_sessions", "csat_rating INTEGER"),
        ("chat_sessions", "csat_feedback TEXT"),
        ("chat_sessions", "is_human_takeover INTEGER DEFAULT 0"),
        ("chat_sessions", "active_human_agent TEXT"),
        ("chat_messages", "sender_name TEXT"),
        ("chat_messages", "sentiment_score REAL")
    ]:
        try:
            cursor.execute(f"ALTER TABLE {col_def[0]} ADD COLUMN {col_def[1]}")
        except Exception:
            pass # Column already exists

    # 10. Performance Indexes for high-throughput concurrency
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_platform ON orders(platform)",
        "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
        "CREATE INDEX IF NOT EXISTS idx_tickets_customer ON tickets(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)",
        "CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority)",
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_customer ON chat_sessions(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_documents(category)",
        "CREATE INDEX IF NOT EXISTS idx_hotel_reservations_room ON hotel_reservations(room_id)",
        "CREATE INDEX IF NOT EXISTS idx_saas_docs_code ON saas_error_docs(code)"
    ]
    for idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
        except Exception:
            pass
    
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False):
    """Executes a SELECT query and returns dict results."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        result = [dict(row) for row in rv]
        return (result[0] if result else None) if one else result
    finally:
        conn.close()

def execute_db(query, args=()):
    """Executes an INSERT, UPDATE, or DELETE query and commits."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def get_db_stats():
    """Returns database integrity status, table names, row counts, and disk size."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check")
        integrity_row = cur.fetchone()
        integrity = integrity_row[0] if integrity_row else "unknown"

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]

        counts = {}
        for tbl in tables:
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            counts[tbl] = cur.fetchone()[0]

        db_path = Path(Config.DATABASE_PATH)
        file_size_bytes = db_path.stat().st_size if db_path.exists() else 0

        # Check WAL mode
        cur.execute("PRAGMA journal_mode")
        journal_mode = cur.fetchone()[0]

        return {
            "path": str(db_path),
            "integrity": integrity,
            "journal_mode": journal_mode,
            "size_bytes": file_size_bytes,
            "size_kb": round(file_size_bytes / 1024, 2),
            "tables_count": len(tables),
            "tables": counts
        }
    finally:
        conn.close()

def optimize_db():
    """Runs VACUUM and ANALYZE to optimize SQLite database file and indices."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA optimize")
        conn.commit()
        return True
    finally:
        conn.close()

def verify_db_integrity():
    """Runs foreign key check and integrity check on database."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check")
        integrity = cur.fetchone()[0]
        cur.execute("PRAGMA foreign_key_check")
        fk_violations = cur.fetchall()
        return {
            "healthy": integrity == "ok" and len(fk_violations) == 0,
            "integrity": integrity,
            "foreign_key_violations": len(fk_violations)
        }
    finally:
        conn.close()
