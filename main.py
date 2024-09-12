from telegram import Update, MessageEntity
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, CallbackContext
import asyncio
import sqlite3
import re

TOKEN = '7521576316:AAHiPNQVwbxtjm0khWdP-rQUPbzYCaoTGSg'
INTRO_REGEX_PERSIAN = re.compile(r"#معرفی\s*(.+?)\s*\n+(.+)", re.IGNORECASE | re.DOTALL)

def extract_text_with_entities(message):
    entities = message.entities if message.entities else []
    raw_text = message.text
    result = []
    last_offset = 0

    for entity in entities:
        result.append(raw_text[last_offset:entity.offset])
        entity_text = raw_text[entity.offset:entity.offset + entity.length]

        if entity.type == MessageEntity.SPOILER:
            result.append(f"||{entity_text}||")
        else:
            result.append(entity_text)

        last_offset = entity.offset + entity.length

    result.append(raw_text[last_offset:])

    return ''.join(result)


# Initialize the database
def init_db():
    conn = sqlite3.connect('introductions.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            full_name TEXT,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Insert or update user introduction
def add_user(username, full_name, description):
    conn = sqlite3.connect('introductions.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (username, full_name, description)
        VALUES (?, ?, ?)
    ''', (username, full_name, description))
    conn.commit()
    conn.close()

# Retrieve user introduction
def get_user(username):
    conn = sqlite3.connect('introductions.db')
    cursor = conn.cursor()
    cursor.execute('SELECT full_name, description FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

# Handle user messages (Persian introduction)
async def handle_message(update: Update, context: CallbackContext):
    message = update.message
    formatted_message = extract_text_with_entities(message)
    match = INTRO_REGEX_PERSIAN.match(formatted_message)

    if match:
        full_name = match.group(1).strip()  # First line is the full name
        description = match.group(2).strip()  # Second line is the description
        full_name_escaped = re.escape(full_name)
        description_escaped = re.escape(description)
        if update.message.reply_to_message:
            replied_user = update.message.reply_to_message.from_user.username

            if replied_user:
                if replied_user == 'introduce_CEEE_bot':
                    await update.message.reply_text(f"آقا با این بات بازی نکنید :) به پیام خودتون ریپلای بزنید یا اصلا ریپلای نزنید")
                elif update.message.from_user.username == 's_Ahmad_m_Awal':
                    add_user(replied_user, full_name_escaped, description_escaped)
                    await update.message.reply_text(f"معرفی برای {replied_user} ذخیره شد!")
                else:
                    add_user(update.message.from_user.username, full_name_escaped, description_escaped)
                    await update.message.reply_text(f"""با عرض پوزش با توجه به مطالبات سهیل🙂و دیگر کاربران فقط ادمین ربات میتونه معرفی دیگران رو تغییر بده به همین خاطر معرفی رو برای خودت ذخیره کردم!
اگر میخواید که به افرادی که قابلیت ادیت کردن دارن اضافه شوید به ادمین ربات پیام بدید تا شما رو اضافه کنه با تشکر""")
            else:
                await update.message.reply_text("کاربری که به آن پاسخ داده‌اید، نام کاربری ندارد.")
        else:
            # If not replying to anyone, save the introduction for the message sender
            username = update.message.from_user.username
            if username:
                add_user(username, full_name, description)
                await update.message.reply_text(f"معرفی شما ذخیره شد! خوش آمدید، {full_name}.")
            else:
                await update.message.reply_text("شما نام کاربری ندارید، بنابراین معرفی شما ذخیره نمی‌شود.")
    elif update.message.reply_to_message and formatted_message == "(معرفی)":
        # Handle when a user replies to a message with "معرفی"
        replied_user = update.message.reply_to_message.from_user.username

        if replied_user:
            # Retrieve the introduction of the replied user
            user_info = get_user(replied_user)

            if user_info:
                full_name, description = user_info
                full_name_escaped = re.escape(full_name)
                # description_escaped = re.escape(description)
                await update.message.reply_text(f"\\#معرفی\n{full_name_escaped}\n{description}", parse_mode='MarkdownV2')
            else:
                await update.message.reply_text(f"""متاسفانه معرفی ای برای ایشون ذخیره نشده است😞
لطفا با استفاده از فرمت ذکر شده ایشون رو معرفی کنید
البته حتما روی یکی از پیام های ایشون ریپلای بزنید در غیر اینصورت معرفی برای خود شما ذخیره میشود!""")
    elif formatted_message == "(معرفی)":
        username_user = update.message.from_user.username
        user_info = get_user(username_user)
        if user_info:
            full_name, description = user_info
            full_name_escaped = re.escape(full_name)
            # description_escaped = re.escape(description)
            await update.message.reply_text(f"\\#معرفی\n{full_name_escaped}\n{description}", parse_mode='MarkdownV2')

        else:
            await update.message.reply_text(f"متاسفانه معرفی‌ای برای شما یافت نشد😞 لطفا خودتان را با فرمت ذکر شده معرفی کنید!")
# Handle `/my_intro` command
async def get_introduction(update: Update, context: CallbackContext):
    username = update.message.from_user.username
    user = get_user(username)

    if user:
        full_name, description = user
        full_name_escaped = re.escape(full_name)
        await update.message.reply_text(f"معرفی شما:\nنام کامل: {full_name_escaped}\nتوضیحات: {description}", parse_mode='MarkdownV2')
    else:
        await update.message.reply_text("متاسفانه معرفی‌ای برای شما یافت نشد😞")

# Define the start function
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("سلام!")

# Define the welcome function for new members
async def welcome(update: Update, context: CallbackContext):
    for member in update.message.new_chat_members:
        if member.username == 'introduce_CEEE_bot':
            continue
        if (member.username == 'None'):
            if get_user(member.fullname):
                await update.message.reply_text(
                    f"""سلام مجدد {member.full_name}👋🏻
    دوباره به گروه CEEE خوش اومدی🙃🚶‍♂🔥"""
                )
            else:
                await update.message.reply_text(
                    f"""سلام @{member.full_name}👋🏻
    به گروه CEEE خوش اومدی🔥
    دلیل اصلی ساخت گروه این پیام بوده:
    🔥https://t.me/c/2155182258/171
که خب در عمل بهش عمل نمیکنیم متاسفانه :(
    ولی خب در اصل یک گروه گپ و گفت مشترک دو دانشکدس
    لطفا خودت رو معرفی کن که هم همه باهات آشنا بشن و هم من توی لیستم اضافت کنم😌
    نمونه معرفی:
    https://t.me/c/2155182258/5150""")

        else:
            if get_user(member.username):
                await update.message.reply_text(
                    f"""سلام مجدد @{member.username}👋🏻
    دوباره به گروه CEEE خوش اومدی🙃🚶‍♂🔥"""
                )
            else:
                await update.message.reply_text(
                    f"""سلام @{member.username}👋🏻
    به گروه CEEE خوش اومدی🔥
    دلیل اصلی ساخت گروه این پیام بوده:
    🔥https://t.me/c/2155182258/171
که خب در عمل بهش عمل نمیکنیم متاسفانه :(
    ولی خب در اصل یک گروه گپ و گفت مشترک دو دانشکدس
    لطفا خودت رو معرفی کن که هم همه باهات آشنا بشن و هم من توی لیستم اضافت کنم😌
    نمونه معرفی:
    https://t.me/c/2155182258/5150""")
# Entry point for running the bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    # Initialize the database
    init_db()

    # Add handlers to the application
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("my_intro", get_introduction))  # Add `/my_intro` handler
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))  # Message handler for Persian introductions

    # Run polling to receive updates
    asyncio.run(app.run_polling())
