import os
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from pymongo import MongoClient

# --------------------- Configuration Variables ---------------------
# Bot Token from BotFather (Main Bot)
BOT_TOKEN = "7530428356:AAEIqnXFYd4yuKTcS12LpmziyPM9phTpQDc"  # Apna BotFather token yahan dalo

# MongoDB Configuration
MONGO_URI = "mongodb+srv://soniji:soniji@cluster0.i5zy74f.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Apna MongoDB URI
DB_NAME = "telegram_bot_db"
USERS_COLLECTION = "users"  # Users ka data
CLONES_COLLECTION = "cloned_bots"  # Cloned bots ka data

# Force Subscription Channel
FORCE_SUB_CHANNEL = "@joinnowearn"  # Channel username for force subscription

# Reaction Emojis (Multiple Reactions)
REACTION_EMOJIS = ["👍", "❤", "🔥", "😂", "😍", "👏"]  # Multiple reaction options

# Admin Configuration
ADMIN_ID = 1938030055  # Apna Telegram user ID yahan dalo

# --------------------- MongoDB Setup ---------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db[USERS_COLLECTION]
clones_collection = db[CLONES_COLLECTION]

# --------------------- Helper Functions ---------------------

# Random reaction emoji select karna
def get_random_reaction():
    return random.choice(REACTION_EMOJIS)

# Check if message is from BotFather (for cloning)
def is_botfather_message(update: Update):
    if update.message and update.message.forward_from:
        return update.message.forward_from.username == "BotFather"
    return False

# --------------------- Command Handlers ---------------------

# /start Command Handler (Force Subscription Check)
async def start(update: Update, context):
    user_id = update.effective_user.id
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
    
    # User ko database mein save karo
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id})
    
    await update.message.reply_text(
        "Welcome! Main group aur channel posts pe multiple reactions dunga.\n"
        "Bot clone karne ke liye BotFather se token forward karo.\n"
        "Broadcast ke liye admin use karega /broadcast."
    )

# Auto Reaction Handler (Groups aur Channels ke liye)
async def auto_react(update: Update, context):
    # Check if message is valid (error fix)
    if update.message is None or update.message.text is None:
        return  # Agar message valid nahi hai, skip karo
    
    # Channel ya group ka message ho to reaction do
    if update.message.chat.type in ['group', 'supergroup', 'channel']:
        reaction = get_random_reaction()
        try:
            await update.message.reply_text(reaction)
        except Exception as e:
            print(f"Reaction failed: {e}")

# Clone Bot Handler (BotFather se Token Forward)
async def clone_bot(update: Update, context):
    user_id = update.effective_user.id
    
    # Force subscription check
    try:
        member = await context.bot.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            await update.message.reply_text(
                f"Bot clone karne ke liye pehle {FORCE_SUB_CHANNEL} join karo!\n"
                f"Join link: https://t.me/{FORCE_SUB_CHANNEL[1:]}"
            )
            return
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return
    
    # Check if message is forwarded from BotFather
    if not is_botfather_message(update):
        await update.message.reply_text(
            "Bot clone karne ke liye BotFather se token forward karo.\n"
            "BotFather ko /newbot bolkar token lo aur yahan bhejo."
        )
        return
    
    # Extract token from forwarded message
    forwarded_text = update.message.text
    if "Here is your token" not in forwarded_text:
        await update.message.reply_text("Yeh valid BotFather token nahi hai. Sahi token forward karo.")
        return
    
    token = forwarded_text.splitlines()[-1].strip()  # Token last line mein hota hai
    
    # Save cloned bot data to MongoDB
    clone_data = {
        "user_id": user_id,
        "token": token,
        "created_at": update.message.date.isoformat()
    }
    clones_collection.insert_one(clone_data)
    
    await update.message.reply_text(
        f"Bot successfully cloned!\nToken: {token}\n"
        "Is token ka use karke aap apna bot deploy kar sakte ho.\n"
        "Code copy karke apne server pe run karo."
    )

# Broadcast Command Handler
async def broadcast(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Sirf admin broadcast kar sakta hai.")
        return
    
    if not context.args:
        await update.message.reply_text("Broadcast ke liye message type karo: /broadcast <message>")
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
    application = Application.builder().token(BOT_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))
    
    # Message Handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_react))
    application.add_handler(MessageHandler(filters.FORWARDED, clone_bot))

    # Bot Start Karo
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
