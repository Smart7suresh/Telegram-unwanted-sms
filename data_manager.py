import sqlite3
import logging

# Configure logging for Data_manager.py
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database file name to store bot data
DB_NAME = 'bot_data.db'

def init_db():
    """Initializes the SQLite database tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Table for user warnings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warnings (
            user_id INTEGER PRIMARY KEY,
            warning_count INTEGER DEFAULT 0
        )
    ''')
    
    # Table for chat message counts (for rules alert)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_message_counts (
            chat_id INTEGER PRIMARY KEY,
            message_count INTEGER DEFAULT 0
        )
    ''')

    # New table to store message IDs for deletion on ban
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_messages (
            message_id INTEGER PRIMARY KEY,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

def get_warning_count(user_id: int) -> int:
    """Retrieves the current warning count for a specific user from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT warning_count FROM warnings WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def increment_warning_count(user_id: int):
    """Increments the warning count for a user in the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO warnings (user_id, warning_count) VALUES (?, COALESCE((SELECT warning_count FROM warnings WHERE user_id = ?), 0) + 1)", (user_id, user_id))
    conn.commit()
    conn.close()
    logger.info(f"Incremented warning count for user {user_id}")

def reset_warning_count(user_id: int):
    """Resets the warning count for a user in the database (e.g., after a ban)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM warnings WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    logger.info(f"Reset warning count for user {user_id}")

def get_message_count(chat_id: int) -> int:
    """Gets the current message count for a given chat."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT message_count FROM chat_message_counts WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def increment_message_count(chat_id: int):
    """Increments the message count for a given chat."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO chat_message_counts (chat_id, message_count) VALUES (?, COALESCE((SELECT message_count FROM chat_message_counts WHERE chat_id = ?), 0) + 1)", (chat_id, chat_id))
    conn.commit()
    conn.close()
    logger.info(f"Incremented message count for chat {chat_id}")

def reset_message_count(chat_id: int):
    """Resets the message count for a given chat."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE chat_message_counts SET message_count = 0 WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
    logger.info(f"Reset message count for chat {chat_id}")

def store_message_id(message_id: int, chat_id: int, user_id: int):
    """Stores a message ID with its associated chat and user ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_messages (message_id, chat_id, user_id) VALUES (?, ?, ?)", (message_id, chat_id, user_id))
    conn.commit()
    conn.close()
    logger.debug(f"Stored message {message_id} from user {user_id} in chat {chat_id}")

def get_user_message_ids(user_id: int, chat_id: int):
    """Retrieves all message IDs sent by a specific user in a specific chat."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT message_id FROM user_messages WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
    messages = cursor.fetchall()
    conn.close()
    return [msg[0] for msg in messages]

def delete_user_message_ids_from_db(user_id: int, chat_id: int):
    """Removes all stored message IDs for a user from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_messages WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
    conn.commit()
    conn.close()
    logger.info(f"Deleted all stored message IDs for user {user_id} in chat {chat_id} from DB.")

if __name__ == '__main__':
    # This block will only run if Data_manager.py is executed directly
    # You can use it for testing database initialization
    init_db()
    print(f"Database '{DB_NAME}' initialized with tables: warnings, chat_message_counts, user_messages.")
    # Example usage:
    # increment_warning_count(12345)
    # print(f"Warning count for 12345: {get_warning_count(12345)}")
    # store_message_id(1001, -12345, 12345)
    # print(f"Messages for 12345 in -12345: {get_user_message_ids(12345, -12345)}")
