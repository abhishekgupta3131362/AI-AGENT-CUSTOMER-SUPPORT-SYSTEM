import sqlite3
import json
from pathlib import Path
from backend.config import Config

DB_FILE = Config.DATABASE_PATH

def get_db_connection():
    """Returns a SQLite connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
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
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)
    
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
