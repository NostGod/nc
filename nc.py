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
TOKENS = [
    "8438165700:AAH-LagtErrIU23-iGujGb_30eHIRpXP-r0", 
    "8558866135:AAGUXp7S_O7xXDcItQq_oJrbe8CWd0mpE-M"
]

MEMORY_FILE = "nc_memory.json"
MASTER_EMOJIS = [chr(i) for i in range(0x1F600, 0x1F64F)] + [chr(i) for i in range(0x1F300, 0x1F5FF)]
ACTIVE_GROUPS = {}

def load_memory():
    global ACTIVE_GROUPS
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            try:
                ACTIVE_GROUPS = {int(k): v for k, v in json.load(f).items()}
            except:
                ACTIVE_GROUPS = {}

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(ACTIVE_GROUPS, f)

def log_flood_console(bot_idx, chat_id, name, emoji):
    t = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{t}] [BOT #{bot_idx}] [GC: {chat_id}] -> ({name}) 𝗡𝗖 𝗞𝗔𝗥 {emoji}")

# --- WORKER (1-1 ROTATION) ---
async def individual_bot_worker(bot, bot_index):
    try: await bot.initialize()
    except: pass

    e_idx = 0
    while True:
        load_memory()
        if not ACTIVE_GROUPS:
            await asyncio.sleep(2)
            continue

        # Convert to list to iterate 1-1 across all groups
        group_list = list(ACTIVE_GROUPS.items())
        
        for chat_id, data in group_list:
            # Check if stop was called mid-loop
            if chat_id not in ACTIVE_GROUPS:
                continue
                
            try:
                emoji = MASTER_EMOJIS[e_idx % len(MASTER_EMOJIS)]
                title = f"({data['name']}) 𝗡𝗖 𝗞𝗔𝗥 {emoji}"
                
                await bot.set_chat_title(chat_id=chat_id, title=title)
                log_flood_console(bot_index, chat_id, data['name'], emoji)
                
                e_idx += 1
                # FIXED DELAY: 1 Second
                await asyncio.sleep(1) 

            except (Forbidden, BadRequest):
                # Bot removed from admin or group
                continue
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except Exception:
                await asyncio.sleep(1)
        
        await asyncio.sleep(0.1)

# --- COMMANDS ---
async def nc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in AUTHORIZED_USERS:
        name = " ".join(context.args) if context.args else "TARGET"
        ACTIVE_GROUPS[update.effective_chat.id] = {"name": name}
        save_memory()

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in AUTHORIZED_USERS:
        cid = update.effective_chat.id
        if cid in ACTIVE_GROUPS:
            del ACTIVE_GROUPS[cid]
            save_memory()

def run_bot(token, index):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        app = ApplicationBuilder().token(token).build()
        app.add_handler(CommandHandler("nc", nc_cmd))
        app.add_handler(CommandHandler("stop", stop_cmd))
        
        loop.create_task(individual_bot_worker(app.bot, index))
        app.run_polling(drop_pending_updates=True, stop_signals=None)
    except Exception: pass

if __name__ == "__main__":
    load_memory()
    print("="*45)
    print("NC ARMY SYSTEM ONLINE | DELAY: 1s | 1-1 ROTATION")
    print("AUTHORIZED USER: 7831276550")
    print("="*45)
    for i, t in enumerate(TOKENS):
        threading.Thread(target=run_bot, args=(t, i), daemon=True).start()
    threading.Event().wait()
