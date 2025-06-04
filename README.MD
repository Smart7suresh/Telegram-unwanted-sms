Here's the complete README.md file for your Telegram bot, incorporating all the details from the provided my_telegram_bot.txt and assuming the Data_manager.py separation as discussed.
# Telegram Group Admin Bot

This is a Python-based Telegram bot designed to help moderate group chats by filtering unwanted content, managing user warnings, and periodically reminding members about group rules.

## Features

* **Unwanted Content Filtering**: Automatically deletes messages containing specified unwanted keywords (e.g., "spam", "அநாகரீகம்", "போலி", "மோசடி", "sex", "அட்ல்ட்", "adult content", "கெட்ட வார்த்தை") or links/URLs.
* **Warning System**:
    * Users who post unwanted content receive a warning.
    * A warning count is maintained for each user in an SQLite database.
    * If a user reaches a pre-defined warning limit (default: 5 warnings), they are automatically banned from the group.
    * Upon banning, all their previously sent messages in that chat are attempted to be deleted.
    * The warning count is reset after a user is banned.
* **Group Rules Alert**:
    * The bot posts a formatted group rules message periodically after a certain number of messages (default: every 30 messages).
    * These alert messages are automatically deleted after a short delay (e.g., 30 seconds) to keep the chat clean.
* **User Message Tracking**: Stores message IDs of all user messages (including chat ID and user ID) to facilitate mass deletion if a user is banned. These stored IDs are deleted from the database after a ban.
* **Admin Contact Information**: The rules message includes a clickable link to contact the group admin.
* **Help Command (`/help`)**: Provides information on bot functionality, including the fact that it deletes messages with links or specific words, issues warnings, bans users for repeated violations, and shows group rules every 30 messages. It also explains how a banned user can rejoin by contacting the admin with their User ID.
* **Start Command (`/start`)**: Greets the user in Tamil, mentions its functions of deleting unwanted content and links, warns about warnings and bans, and reminds to check if the bot has admin permissions for deleting messages and banning users.

## Setup and Installation

### Prerequisites

* Python 3.8+
* A Telegram Bot Token (obtained from BotFather)
* Basic understanding of command line and Python.

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd <your-repository-name>

2. Install Dependencies
Install the required Python libraries using pip. Create a requirements.txt file with the following content:
python-telegram-bot

Then run:
pip install -r requirements.txt

3. Database Initialization
The bot uses an SQLite database (bot_data.db) to store warning counts, message counts, and message IDs. The database tables will be automatically initialized when the bot starts for the first time by calling init_db().
4. Configuration
Open the my_telegram_bot.py file and configure the following:
 * BOT_TOKEN: Replace "7982696434:AAFthyFTGGtjx-ALbPRzmN0JD6GmUX3UZ8" with your actual bot token obtained from BotFather.
   * Security Note: For production environments, it is highly recommended to use environment variables instead of hardcoding your bot token directly in the code.
 * UNWANTED_KEYWORDS: Customize the list of unwanted keywords (case-insensitive).
 * WARNING_LIMIT: Set the number of warnings (default: 5) before a user is banned.
 * MESSAGES_FOR_ALERT: Define how many messages (default: 30) should pass before the group rules alert is posted.
 * GROUP_ADMIN_USERNAME_OR_ID: Replace "YourAdminUsernameOrIDHere" with the Telegram username or user ID of your group admin. If using a username, do not include the '@' symbol. If using a user ID, make sure it's an integer.
# --- Configuration ---
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE" # Replace with your actual bot token
UNWANTED_KEYWORDS = ["spam", "அநாகரீகம்", "போலி", "மோசடி", "sex", "அட்ல்ட்", "adult content", "கெட்ட வார்த்தை"]
WARNING_LIMIT = 5 # 5 warnings before a user is banned
MESSAGES_FOR_ALERT = 30 # Show rules after every 30 messages
GROUP_ADMIN_USERNAME_OR_ID = "YourAdminUsernameOrIDHere" # <--- IMPORTANT: REPLACE THIS

5. Run the Bot
To start your bot, simply run the my_telegram_bot.py file:
python my_telegram_bot.py

The bot will start polling for updates.
Deployment (e.g., on GitHub Cloud Services like Heroku/Render)
To deploy your bot on a cloud service, you will typically:
 * Push to GitHub: Ensure your my_telegram_bot.py, Data_manager.py (if you separated it), requirements.txt, and this README.md are pushed to a GitHub repository.
 * Choose a Platform: Select a platform like Heroku, Render, Railway, etc.
 * Connect to GitHub: Link your chosen platform to your GitHub repository.
 * Set Environment Variables: Crucially, set BOT_TOKEN and GROUP_ADMIN_USERNAME_OR_ID as environment variables within your deployment platform's settings. This is more secure than hardcoding them.
 * Configure Buildpack/Runtime: Ensure the platform uses a Python buildpack and executes my_telegram_bot.py as the main process.
Bot Permissions
For the bot to function correctly, ensure it has the following permissions in your Telegram group:
 * Delete Messages: To remove unwanted content and old messages of banned users.
 * Ban Users: To remove users who exceed the warning limit.
 * Is an administrator: The bot needs to be an administrator in the group.
Project Structure (Assumed)
.
├── my_telegram_bot.py    # Main bot logic and handlers
├── Data_manager.py       # Handles all SQLite database operations (if separated)
├── requirements.txt      # List of Python dependencies
├── README.md             # This file
└── bot_data.db           # SQLite database file (generated on first run)


