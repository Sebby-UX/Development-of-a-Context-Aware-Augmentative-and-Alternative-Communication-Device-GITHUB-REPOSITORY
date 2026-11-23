import sqlite3


DB_FILE = "chat.db"

conn = sqlite3.connect(DB_FILE)

def init_database():
    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        """)

    conn.commit()
    conn.close()


def save_message(message):
    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO messages (message)
        VALUES (?)
    """, (message,))

    conn.commit()
    conn.close()


def get_all_messages():
    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT message
        FROM messages
        ORDER BY id ASC
    """)

    messages = [
        row[0]
        for row in cursor.fetchall()
    ]

    conn.close()

    return messages

def get_userinfo(profile):
    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """,(profile,))

    profileInfo = cursor.fetchone()

    conn.close()

    return profileInfo

def get_usernames():
    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT username
        FROM users
    """)

    usernames = [row[0] for row in cursor.fetchall()]


    conn.close()

    return usernames

def changepass(password, profile):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET password = ?
        WHERE id = ?
    """, (password, profile))

    conn.commit()
    conn.close()
    
def changename(name, profile):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET username = ?
        WHERE id = ?
    """, (name, profile))

    conn.commit()
    conn.close()