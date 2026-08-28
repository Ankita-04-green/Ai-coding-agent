import sqlite3

DB_NAME = "conversations.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        project_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL)
    """)

    conn.commit()
    conn.close()

def save_message(project_id, role, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO messages (project_id, role, content) VALUES(?, ?, ?)""", (project_id, role, content))

    conn.commit()
    conn.close()

def get_messages(project_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content
        FROM messages
        WHERE project_id = ?
        ORDER BY id Asc
    """, (project_id,))

    rows = cursor.fetchall()
    conn.close()
    return rows