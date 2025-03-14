import random
from telethon import TelegramClient, events
from telethon.tl.types import ReactionEmoji
from pymongo import MongoClient

# --------------------- Configuration Variables ---------------------
API_ID = 28196292  # Your API ID from my.telegram.org (Apna API ID daal do)
API_HASH = "7938119512:AAG3r2E3ag7UEo75wVGkLK9zFWpK7k97SYM"  # Your API Hash from my.telegram.org (Apna API Hash daal do)
SESSION_FILE = "1BJWap1sBu6RdktbIA6aJGooNFEGKK8_hXJmVyNyGwXNzG4U6RzkC0wVG_j4FXU3fdKFKN8pVnVKzIOkQGoZ4xxXHWB0dQfBUgCWnaOsnsLt2l00R9y8LGk9tWJsrtm0MJPVuJw3-SJwmd25QmQ7W7PLjtnpzmbWp-M4tOP2Aj3UeRwz7yuEMxKf00DB0l8ky7rQdD4ipD_kB__Cblc0y52XSHzrEGBSAsG_9v66dCaHvALeJugd-03JrmrEUve1sYfQ9P7qQFE5MrHzLc_c3nQ7Y1pU5B_Kp_O-3oVqX6eOzjP0KZUiCJIJz7VtoP1Yj8CF4GDrwy8cR5ObNE6dWlFEaaOw6ooA=.session"  # Session file ka naam (e.g., session_file.session)

# BotFather Token (for cloning feature)
BOT_TOKEN = "7345897707:AAHWi7-DSbv9VASFSP6nXGQIsu_oKdq8Vl4"

# MongoDB Configuration
MONGO_URI = "mongodb+srv://soniji:soniji@cluster0.i5zy74f.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "telegram_bot_db"
USERS_COLLECTION = "users"
CLONES_COLLECTION = "cloned_bots"

# Force Subscription Channel
FORCE_SUB_CHANNEL = "@joinnowearn"

# Reaction Emojis (Multiple Reactions)
REACTION_EMOJIS = ["👍", "❤", "🔥", "😂", "😍", "👏"]

# Admin Configuration
ADMIN_ID = 123456789  # Apna Telegram user ID daal do

# --------------------- MongoDB Setup ---------------------
client_db = MongoClient(MONGO_URI)
db = client_db[DB_NAME]
users_collection = db[USERS_COLLECTION]
clones_collection = db[CLONES_COLLECTION]

# --------------------- Telegram Client Setup ---------------------
# Session file ke saath client initialize kiya gaya
client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

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
@client.on(events.NewMessage(chats=[FORCE_SUB_CHANNEL]))
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
    await client.start()  # Session file se automatically connect hoga
    print("Bot is running...")
    await client.run_until_disconnected()

if _name_ == '_main_':
    client.loop.run_until_complete(main())
