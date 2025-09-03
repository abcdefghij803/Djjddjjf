import asyncio
from telethon import TelegramClient, events
from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URL
from database import Database

db = Database(MONGO_URL)
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

HELP_TEXT = """
Commands:
/connect <string_session> - Connect your Telethon session
/me - Show your assets
/transfer <asset> @username [amount] - Transfer assets
Assets = nft, stars, gifts, premium
"""

@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    await db.ensure_user(event.sender_id)
    await event.reply("👋 Welcome to TransferBot!\n\n" + HELP_TEXT)

@bot.on(events.NewMessage(pattern=r"^/connect"))
async def connect_handler(event):
    parts = event.raw_text.split(maxsplit=1)
    if len(parts) < 2:
        return await event.reply("Usage: /connect <your_string_session>")

    session = parts[1].strip()
    await db.set_session(event.sender_id, session)
    await event.reply("✅ Your string session has been saved.")

@bot.on(events.NewMessage(pattern="/me"))
async def me_handler(event):
    user = await db.get_user(event.sender_id)
    msg = (
        f"📊 Your assets:\n"
        f"NFTs: {user['nft']}\n"
        f"Stars: {user['stars']}\n"
        f"Gifts: {user['gifts']}\n"
        f"Premium: {'✅' if user['premium'] else '❌'}"
    )
    await event.reply(msg)

@bot.on(events.NewMessage(pattern=r"^/transfer"))
async def transfer_handler(event):
    parts = event.raw_text.split()
    if len(parts) < 3:
        return await event.reply("Usage: /transfer <asset> @username [amount]")

    asset = parts[1].lower()
    recipient_username = parts[2].lstrip("@")
    amount = 1

    if asset not in ("nft", "stars", "gifts", "premium"):
        return await event.reply("Invalid asset. Allowed: nft, stars, gifts, premium.")

    if asset != "premium" and len(parts) >= 4:
        try:
            amount = int(parts[3])
            if amount < 1:
                raise ValueError
        except:
            return await event.reply("Amount must be positive integer.")

    try:
        recipient_entity = await bot.get_entity(recipient_username)
        recipient_id = recipient_entity.id
    except Exception:
        return await event.reply("❌ Could not find recipient user.")

    # ensure recipient exists in DB
    await db.ensure_user(recipient_id)

    ok = await db.transfer_asset(event.sender_id, recipient_id, asset, amount)

    if ok:
        if asset == "premium":
            msg = f"✅ Premium transferred to @{recipient_username}"
        else:
            msg = f"✅ Transferred {amount} {asset}(s) to @{recipient_username}"
        await event.reply(msg)
    else:
        await event.reply("❌ Transfer failed. Not enough assets or invalid.")

if __name__ == "__main__":
    print("Bot started...")
    bot.run_until_disconnected()
