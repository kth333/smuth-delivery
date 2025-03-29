# General Welcome
WELCOME_TEXT = (
    "👋 *Welcome to SmuthDelivery!* 🚀\n\n"
    "🎓 Before you start, please use the help command to learn how it works!\n\n"

    "💡 *Quick Commands:*\n"
    "📌 /order - Place an order\n"
    "📌 /vieworders - See available food orders\n"
    "📌 /claim or /claim <order id> - Claim an order as a runner\n"
    "📌 /help - Get assistance\n\n"

    "*Please ensure your Telegram chat is open to new contacts so that orderers/runners can communicate with you!*"
)

HELP_TEXT = (
        "💡 *SmuthDelivery Bot Guide* 🚀\n\n"
        "📌 *How It Works:*\n"
        "1️⃣ *Place an Order:* To place an order, use the bot to enter the details of your meal, delivery location, time, and the delivery fee you wish to pay\.\n"
        "2️⃣ *Claim an Order:* Use view orders to claim an order and deliver it to get a delivery fee\.\n"
        "3️⃣ *Delivering Food:* After claiming an order, get the food and deliver it to the user’s specified location\.\n"
        "4️⃣ *Communicate via Telegram Chat:* Once you've claimed an order, communicate with the orderer via Telegram chat to finalize details\.\n\n"
        "The bot privately sends the Telegram handles of the orderer/runner to each party once an order is claimed\. Please ensure your Telegram chat is open to new contacts so that orderers/runners can communicate with you\.\n\n"

        "🔹 This bot is still in very early development\. Features are not perfect\.\n"
        f"🔹 If you have any issues or suggestions, leave your comments here \(along with your Telegram handle if you want us to get back to you\)\:\n"
        "https://forms\.gle/f6FAuLeXSbw1vSSM7\n\n"
        
        "📢 *Stay Updated:* Subscribe to our channel for real\-time updates on new orders: [Smuth Delivery](https://t\.me/smuth\_delivery)"
)

# Order placement instructions
ORDER_INSTRUCTIONS_MEAL = (
    "📝 *Placing an Order*. We will ask for delivery location, time, additional info and delivery fee next.\n\n"
    "📌 Enter: The *food* you want\n"
    "✅ Example: *Menu number 1 at King Kong Curry*"
)

ORDER_INSTRUCTIONS_LOCATION = (
    "📝 *Placing an Order*\n\n"
    "📌 Enter: The *location* you want your food to be delivered to:\n"
    "✅ Example: *SCIS 1 SR 3-1*"
)

ORDER_INSTRUCTIONS_EARLIEST_TIME = (
    "📝 *Placing an Order*\n\n"
    "📌 Enter: The *earliest time* you’re available to receive the order (must be within the next 7 days):\n\n"
    "IMPORTANT: Follow the format below!\n"
    "*MM-DD HH:MMpm/am*\n\n"
    "✅ Example, *03-27 04:10pm* or *11-08 08:15am*"
)

ORDER_INSTRUCTIONS_LATEST_TIME = (
    "📝 *Placing an Order*\n\n"
    "📌 Enter: The *latest time* you’re available to receive the order (must be within the next 3 hours of earliest):\n\n"
    "IMPORTANT: Follow the format below!\n"
    "*MM-DD HH:MMpm/am*\n\n"
    "✅ Example, *03-27 05:00pm* or *11-08 09:15am*"
)

ORDER_INSTRUCTIONS_DETAILS = (
    "📝 *Placing an Order*\n\n"
    "📌 Enter: any *additional info* (enter \"none\" if not applicable):\n"
    "✅ Example: *Extra cutlery please*"
)

ORDER_INSTRUCTIONS_FEE = (
    "📝 *Placing an Order*\n\n"
    "📌 Enter: The *delivery fee* you're offering to the runners (only input a number):\n"
    "✅ Example: *1.50*"
)

# Claim success notification
CLAIM_SUCCESS_MESSAGE = (
    "✅ *Order {order_id} Successfully Claimed\!*\n\n"
    "👤 *Orderer's Telegram Handle:* @{orderer_handle}\n\n"
    "📌 *Order Info:*\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}\n\n"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* ${delivery_fee}\n\n" 
    "🚀 *Next Steps:*\n"
    "1️⃣ Buy the meal from the vendor\.\n"
    "2️⃣ Confirm purchase via the bot\.\n"
    "3️⃣ Deliver to the delivery location\.\n"
    "4️⃣ Receive your payment\!\n\n"
    "💡 Stay updated with your claimed orders for smooth transactions\!"
)

# Order claimed notification for the orderer
ORDER_CLAIMED_NOTIFICATION = (
    "📢 *Your Order Has Been Claimed\!*\n\n"
    "📌 *Order ID:* {order_id}\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}\n"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* ${delivery_fee}\n\n" 
    "🚴 Claimed by: {claimed_by}\n\n"
    "📍 *Stay tuned for updates on delivery\!*"
)

# Order ID request prompt
ORDER_ID_REQUEST = "🔍 Please enter the *Order ID* you want to claim:"

# Invalid order ID message
INVALID_ORDER_ID = "❌ Invalid Order ID. Please enter a valid number."

# Order length error
ORDER_TOO_LONG = (
    "⚠️ Your message is too long! Please limit it to {max_length} characters.\n\n"
    "📝 *Your message length:* {order_length} characters."
)

ORDER_DETAILS_TOO_LONG = (
    "⚠️ Your message is too long! Please limit it to {max_length} characters.\n\n"
    "📝 *Your message length:* {order_length} characters."
)

ORDER_SUMMARY = """*Order Summary*:
🍽 *Meal:* {order_text}
📍 *Location:* {order_location}
⏳ *Time:* {order_time}
ℹ️ *Details:* {order_details}
💸 *Delivery Fee:* ${delivery_fee}

Would you like to confirm this order?
"""

# Order placement confirmation
ORDER_PLACED = (
    "✅ *Order Placed Successfully\!*\n\n"
    "📌 *Order ID:* {order_id}\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}\n"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* ${delivery_fee}\n\n" 
    "⚡ Your order has been listed\! A food runner will claim it soon\."
)

# New order notification in channel
NEW_ORDER = (
    "📢 New Order Available\n\n📌 Order ID: {order_id}\n\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}\n"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* ${delivery_fee}\n\n"
    "{claim_status}"
)

NEW_CLAIM = (
    "✅ Order {order_id} has been claimed\!\n\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}\n"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* ${delivery_fee}\n\n" 
)

EDITED_ORDER = (
    "📢 Order ID: {order_id} has been edited\.\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* ${delivery_fee}\n\n" 
)

# No available orders message
NO_ORDERS_AVAILABLE = (
    "⏳ *No orders available right now!*\n\n"
    "💡 Check back later or place an order using /order."
)

# Claim failed or already claimed order message
CLAIM_FAILED = "⚠️ Order {order_id} has already been claimed or does not exist."

# Claim invalid order ID message
CLAIM_INVALID = "❌ *Invalid order claim request.* Please check the order ID and try again."

# General error message
GENERAL_ERROR = "⚠️ Something went wrong. Please try again later."

CLAIM_CONFIRMATION = (
    "✅ You are about to claim *Order ID: {order_id}*\.\n\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}\n"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* ${delivery_fee}\n\n" 
    "Please confirm by sending the *Order ID* again\.\n\n"
    "To cancel, press the *Back* button below\."
)