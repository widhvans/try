import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from pymongo import MongoClient

# --------------------- Configuration Variables ---------------------
# Bot Token from BotFather
BOT_TOKEN = "7530428356:AAEIqnXFYd4yuKTcS12LpmziyPM9phTpQDc"  # BotFather se mila token yahan dalo

# MongoDB Configuration
MONGO_URI = "mongodb+srv://soniji:soniji@cluster0.i5zy74f.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Apna MongoDB URI yahan dalo
DB_NAME = "telegram_bot_db"  # Database ka naam
USERS_COLLECTION = "users"  # Collection ka naam jahan user data save hoga

# Force Subscription Channel
FORCE_SUB_CHANNEL = "@joinnowearn"  # Channel username jahan subscription force karna hai

# Reaction Emoji
REACTION_EMOJI = "👍"  # Group ya channel mein auto reaction ke liye emoji

# Admin Configuration
ADMIN_ID = 1938030055  # Bot owner ka Telegram user ID (broadcast ke liye)

# --------------------- MongoDB Setup ---------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db[USERS_COLLECTION]

# --------------------- Command Handlers ---------------------

# /start Command Handler (Force Subscription Check)
async def start(update: Update, context):
    user_id = update.effective_user.id
    # Check if user is subscribed to the channel
    try:
        member = await context.bot.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            await update.message.reply_text(
                f"Bot use karne ke liye pehle {FORCE_SUB_CHANNEL} join karo!\n"
                f"Join link: https://t.me/{FORCE_SUB_CHANNEL[1:]}"
            )
            return
    except Exception as e:
        print(f"Error checking subscription: {e}")
        await update.message.reply_text("Subscription check karne mein error aaya. Thodi der baad try karo.")
        return
    
    # User ko database mein save karo agar pehle se nahi hai
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id})
    
    await update.message.reply_text(
        "Welcome! Main is bot ka use groups aur channels mein auto reaction ke liye karunga.\n"
        "Mujhe group mein add karo ya channel ke discussion group mein daalo."
    )

# Auto Reaction Handler (Groups aur Channels ke Discussion Groups ke liye)
async def auto_react(update: Update, context):
    # Har naye message pe reaction emoji reply karo
    await update.message.reply_text(REACTION_EMOJI)

# Broadcast Command Handler
async def broadcast(update: Update, context):
    # Sirf admin broadcast kar sakta hai
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Aapko yeh command use karne ki permission nahi hai.")
        return
    
    if not context.args:
        await update.message.reply_text("Broadcast ke liye message type karo. Example: /broadcast Hello everyone!")
        return
    
    message = " ".join(context.args)
    users = users_collection.find()
    sent_count = 0
    failed_count = 0
    
    for user in users:
        try:
            await context.bot.send_message(chat_id=user['user_id'], text=message)
            sent_count += 1
        except Exception as e:
            print(f"User {user['user_id']} ko message send nahi hua: {e}")
            failed_count += 1
    
    await update.message.reply_text(f"Broadcast complete!\nSent: {sent_count}\nFailed: {failed_count}")

# --------------------- Main Function ---------------------
def main():
    # Bot ko initialize karo
    application = Application.builder().token(BOT_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))

    # Auto Reaction ke liye Message Handler (Non-command messages pe reaction)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_react))

    # Bot Start Karo
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
