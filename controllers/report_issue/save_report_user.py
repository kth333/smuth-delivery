from telegram import Update
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown
from models.database import session_local
from models.order_model import ReportUser, Order
from controllers.order_state import user_states
from utils.utils import get_main_menu

async def save_report_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message
    
    session = session_local()
    
    order_id = user_states[user_id]['order_id']
    order = session.query(Order).filter(Order.id == order_id).first()
    reported_user_id = order.runner_id if order.user_id == user_id else order.orderer_id
    reported_user_handle = order.runner_handle if order.user_id == user_id else order.user_handle
    
    new_report = ReportUser(
            reporter_id=user_id,
            order_id=order_id,
            reported_user_id=reported_user_id,
            reason=message.text,
        )
    
    session.add(new_report)
    session.commit()
    session.close()
    
    del user_states[user_id]
    
    # Prepare the summary of the report
    report_summary = (
        "✅ Your report has been submitted successfully. Thank you for your feedback!\n\n"
        "*Report Summary:*\n"
        f"- *Order ID:* {order_id}\n"
        f"- *Reported User:* {reported_user_handle}\n"
        f"- *Reason:* {message.text if message.text else 'No text provided'}"
    )
    
    await message.reply_text(
        report_summary,
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )