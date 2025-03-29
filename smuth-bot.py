import os
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from controllers.start import start
from controllers.order_conversation import start_order, handle_conversation
from controllers.order_claim import handle_claim
from controllers.help_command import help_command
from controllers.order_management import view_orders, handle_my_orders, handle_my_claims
from controllers.order_buttons import handle_button
from tasks.expire_orders import expire_old_orders
from models.database import create_tables

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Register command handlers.
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("order", start_order))
    app.add_handler(CommandHandler("vieworders", view_orders))
    app.add_handler(CommandHandler("claim", handle_claim))
    app.add_handler(CommandHandler("myorders", handle_my_orders))
    app.add_handler(CommandHandler("help", help_command))
    
    # Register a message handler for the order conversation.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_conversation))
    
    # Register the callback query handler for inline buttons.
    app.add_handler(CallbackQueryHandler(handle_button))
    
    # Set up the scheduler to run the expire_old_orders task every 5 minutes.
    scheduler = AsyncIOScheduler()
    scheduler.add_job(expire_old_orders, 'interval', minutes=5, args=[bot])
    scheduler.start()
    
    # Start polling.
    app.run_polling()

if __name__ == '__main__':
    create_tables()
    main()
