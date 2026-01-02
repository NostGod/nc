import asyncio
import os
import threading
import json
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import RetryAfter, Forbidden, BadRequest

# --- CONFIGURATION ---
AUTHORIZED_USERS = [7831276550]

# Add your 4 tokens here:
# Index 0, 1 -> Name Change Bots
# Index 2, 3 -> Text Spam Bots
TOKENS = [
    "8438165700:AAH-LagtErrIU23-iGujGb_30eHIRpXP-r0", # NC Bot 1
    "8558866135:AAGUXp7S_O7xXDcItQq_oJrbe8CWd0mpE-M", # NC Bot 2
    "8550943525:AAFbseXlKl8IqAlZ0V0G2F4gM3hZHLjtCRQ", # Text Bot 1
    "8207344285:AAF9fQ1KXWoNLpEq1bgdNfiJbIsGKHV_fdM"  # Text Bot 2
]

MEMORY_FILE = "army_roles_memory.json"
MASTER_EMOJIS = [chr(i) for i in range(0x1F600, 0x1F64F)] + [chr(i) for i in range(0x1F300, 0x1F5FF)]
ACTIVE_GROUPS = {}

# --- MEMORY ---
def load_memory():
    global ACTIVE_GROUPS
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                ACTIVE_GROUPS = {int(k): v for k, v in json.load(f).items()}
        except: pass

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(ACTIVE_GROUPS, f)

# --- SPECIALIZED WORKERS ---

async def nc_worker(bot, bot_index):
    """Specific logic for Name Change Bots (0 and 1)"""
    e_idx = 0
    while True:
        if not ACTIVE_GROUPS:
            await asyncio.sleep(2)
            continue
        
        for chat_id, data in list(ACTIVE_GROUPS.items()):
            try:
                emoji = MASTER_EMOJIS[e_idx % len(MASTER_EMOJIS)]
                title = f"({data['name']}) 𝗡𝗖 𝗞𝗔𝗥 {emoji}"
                await bot.set_chat_title(chat_id=chat_id, title=title)
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [NC-BOT #{bot_index}] -> {chat_id}")
                e_idx += 1
                await asyncio.sleep(1.5) 
            except RetryAfter as e: await asyncio.sleep(e.retry_after)
            except Exception: await asyncio.sleep(1)

async def spam_worker(bot, bot_index):
    """Specific logic for Text Spam Bots (2 and 3)"""
    while True:
        if not ACTIVE_GROUPS:
            await asyncio.sleep(2)
            continue
        
        for chat_id, data in list(ACTIVE_GROUPS.items()):
            try:
                text = f"{data['name']} 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗢 𝗖𝗛𝗢𝗗 𝗞𝗘 𝗖𝗛𝗔𝗕𝗔 𝗝𝗔𝗬𝗘 𝗡𝗢𝗦𝗧-𝗦𝗛𝗔𝗥-𝗘𝗥𝗘𝗡 🔥"
                await bot.send_message(chat_id=chat_id, text=text)
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [TEXT-BOT #{bot_index}] -> {chat_id}")
                await asyncio.sleep(1.2)
            except RetryAfter as e: await asyncio.sleep(e.retry_after)
            except Exception: await asyncio.sleep(1)

# --- COMMANDS ---

async def attack_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unified command to start both NC and Text spam"""
    if update.effective_user.id in AUTHORIZED_USERS:
        name = " ".join(context.args) if context.args else "TARGET"
        ACTIVE_GROUPS[update.effective_chat.id] = {"name": name}
        save_memory()
        await update.message.reply_text(f"🚀 **ROLES ASSIGNED & ATTACK STARTED**\nTarget: {name}")

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in AUTHORIZED_USERS:
        cid = update.effective_chat.id
        if cid in ACTIVE_GROUPS:
            del ACTIVE_GROUPS[cid]
            save_memory()
            await update.message.reply_text("🛑 **ALL BOTS STOPPED**")

# --- MAIN RUNNER ---

def run_bot(token, index):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        app = ApplicationBuilder().token(token).build()
        app.add_handler(CommandHandler("start", attack_cmd))
        app.add_handler(CommandHandler("stop", stop_cmd))
        
        # ASSIGN ROLES BASED ON INDEX
        if index < 2:
            print(f">>> [INIT] Bot #{index} assigned to NAME CHANGE")
            loop.create_task(nc_worker(app.bot, index))
        else:
            print(f">>> [INIT] Bot #{index} assigned to TEXT SPAM")
            loop.create_task(spam_worker(app.bot, index))
            
        app.run_polling(drop_pending_updates=True, stop_signals=None)
    except Exception as e:
        print(f"Bot {index} error: {e}")

if __name__ == "__main__":
    load_memory()
    print("="*50)
    print("  NC & TEXT ARMY - ROLE SYSTEM ONLINE")
    print(f"  AUTHORIZED: {AUTHORIZED_USERS[0]}")
    print("="*50)
    
    for i, t in enumerate(TOKENS):
        threading.Thread(target=run_bot, args=(t, i), daemon=True).start()
    
    threading.Event().wait()
