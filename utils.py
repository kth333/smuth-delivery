from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    """Generates the main menu keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Place Order", callback_data='order')],
        [InlineKeyboardButton("View Orders", callback_data='vieworders')],
        [InlineKeyboardButton("Claim Order", callback_data='claim')],
        [InlineKeyboardButton("View and Cancel Orders", callback_data='myorders')],
        [InlineKeyboardButton("View and Cancel Claims", callback_data='myclaims')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ])
    
def get_my_orders_menu():
    """Generates the My Orders menu keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Complete Order", callback_data='complete_order')],
        [InlineKeyboardButton("Make Payment", callback_data='handle_payment')],
        [InlineKeyboardButton("Edit Order", callback_data='edit_order')],
        [InlineKeyboardButton("Report Runner", callback_data='report_user')],
        [InlineKeyboardButton("Delete Order", callback_data='delete_order')],
        [InlineKeyboardButton("Back", callback_data='start')]
    ])