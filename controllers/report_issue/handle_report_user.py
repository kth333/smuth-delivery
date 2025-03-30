from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from models.database import session_local
from models.order_model import Order
from utils.utils import get_main_menu

async def handle_report_user(update: Update, context: CallbackContext):
    """
    Retrieves the last 3 orders where the user is orderer
    and the last 3 orders where the user is runner.
    """
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message
    
    session = session_local()
    orders_as_orderers = session.query(Order).filter(
        (Order.user_id == user_id) & (Order.runner_id.isnot(None))
    ).order_by(Order.order_placed_time.desc()).limit(3).all()
    
    orders_as_runners = session.query(Order).filter(
        (Order.runner_id == user_id) 
    ).order_by(Order.order_placed_time.desc()).limit(3).all()
    session.close()
    
    orders = []
    for order in orders_as_orderers:
        orders.append({
            "id": order.id ,
            "details": order.order_text,
            "handle": order.runner_handle
            })
    for order in orders_as_runners:
        orders.append({
            "id": order.id,
            "details": order.order_text,
            "handle": order.user_handle
        })
    
    if not orders:
        await message.reply_text(
            "❌ You do not have any recent orders to report.\n\n"
            "Returning to main menu.",
            reply_markup=get_main_menu()
        )
    
    else:
        details_message = "Here are your recent orders:\n\n"
        for order in orders:
            details_message += f"Order Id: {order['id']}\nDetails: {order['details']}\n\n"
        details_message += "Please select the user you would like to report: "
        
        keyboard = [[
            InlineKeyboardButton(f"Order Id: {order['id']} | Handle: {order['handle']}", callback_data=f"reporting_user_{order['id']}_{order['handle']}")
        ] for order in orders]
    
        reply_markup = InlineKeyboardMarkup(keyboard)
    
        await message.reply_text(
            details_message,
            reply_markup=reply_markup
        )
    
    