import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.constants import ParseMode # For HTML formatting in messages
from datetime import timedelta
import asyncio
import sqlite3 # For managing user warnings, message counts, and storing message IDs

# --- Configuration ---
# Replace with your actual bot token obtained from BotFather
BOT_TOKEN = "7982696434:AAFthyFTGGtjx-ALbPRzmN0JtD6GmUX3UZ8"

# List of unwanted keywords (case-insensitive). Add or remove as needed.
UNWANTED_KEYWORDS = ["spam", "அநாகரீகம்", "போலி", "மோசடி", "sex", "அட்ல்ட்", "adult content", "கெட்ட வார்த்தை"]

# Warning system settings
WARNING_LIMIT = 5 # 5 warnings before a user is banned.

# Message count for group rules alert
MESSAGES_FOR_ALERT = 30 # Show rules after every 30 messages

# Group Admin's Telegram Username or ID for contact (replace with actual admin's username or ID)
# If using username, do NOT include the '@' symbol. Example: "my_admin_username"
# If using user ID, make sure it's an integer. Example: 123456789
GROUP_ADMIN_USERNAME_OR_ID = "YourAdminUsernameOrIDHere" # <--- IMPORTANT: REPLACE THIS

# Configure logging to see what your bot is doing
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Database Setup (SQLite) ---
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

# Warning functions
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

# Message count functions for alerts
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

# New functions for storing and retrieving message IDs
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

# --- Group Rules Message (Formatted with HTML for visual appeal) ---
GROUP_RULES_MESSAGE = f"""
✨ <b><pre>⚠️GROUP RULE⚠️</pre></b> ✨

🚫 <b>Do not share any personal details</b> like your phone number, bank details etc. here.

🔞 <b>Posting 18+ is strictly prohibited here.</b>

🔗 Do not use <b>unnecessary words</b> or <b>unnecessary links.</b>

📚 Please use this platform created for educational purposes to <b>share doubts properly.</b>

🚨 <b>If you break the rules, you will be kicked out.</b>

📞 Contact Group Admin: <a href="tg://user?id={GROUP_ADMIN_USERNAME_OR_ID}">{GROUP_ADMIN_USERNAME_OR_ID}</a> (Click to message)

"""

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcoming message when the /start command is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"வணக்கம் {user.mention_html()}! நான் ஒரு குழு நிர்வாக பாட். நான் இணைப்புகள் மற்றும் குறிப்பிட்ட தேவையற்ற வார்த்தைகள் கொண்ட செய்திகளை நீக்குவேன். விதிமீறினால் எச்சரிக்கை வழங்கப்படும் மற்றும் மீண்டும் செய்தால் குழுவிலிருந்து நீக்கப்படுவீர்கள். நான் குழுவில் நிர்வாகியாகவும், 'செய்திகளை நீக்கும்' மற்றும் 'பயனர்களை நீக்கும்' அனுமதி பெற்றும் உள்ளேனா என்பதை உறுதிப்படுத்தவும்."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a helpful message when the /help command is issued."""
    await update.message.reply_text(
        "நான் இணைப்புகள் அல்லது குறிப்பிட்ட வார்த்தைகள் கொண்ட செய்திகளை நீக்குவேன். விதிமீறினால் எச்சரிக்கை வழங்கப்படும் மற்றும் மீண்டும் செய்தால் நீக்கப்படுவீர்கள். ஒவ்வொரு 30வது செய்தியிலும் குழு விதிகள் காண்பிக்கப்படும்.\n\n"
        "<b>நீக்கப்பட்ட பயனர் மீண்டும் இணைய விரும்பினால்:</b>\n"
        "குழு நிர்வாகியை அணுகி, உங்கள் User ID ஐ (உங்கள் டெலிகிராம் சுயவிவரத்தில் காணலாம்) தெரிவித்து, குழுவில் மீண்டும் இணையும்படி கேட்கவும். நிர்வாகி உங்களை தடைநீக்க முடியும்.",
        parse_mode=ParseMode.HTML
    )

# --- Message Deletion Function (for alerts) ---
async def delete_alert_message(context: ContextTypes.DEFAULT_TYPE):
    """Deletes an alert message posted by the bot after a delay."""
    job_data = context.job.data
    chat_id = job_data['chat_id']
    message_id = job_data['message_id']
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Deleted alert message {message_id} from chat {chat_id}.")
    except Exception as e:
        logger.error(f"Failed to delete alert message {message_id} from chat {chat_id}: {e}")

# --- Main Message Handler Function ---
async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles messages in groups, checks for unwanted content, takes action (delete, warn, ban),
    and manages the message counter for rules alerts. Stores message IDs for potential mass deletion."""
    
    # Only process messages from group or supergroup chats
    if update.effective_chat.type not in ['group', 'supergroup']:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    message_id = update.message.message_id
    message_text = update.message.text
    
    # Store the message ID for potential later deletion (regardless of content)
    store_message_id(message_id, chat_id, user_id)

    # --- Content Check Logic ---
    is_unwanted_content = False
    
    # Check for URLs/links in the message entities
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == 'url' or entity.type == 'text_link':
                is_unwanted_content = True
                break

    # If no link found, check for unwanted keywords in the message text
    if not is_unwanted_content and message_text:
        for keyword in UNWANTED_KEYWORDS:
            if keyword.lower() in message_text.lower():
                is_unwanted_content = True
                break
    
    # --- Action Based on Content Check (Warning/Ban) ---
    if is_unwanted_content:
        logger.info(f"Unwanted content detected from {user_name} (ID: {user_id}) in chat {chat_id}. Message: '{message_text}'")
        
        # Attempt to delete the immediate unwanted message
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            logger.info(f"Successfully deleted immediate unwanted message from {user_name}.")
            # Also remove it from our stored messages as it's already deleted
            delete_user_message_ids_from_db(user_id, chat_id) # Consider only deleting this specific message from DB. For simplicity, all of user's messages are removed from DB.
        except Exception as e:
            logger.error(f"Failed to delete immediate unwanted message from {user_name} in chat {chat_id}: {e}")

        # Check user's warning count from the database
        warning_count = get_warning_count(user_id)
        
        if warning_count < WARNING_LIMIT:
            # If user is under the warning limit, increment warning and send a warning message
            increment_warning_count(user_id)
            new_warning_count = get_warning_count(user_id) # Get updated count
            remaining_warnings = WARNING_LIMIT - new_warning_count
            
            warning_message = await context.bot.send_message(
                chat_id=chat_id,
                text=f"🚨 <b>எச்சரிக்கை!</b> {user_name}, உங்கள் செய்தி தேவையற்ற உள்ளடக்கத்தைக் கொண்டிருந்ததால் நீக்கப்பட்டது.\n"
                     f"இது உங்கள் <b>{new_warning_count}/{WARNING_LIMIT}</b> வது எச்சரிக்கை ஆகும். (மீதமுள்ள எச்சரிக்கைகள்: <b>{remaining_warnings}</b>)\n"
                     f"மீண்டும் விதிமீறினால் குழுவிலிருந்து நிரந்தரமாக நீக்கப்படுவீர்கள்.",
                parse_mode=ParseMode.HTML,
                reply_to_message_id=update.message.message_id # Reply to the position where the deleted message was
            )
            logger.info(f"Sent warning to {user_name}. Current warning count: {new_warning_count}. Remaining: {remaining_warnings}")
            # Schedule the warning message to be deleted after 30 seconds
            context.job_queue.run_once(
                delete_alert_message,
                timedelta(seconds=30),
                data={'chat_id': chat_id, 'message_id': warning_message.message_id}
            )

        else:
            # If user exceeds the warning limit, ban them from the group
            try:
                await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                reset_warning_count(user_id) # Reset warning count after banning
                
                # --- Attempt to delete all previous messages from this user ---
                user_all_messages = get_user_message_ids(user_id, chat_id)
                logger.info(f"Attempting to delete {len(user_all_messages)} previous messages from banned user {user_name}.")
                deleted_count = 0
                for msg_id in user_all_messages:
                    try:
                        await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                        deleted_count += 1
                        # Add a small delay to respect API rate limits if many messages
                        await asyncio.sleep(0.1) 
                    except Exception as e:
                        logger.warning(f"Failed to delete old message {msg_id} from {user_name}: {e}. (May be too old or already deleted)")
                
                delete_user_message_ids_from_db(user_id, chat_id) # Clean up DB after attempting deletion

                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🚫 <b>{user_name}</b> மீண்டும் விதிமீறியதால் குழுவிலிருந்து <b>நிரந்தரமாக நீக்கப்பட்டார்</b>. அவரது <b>{deleted_count}</b> பழைய செய்திகள் நீக்க முயற்சி செய்யப்பட்டன. குழு விதிகளை மதித்து நடப்போம்!\n\n"
                         f"<b>பயனர் மீண்டும் இணைய விரும்பினால்:</b>\n"
                         f"குழு நிர்வாகியை அணுகி, User ID: <code>{user_id}</code> ஐ தெரிவித்து, குழுவில் மீண்டும் இணையும்படி கேட்கவும். நிர்வாகி உங்களை தடைநீக்க முடியும்.",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"Banned {user_name} (ID: {user_id}) from chat {chat_id}.")
            except Exception as e:
                logger.error(f"Failed to ban {user_name} from chat {chat_id}: {e}")
                # Inform the group if banning failed (e.g., bot lacks ban permissions)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ {user_name} ஐ தடை செய்ய முடியவில்லை. எனக்கு போதுமான அனுமதி இல்லை அல்லது வேறு ஏதேனும் பிழை ஏற்பட்டது.",
                    parse_mode=ParseMode.HTML
                )
    else:
        logger.debug(f"No unwanted content detected from {user_name} in chat {chat_id}.")
    
    # --- Message Counter for Rules Alert ---
    # Increment message count for this chat (only if it's not the bot's own message)
    # The rules alert message itself should not count towards the 30 message threshold
    if update.effective_user.id != context.bot.id:
        increment_message_count(chat_id)
        current_count = get_message_count(chat_id)

        logger.info(f"Chat {chat_id} current message count: {current_count}")

        # If message count reaches the alert threshold, post rules and reset count
        if current_count >= MESSAGES_FOR_ALERT:
            logger.info(f"Message count reached {MESSAGES_FOR_ALERT} for chat {chat_id}. Posting rules.")
            try:
                rules_message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=GROUP_RULES_MESSAGE,
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"Posted group rules alert to chat {chat_id}.")
                
                # Schedule the deletion of this rules message after 30 seconds
                context.job_queue.run_once(
                    delete_alert_message,
                    timedelta(seconds=30),
                    data={'chat_id': chat_id, 'message_id': rules_message.message_id}
                )
                
                reset_message_count(chat_id) # Reset count after posting rules
                logger.info(f"Reset message count for chat {chat_id} after posting rules.")

            except Exception as e:
                logger.error(f"Failed to post group rules alert to chat {chat_id}: {e}")


# --- Main Function ---
def main() -> None:
    """Starts the bot and initializes the database."""
    # Initialize the SQLite database tables
    init_db()

    # Create the Application instance for the bot
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers for /start and /help
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Add a message handler to process all text messages (excluding commands)
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_group_messages))

    # Run the bot; it will continuously check for new updates
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
