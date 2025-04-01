from telegram import Update
from telegram.ext import CallbackContext
from utils.utils import get_main_menu
from views import messages
from controllers.order_state import user_states
from controllers.claim_steps.perform_claim import perform_claim
from models.database import session_local
from models.order_model import Order

async def handle_claim_confirmation(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    try:
        order_id = int(text)
    except ValueError:
        user_states.pop(user_id, None)
        await update.message.reply_text(
            messages.INVALID_ORDER_ID,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        return

    state_data = user_states.get(user_id, {})
    stored_order_id = state_data.get("order_id")

    if order_id != stored_order_id:
        user_states.pop(user_id, None)
        await update.message.reply_text(
            messages.INVALID_ORDER_ID,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        return

    # Open session and validate
    with session_local() as session:
        order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()

        if not order:
            user_states.pop(user_id, None)
            await update.message.reply_text(
                messages.CLAIM_FAILED.format(order_id=order_id),
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            return

        # if order.user_id == user_id:
        #     await update.message.reply_text(
        #         "⚠️ You can't claim your own order.",
        #         parse_mode="Markdown",
        #         reply_markup=get_main_menu()
        #     )
        #     return

        # active_claims = session.query(Order).filter_by(runner_id=user_id, claimed=True, expired=False).count()
        # if active_claims >= 2:
        #     await update.message.reply_text(
        #         "🚫 You have already claimed 2 active orders.\n\n"
        #         "Please cancel one of your existing claims before claiming a new one.",
        #         parse_mode="Markdown",
        #         reply_markup=get_main_menu()
        #     )
        #     return

        # Delegate the actual claiming
        await perform_claim(session, order, order_id, update, context)
