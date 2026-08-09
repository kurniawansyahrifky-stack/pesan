import traceback
from telethon import events, Button
from main import bot
from utils import IS_OWNER
from config import OWNER_IDS

# LISTENER LIVE: Print semua chat yang masuk ke terminal VPS
@bot.on(events.NewMessage)
async def global_debug_listener(event):
    if event.is_private:
        sender = await event.get_sender()
        print(f"📩 [CHAT MASUK] Dari: {sender.first_name} (ID: {event.sender_id}) | Teks: '{event.text}'")

@bot.on(events.NewMessage(pattern=r'^/(start|settings|menu)(?:@\w+)?'))
async def main_menu_handler(event):
    try:
        user_id = event.sender_id
        print(f"🎯 Command Executed: {event.text} oleh User: {user_id}")

        if not IS_OWNER(user_id):
            print(f"⚠️ User {user_id} BUKAN OWNER! Owner terdaftar: {OWNER_IDS}")
            msg_denied = (
                f"❌ <b>AKSES DITOLAK!</b>\n\n"
                f"ID Telegram Anda: <code>{user_id}</code>\n"
                f"Belum terdaftar di <code>OWNER_IDS</code> pada file <code>config.py</code>."
            )
            await event.reply(msg_denied, parse_mode="html")
            return

        await show_dashboard(event)
    except Exception as e:
        print(f"❌ ERROR PADA HANDLER START: {e}")
        traceback.print_exc()

async def show_dashboard(event):
    text = (
        "✨ <b>PANEL BOT PESAN BERULANG (TELETHON)</b>\n\n"
        "Selamat datang di Panel Kontrol Bot Pesan Berulang.\n"
        "Gunakan tombol di bawah untuk mengelola semua pesan berulang."
    )

    # Tombol Inline Telethon Standard
    buttons = [
        [Button.inline("⚙️ Kelola Multi-Pesan", b"manage_tasks")],
        [Button.inline("➕ Buat Pesan Baru", b"create_task")],
        [Button.inline("❌ Tutup Menu", b"close_panel")]
    ]

    try:
        if isinstance(event, events.CallbackQuery.Event):
            await event.edit(text, buttons=buttons, parse_mode="html")
        else:
            await event.reply(text, buttons=buttons, parse_mode="html")
        print("✅ [TERKIRIM SUKSES] Balasan menu berhasil dikirim ke Telegram!")
    except Exception as e:
        print(f"❌ GAGAL MENGIRIM PESAN BALASAN: {e}")
        traceback.print_exc()
