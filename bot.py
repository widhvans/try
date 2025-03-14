import os
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from pymongo import MongoClient

# --------------------- Configuration Variables ---------------------
BOT_TOKEN = "7530428356:AAEIqnXFYd4yuKTcS12LpmziyPM9phTpQDc"  # BotFather se token
MONGO_URI = "mongodb+srv://soniji:soniji@cluster0.i5zy74f.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "telegram_bot_db"
USERS_COLLECTION = "users"
CLONES_COLLECTION = "cloned_bots"
FORCE_SUB_CHANNEL = "@joinnowearn"  # Force subscription channel
REACTION_EMOJIS = ["👍", "❤", "🔥", "😂", "😍", "👏"]  # Multiple reaction emojis
ADMIN_ID = 1938030055  # Admin Telegram ID

# --------------------- MongoDB Setup ---------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db[USERS_COLLECTION]
clones_collection = db[CLONES_COLLECTION]

# --------------------- Helper Functions ---------------------
def get_random_reaction():
    return random.choice(REACTION_EMOJIS)

def is_botfather_message(update: Update):
    if update.message and update.message.forward_from:
        return update.message.forward_from.username == "BotFather"
    return False

# --------------------- Command Handlers ---------------------

# /start Command Handler
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
        await update.message.reply_text("Subscription check mein error. Thodi der baad try karo.")
        return
    
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id})
    
    await update.message.reply_text(
        "Welcome! Main group aur channel posts pe reactions dunga.\n"
        "Channel mein kaam karne ke liye mujhe admin banao ya discussion group mein add karo."
    )

# Auto Reaction Handler
async def auto_react(update: Update, context):
    # Check if update has a valid message
    if update.message is None:
        # Channel post ho sakta hai, check channel_post
        if update.channel_post is None:
            return  # Agar dono None hain, skip karo
        # Channel post pe reaction
        reaction = get_random_reaction()
        try:
            await context.bot.send_message(
                chat_id=update.channel_post.chat_id,
                text=reaction,
                reply_to_message_id=update.channel_post.message_id
            )
        except Exception as e:
            print(f"Channel reaction failed: {e}")
        return
    
    # Group ya supergroup message pe reaction
    if update.message.chat.type in ['group', 'supergroup']:
        reaction = get_random_reaction()
        try:
            await update.message.reply_text(reaction)
        except Exception as e:
            print(f"Group reaction failed: {e}")

# Clone Bot Handler
async def clone_bot(update: Update, context):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            await update.message.reply_text(
                f"Clone karne ke liye {FORCE_SUB_CHANNEL} join karo!\n"
                f"Join link: https://t.me/{FORCE_SUB_CHANNEL[1:]}"
            )
            return
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return
    
    if not is_botfather_message(update):
        await update.message.reply_text(
            "BotFather se token forward karo.\n/newbot se token lo aur yahan bhejo."
        )
        return
    
    forwarded_text = update.message.text
    if "Here is your token" not in forwarded_text:
        await update.message.reply_text("Valid BotFather token forward karo.")
        return
    
    token = forwarded_text.splitlines()[-1].strip()
    clone_data = {
        "user_id": user_id,
        "token": token,
        "created_at": update.message.date.isoformat()
    }
    clones_collection.insert_one(clone_data)
    
    await update.message.reply_text(f"Bot cloned!\nToken: {token}\nCode copy karke deploy karo.")

# Broadcast Command Handler
async def broadcast(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Sirf admin broadcast kar sakta hai.")
        return
    
    if not context.args:
        await update.message.reply_text("Broadcast ke liye message do: /broadcast <message>")
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
            print(f"User {user['user_id']} ko message nahi gaya: {e}")
            failed_count += 1
    
    await update.message.reply_text(f"Broadcast complete!\nSent: {sent_count}\nFailed: {failed_count}")

# --------------------- Main Function ---------------------
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_react))
    application.add_handler(MessageHandler(filters.FORWARDED, clone_bot))

    # Channel Post Handler
    application.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, auto_react))

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
