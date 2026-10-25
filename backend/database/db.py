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
            content TEXT NOT NULL,
            tool_calls TEXT,
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
