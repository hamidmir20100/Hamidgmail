import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Gmail Accounts from a file
def load_accounts(file_path):
    accounts = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    email, password, price = parts
                    accounts.append({"email": email, "password": password, "price": int(price)})
    except FileNotFoundError:
        logger.warning("Account file not found. Please ensure the file exists.")
    return accounts

# File path for Gmail accounts
ACCOUNTS_FILE = "accounts.txt"
ACCOUNTS = load_accounts(ACCOUNTS_FILE)

# Admin ID
ADMIN_ID = 7888864258

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("خرید اکانت جیمیل", callback_data='buy')],
        [InlineKeyboardButton("پشتیبانی", callback_data='support')],
        [InlineKeyboardButton("راهنما", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("به ربات فروش اکانت جیمیل خوش آمدید!", reply_markup=reply_markup)

# Handle button clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'buy':
        keyboard = [
            [InlineKeyboardButton("1 عدد", callback_data='buy_1')],
            [InlineKeyboardButton("2 عدد", callback_data='buy_2')],
            [InlineKeyboardButton("3 عدد", callback_data='buy_3')],
            [InlineKeyboardButton("5 عدد", callback_data='buy_5')],
            [InlineKeyboardButton("10 عدد", callback_data='buy_10')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("تعداد اکانت مورد نظر برای خرید را انتخاب کنید:", reply_markup=reply_markup)

    elif query.data == 'support':
        await query.edit_message_text(" @hamidmir2027  :  برای پشتیبانی، لطفاً با مدیر تماس بگیرید یا پیام خود را ارسال کنید.")

    elif query.data.startswith('buy_'):
        quantity = int(query.data.split('_')[1])

        if len(ACCOUNTS) < quantity:
            await query.edit_message_text(f"تعداد اکانت‌های در دسترس کافی نیست. موجودی فعلی: {len(ACCOUNTS)}")
        else:
            total_price = sum([acc['price'] for acc in ACCOUNTS[:quantity]])
            context.user_data['pending_accounts'] = ACCOUNTS[:quantity]
            context.user_data['user_id'] = query.from_user.id

            await query.edit_message_text(
                f"لطفاً مبلغ {total_price} تومان را به شماره کارت 5041.7210.8297.8686 واریز کنید.\n"
                "پس از واریز، پیام تایید را ارسال کنید."
            )

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"درخواست خرید {quantity} اکانت به مبلغ {total_price} تومان توسط {query.from_user.username}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("تایید سفارش", callback_data=f'confirm_{quantity}_{query.from_user.id}')],
                    [InlineKeyboardButton("لغو سفارش", callback_data=f'cancel_{query.from_user.id}')]
                ])
            )

    elif query.data.startswith('confirm_'):
        parts = query.data.split('_')
        quantity = int(parts[1])
        user_id = int(parts[2])

        selected_accounts = ACCOUNTS[:quantity]
        ACCOUNTS[:] = ACCOUNTS[quantity:]

        with open(ACCOUNTS_FILE, 'w') as file:
            for acc in ACCOUNTS:
                file.write(f"{acc['email']},{acc['password']},{acc['price']}\n")

        account_info = "\n".join([f"ایمیل: {acc['email']} | رمز: {acc['password']}" for acc in selected_accounts])
        await context.bot.send_message(chat_id=user_id, text=f"سفارش شما تایید شد:\n\n{account_info}")
        await query.edit_message_text("سفارش تایید شد و به کاربر ارسال شد.")

    elif query.data.startswith('cancel_'):
        user_id = int(query.data.split('_')[1])
        await context.bot.send_message(chat_id=user_id, text="سفارش شما لغو شد.")
        await query.edit_message_text("سفارش لغو شد.")

# Handle payment confirmation
async def payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'pending_accounts' in context.user_data:
        transaction_info = update.message.text
        accounts_info = context.user_data['pending_accounts']

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"کاربر {update.effective_user.username} اطلاعات واریز را ارسال کرد:\n{transaction_info}\n"
        )
        await update.message.reply_text("اطلاعات واریز برای مدیر ارسال شد.")

# Main function to run the bot
def main() -> None:
    application = ApplicationBuilder().token('7667045738:AAF5NuZaANiNSqBiydO7HVauRQROGLhfxGI').build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, payment_confirmation))

    application.run_polling()

if __name__ == "__main__":
    main()
