import logging
import argparse
import re
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
joined_channels = []
keyword_patterns = []


def start(update: Update, _: CallbackContext):
    """Start command handler."""
    update.message.reply_text("Bot started! Use /join to join channels.")


def join_channels(update: Update, _: CallbackContext):
    """Join channels provided in the channel list file."""
    global joined_channels
    # Load the channel list from the file specified by --channel-list argument
    # Replace 'your_channel_list_file.txt' with the actual filename
    with open('your_channel_list_file.txt', 'r') as f:
        channels = f.read().splitlines()

    for channel in channels:
        try:
            # Join the channel
            update.message.bot.get_chat(channel)
            joined_channels.append(channel)
            update.message.reply_text(f"Joined channel: {channel}")
        except Exception as e:
            update.message.reply_text(f"Error joining channel {channel}: {e}")


def stop(update: Update, _: CallbackContext):
    """Stop the bot and exit channels provided in the channel list file."""
    global joined_channels
    for channel in joined_channels:
        # Exit the channel
        update.message.bot.leave_chat(channel)
        update.message.reply_text(f"Exited channel: {channel}")
    joined_channels = []


def status(update: Update, _: CallbackContext):
    """Show bot status (online or offline) and joined channels."""
    global joined_channels
    if joined_channels:
        update.message.reply_text(f"Bot is online. Joined channels: {', '.join(joined_channels)}")
    else:
        update.message.reply_text("Bot is offline.")


def set_nick(update: Update, args: list, _: CallbackContext):
    """Set bot's nick name using the /nick command."""
    if not args:
        update.message.reply_text("Please provide a nick name.")
    else:
        new_nick = ' '.join(args)
        update.message.bot.set_my_commands(commands=[('start', 'Start the bot'),
                                                      ('join', 'Join channels from the list'),
                                                      ('stop', 'Exit channels from the list and stop the bot'),
                                                      ('status', 'Show bot status and joined channels'),
                                                      ('nick', 'Set bot\'s nick name')])
        update.message.reply_text(f"Bot's nick name has been set to: {new_nick}")


def log_message(update: Update, _: CallbackContext):
    """Log messages containing keyword patterns to the SQLite database."""
    global keyword_patterns
    for pattern in keyword_patterns:
        if re.search(pattern, update.message.text, re.IGNORECASE):
            channel_id = update.message.chat.id
            timestamp = datetime.now().isoformat()
            username = update.message.from_user.username
            message_content = update.message.text
            attachment = update.message.document.file_id if update.message.document else None

            # Log the message to the database
            with sqlite3.connect('message_log.db') as conn:
                cursor = conn.cursor()
                # Replace 'channel_name' with the actual channel name or ID
                table_name = f"channel_{channel_id}"
                cursor.execute(f"INSERT INTO {table_name} (timestamp, username, message_content, attachment) "
                               "VALUES (?, ?, ?, ?)", (timestamp, username, message_content, attachment))
                conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Telegram bot with channel management.")
    parser.add_argument("--channel-list", help="Import channel list from file")
    parser.add_argument("--keywords", help="Import keywords or regex patterns from file")
    parser.add_argument("--start", action="store_true", help="Start the bot and join channels")
    parser.add_argument("--stop", action="store_true", help="Stop the bot and exit channels")
    parser.add_argument("--status", action="store_true", help="Show bot status and joined channels")
    parser.add_argument("--nick", help="Set bot's nick name")

    args = parser.parse_args()

    # Load keyword patterns from the file specified by --keywords argument
    # Replace 'your_keywords_file.txt' with the actual filename
    with open('your_keywords_file.txt', 'r') as f:
        keyword_patterns = f.read().splitlines()

    # Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual bot token
    updater = Updater("YOUR_TELEGRAM_BOT_TOKEN")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("join", join_channels))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("nick", set_nick, pass_args=True))

    # Register message handler for monitoring and logging messages
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, log_message))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
