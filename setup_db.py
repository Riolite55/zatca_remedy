import os
import sqlite3
import uuid
from datetime import datetime

import pandas as pd

_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(_DIR, "data", "Remedy_Results.xls")
DB_PATH = os.path.join(_DIR, "remedy_mock.db")


def create_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # --- App tables (IF NOT EXISTS so we never wipe user data) ---
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT DEFAULT 'admin',
            department TEXT,
            created_at DATETIME
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            content TEXT,
            charts_json TEXT,
            created_at DATETIME,
            FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS dashboards (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT,
            created_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS dashboard_widgets (
            id TEXT PRIMARY KEY,
            dashboard_id TEXT,
            title TEXT,
            type TEXT,
            sql_query TEXT,
            x_col TEXT,
            y_col TEXT,
            FOREIGN KEY(dashboard_id) REFERENCES dashboards(id)
        )
    ''')

    # --- Migrate: add role/department columns if missing ---
    existing_cols = [row[1] for row in c.execute("PRAGMA table_info(users)").fetchall()]
    if "role" not in existing_cols:
        c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'admin'")
    if "department" not in existing_cols:
        c.execute("ALTER TABLE users ADD COLUMN department TEXT")

    # --- Seed users if not exist ---
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # Admin user (global access, no department)
        c.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if c.fetchone()[0] == 0:
            admin_id = str(uuid.uuid4())
            hashed_pw = pwd_context.hash("admin")
            c.execute("INSERT INTO users (id, username, password_hash, role, department, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                      (admin_id, "admin", hashed_pw, "admin", None, datetime.now().isoformat()))
            print("Seeded 'admin' user (password: admin)")

        # Zakah Registration Manager (scoped to Zakah_Registration department)
        c.execute("SELECT COUNT(*) FROM users WHERE username = 'zakah_registration_manager'")
        if c.fetchone()[0] == 0:
            zakah_id = str(uuid.uuid4())
            hashed_pw = pwd_context.hash("zakah_registration_manager")
            c.execute("INSERT INTO users (id, username, password_hash, role, department, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                      (zakah_id, "zakah_registration_manager", hashed_pw, "manager", "Zakah_Registration", datetime.now().isoformat()))
            print("Seeded 'zakah_registration_manager' user (password: zakah_registration_manager)")
    except Exception as e:
        print(f"Could not seed users: {e}")

    # --- Import Remedy data from Excel ---
    if not os.path.exists(EXCEL_PATH):
        print(f"WARNING: data/Remedy_Results.xls not found. Place it in the data/ folder and re-run.")
        c.execute('''CREATE TABLE IF NOT EXISTS hpd_help_desk (INCIDENT_NUMBER TEXT)''')
    else:
        df = pd.read_excel(EXCEL_PATH)
        df.to_sql('hpd_help_desk', conn, if_exists='replace', index=False)
        print(f"Loaded {len(df)} incidents into database.")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_db()
