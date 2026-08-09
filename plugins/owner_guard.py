from telethon import events
from main import bot
from utils import IS_OWNER, get_emoji
from config import EMOJI_ID_CROSS

@bot.on(events.ChatAction)
async def auto_leave_unauthorized_groups(event):
    if event.is_group or event.is_channel:
        me = await bot.get_me()
        if event.user_added and event.user_id == me.id:
            if not IS_OWNER(event.added_by_id):
                msg = (
                    f"{get_emoji(EMOJI_ID_CROSS, '❌')} <b>AKSES DITOLAK!</b>\n\n"
                    "<blockquote>Bot Pesan Berulang ini khusus dipasang oleh OWNER!</blockquote>"
                )
                await event.respond(msg, parse_mode="html")
                await bot.leave_chat(event.chat_id)
