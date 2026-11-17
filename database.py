import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent / "clinic_bot.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Conversation history table (to provide multi-turn context to Gemini)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Appointments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            patient_phone TEXT NOT NULL,
            reason TEXT,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT DEFAULT 'CONFIRMED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def save_message(sender_id: str, role: str, message: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (sender_id, role, message) VALUES (?, ?, ?)",
        (sender_id, role, message)
    )
    conn.commit()
    conn.close()

def get_conversation_history(sender_id: str, limit: int = 8) -> List[Dict[str, str]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT role, message FROM conversations
        WHERE sender_id = ?
        ORDER BY id DESC LIMIT ?
        """,
        (sender_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    
    # Return chronologically
    return [{"role": row["role"], "content": row["message"]} for row in reversed(rows)]

def create_appointment(
    patient_name: str,
    patient_phone: str,
    reason: str,
    appointment_date: str,
    appointment_time: str
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO appointments (patient_name, patient_phone, reason, appointment_date, appointment_time, status)
        VALUES (?, ?, ?, ?, ?, 'CONFIRMED')
        """,
        (patient_name, patient_phone, reason, appointment_date, appointment_time)
    )
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return appointment_id

def get_recent_appointments(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM appointments
        ORDER BY id DESC LIMIT ?
        """,
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Initialize tables immediately
init_db()
