import os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv
from handlers import handle_message, start, handle_order, view_orders, handle_claim, help_command, handle_button, handle_my_orders
from database import *

# Load environment variables
load_dotenv()

# Load the bot token
TOKEN = os.getenv('TELEGRAM_TOKEN')

def main():
    app = Application.builder().token(TOKEN).build()

    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("order", handle_order))
    app.add_handler(CommandHandler("vieworders", view_orders))
    app.add_handler(CommandHandler("claim", handle_claim))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("myorders", handle_my_orders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Callback Query Handler (buttons)
    app.add_handler(CallbackQueryHandler(handle_button))

    # Start polling
    app.run_polling()

if __name__ == '__main__':
    main()