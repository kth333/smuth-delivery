from telegram import Update
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown
from models.database import session_local
from models.order_model import Order
from controllers.order_state import user_states
from utils.utils import get_main_menu

async def handle_selecting_claimed_order(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    message = update.message

    try:
        order_id = int(message.text.strip())
        session = session_local()
        order = session.query(Order).filter_by(id=order_id, runner_id=user_id, claimed=True).first()

        if not order:
            await message.reply_text(
                "❌ Invalid or unclaimed Order ID. Please try again.",
                parse_mode="Markdown"
            )
            session.close()
            return

        user_states[user_id] = {'state': 'canceling_claim', 'selected_order': order_id}

        await message.reply_text(
            f"🛑 Are you sure you want to cancel your claim on *Order ID {order_id}*?\n"
            "Reply with *YES* to confirm or *NO* to abort.",
            parse_mode="Markdown"
        )
        session.close()
    except ValueError:
        await message.reply_text(
            "❌ Please enter a valid Order ID.",
            parse_mode="Markdown"
        )