import os
import random
from telethon import TelegramClient, events
from telethon.tl.types import ReactionEmoji
from pymongo import MongoClient

# --------------------- Configuration Variables ---------------------
API_ID = 123456  # Your API ID from my.telegram.org
API_HASH = "your_api_hash_here"  # Your API Hash from my.telegram.org
PHONE_NUMBER = "+1234567890"  # Your phone number (with country code)
SESSION_NAME = "bot_session"  # Session file name

MONGO_URI = "mongodb+srv://your_username:your_password@cluster0.mongodb.net/your_db_name?retryWrites=true&w=majority"
DB_NAME = "telegram_bot_db"
USERS_COLLECTION = "users"
CLONES_COLLECTION = "cloned_bots"

FORCE_SUB_CHANNEL = "@your_channel_username"  # Force subscription channel
REACTION_EMOJIS = ["👍", "❤", "🔥", "😂", "😍", "👏"]  # Reaction options
ADMIN_ID = 123456789  # Your Telegram ID

# --------------------- MongoDB Setup ---------------------
client_db = MongoClient(MONGO_URI)
db = client_db[DB_NAME]
users_collection = db[USERS_COLLECTION]
clones_collection = db[CLONES_COLLECTION]

# --------------------- Telegram Client Setup ---------------------
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# --------------------- Helper Functions ---------------------
def get_random_reaction():
    return ReactionEmoji(emoticon=random.choice(REACTION_EMOJIS))

async def check_subscription(client, user_id):
    try:
        participant = await client.get_participants(FORCE_SUB_CHANNEL, filter=lambda x: x.id == user_id)
        return len(participant) > 0
    except Exception as e:
        print(f"Subscription check failed: {e}")
        return False

# --------------------- Event Handlers ---------------------

# Start Command
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    if not await check_subscription(client, user_id):
        await event.reply(
            f"Bot use karne ke liye pehle {FORCE_SUB_CHANNEL} join karo!\n"
            f"Join link: https://t.me/{FORCE_SUB_CHANNEL[1:]}"
        )
        return
    
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id})
    
    await event.reply(
        "Welcome! Main group aur channel posts pe official reactions dunga.\n"
        "Bot clone karne ke liye BotFather se token forward karo."
    )

# Auto Reaction on Channel/Group Posts
@client.on(events.NewMessage(chats=[FORCE_SUB_CHANNEL]))  # Add more channels/groups if needed
async def auto_react(event):
    if event.is_channel or event.is_group:
        reaction = get_random_reaction()
        try:
            await client.set_reaction(event.chat_id, event.message.id, reaction)
        except Exception as e:
            print(f"Reaction failed: {e}")

# Clone Bot Handler
@client.on(events.NewMessage(forwards=True))
async def clone_bot(event):
    user_id = event.sender_id
    if not await check_subscription(client, user_id):
        await event.reply(
            f"Clone karne ke liye {FORCE_SUB_CHANNEL} join karo!\n"
            f"Join link: https://t.me/{FORCE_SUB_CHANNEL[1:]}"
        )
        return
    
    if event.message.forward and event.message.forward.from_username == "BotFather":
        forwarded_text = event.message.text
        if "Here is your token" not in forwarded_text:
            await event.reply("Valid BotFather token forward karo.")
            return
        
        token = forwarded_text.splitlines()[-1].strip()
        clone_data = {
            "user_id": user_id,
            "token": token,
            "created_at": event.message.date.isoformat()
        }
        clones_collection.insert_one(clone_data)
        
        await event.reply(f"Bot cloned!\nToken: {token}\nCode copy karke deploy karo.")

# Broadcast Command
@client.on(events.NewMessage(pattern='/broadcast'))
async def broadcast(event):
    if event.sender_id != ADMIN_ID:
        await event.reply("Sirf admin broadcast kar sakta hai.")
        return
    
    message = event.raw_text.replace('/broadcast', '').strip()
    if not message:
        await event.reply("Broadcast ke liye message do: /broadcast <message>")
        return
    
    users = users_collection.find()
    sent_count = 0
    failed_count = 0
    
    for user in users:
        try:
            await client.send_message(user['user_id'], message)
            sent_count += 1
        except Exception as e:
            print(f"User {user['user_id']} ko message nahi gaya: {e}")
            failed_count += 1
    
    await event.reply(f"Broadcast complete!\nSent: {sent_count}\nFailed: {failed_count}")

# --------------------- Main Function ---------------------
async def main():
    await client.start(phone=PHONE_NUMBER)
    print("Bot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
