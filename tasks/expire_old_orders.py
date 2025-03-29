import os
import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown

from models.database import session_local, SGT
from models.order_model import Order
import views.messages as messages

async def expire_old_orders(bot):
    now = datetime.now(SGT)
    with session_local() as session:
        expired_orders = session.query(Order).filter(
            Order.expired == False,
            Order.claimed == False,
            Order.latest_pickup_time < now
        ).all()

        # Retrieve the bot's username for URL generation.
        bot_username = (await bot.get_me()).username

        for order in expired_orders:
            order.expired = True
            logging.info(f"[EXPIRED] Order ID {order.id} marked as expired")

            # Notify the orderer privately.
            try:
                await bot.send_message(
                    chat_id=order.user_id,
                    text=f"Sorry, we couldn't find you a runner for Order ID {order.id}.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logging.warning(f"Failed to notify user {order.user_id}: {e}")

            # Create an inline keyboard with options.
            keyboard = [
                [InlineKeyboardButton("Claim This Order", url=f"https://t.me/{bot_username}?start=claim_{order.id}")],
                [InlineKeyboardButton("Place an Order", url=f"https://t.me/{bot_username}?start=order")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if order.channel_message_id:
                try:
                    edited_text = messages.NEW_ORDER.format(
                        order_id=escape_markdown(str(order.id), version=2),
                        order_text=escape_markdown(order.order_text, version=2),
                        order_location=escape_markdown(order.location, version=2),
                        order_time=escape_markdown(
                            f"{order.earliest_pickup_time.astimezone(SGT).strftime('%A %m-%d %I:%M%p')} - "
                            f"{order.latest_pickup_time.astimezone(SGT).strftime('%A %m-%d %I:%M%p')}",
                            version=2
                        ),
                        order_details=escape_markdown(order.details, version=2),
                        delivery_fee=escape_markdown(order.delivery_fee, version=2),
                        claim_status=escape_markdown(
                            "Claim Status: This order has expired and is no longer available.",
                            version=2
                        )
                    )
                    await bot.edit_message_text(
                        chat_id=os.getenv("CHANNEL_ID"),
                        message_id=order.channel_message_id,
                        text=edited_text,
                        parse_mode="MarkdownV2",
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    logging.warning(f"Failed to edit expired message: {e}")
        session.commit()