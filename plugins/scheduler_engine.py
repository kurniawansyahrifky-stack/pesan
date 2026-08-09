import json
import os
from telethon import events, Button
from main import bot, scheduler
from database import get_db
from utils import IS_OWNER, get_emoji, parse_custom_buttons
from config import (
    EMOJI_ID_ROCKET, EMOJI_ID_CHECK, EMOJI_ID_CROSS, EMOJI_ID_TIME,
    EMOJI_ID_BULLET, EMOJI_ID_NOTE, EMOJI_ID_BUTTON
)

user_fsm = {}

# --- CORE JOB: KIRIM PESAN BERULANG ---
async def execute_periodic_job(task_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT chat_id, msg_text, photo_path, buttons_json, last_msg_id FROM periodic_tasks WHERE id=? AND status='RUNNING'", (task_id,))
    task = c.fetchone()

    if not task:
        conn.close()
        return

    chat_id, msg_text, photo_path, buttons_json, last_msg_id = task

    # Telethon Styled Inline Buttons
    tele_buttons = []
    if buttons_json:
        parsed_rows = json.loads(buttons_json)
        for row in parsed_rows:
            btn_row = []
            for b in row:
                btn_row.append(Button.url(b['text'], b['url']))
            tele_buttons.append(btn_row)

    # Auto Delete Last Message
    if last_msg_id:
        try:
            await bot.delete_messages(chat_id, last_msg_id)
        except:
            pass

    # Send Message with Telethon HTML + Premium Emojis Native
    try:
        if photo_path and os.path.exists(photo_path):
            sent = await bot.send_file(chat_id, photo_path, caption=msg_text or "", buttons=tele_buttons or None, parse_mode="html")
        else:
            sent = await bot.send_message(chat_id, msg_text, buttons=tele_buttons or None, parse_mode="html")

        if sent:
            c.execute("UPDATE periodic_tasks SET last_msg_id=? WHERE id=?", (sent.id, task_id))
            conn.commit()
    except Exception as e:
        print(f"❌ Error Job ID #{task_id}: {e}")
    finally:
        conn.close()


# --- DASHBOARD LIST PESAN 1, PESAN 2, DST ---
@bot.on(events.CallbackQuery)
async def scheduler_callback(event):
    data = event.data.decode('utf-8')
    user_id = event.sender_id

    if not IS_OWNER(user_id):
        return await event.answer("❌ Akses Khusus Owner!", alert=True)

    if data == "manage_tasks":
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, title, interval_val, interval_type, start_hour FROM periodic_tasks")
        tasks = c.fetchall()
        conn.close()

        text = f"{get_emoji(EMOJI_ID_ROCKET, '🚀')} <b>DAFTAR PESAN BERULANG AKTIF:</b>\n\n"
        buttons = []

        if tasks:
            for t in tasks:
                text += f"• <b>{t['title']}</b> (ID #{t['id']}) - Tiap {t['interval_val']} {t['interval_type']} (Jam {t['start_hour']:02d}:00)\n"
                buttons.append([
                    Button.inline(f"✏️ Edit #{t['id']}", f"edit_task_{t['id']}".encode('utf-8')),
                    Button.inline(f"🗑️ Hapus #{t['id']}", f"del_task_{t['id']}".encode('utf-8'))
                ])
        else:
            text += "<i>Belum ada pesan berulang yang dibuat.</i>\n"

        buttons.append([Button.inline("➕ Tambah Pesan Baru", b"create_task")])
        buttons.append([Button.inline("🔙 Kembali", b"menu_main")])
        await event.edit(text, buttons=buttons, parse_mode="html")

    elif data == "menu_main":
        user_fsm.pop(user_id, None)
        from plugins.start_menu import show_dashboard
        await show_dashboard(event)

    elif data == "close_panel":
        await event.delete()

    elif data == "create_task":
        user_fsm[user_id] = {'step': 'TITLE', 'chat_id': event.chat_id}
        await event.edit(
            f"{get_emoji(EMOJI_ID_NOTE, '📝')} <b>LANGKAH 1: Masukkan Judul Pesan</b>\n"
            "Contoh: <code>Pesan 1 - Promosi</code> atau <code>Pesan 2 - Rules</code>",
            buttons=[[Button.inline("❌ Batal", b"manage_tasks")]],
            parse_mode="html"
        )

    elif data.startswith("del_task_"):
        tid = int(data.split("_")[2])
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM periodic_tasks WHERE id=?", (tid,))
        conn.commit()
        conn.close()

        try:
            scheduler.remove_job(f"task_{tid}")
        except:
            pass

        await event.answer(f"✅ Pesan #{tid} Dihapus!", alert=True)
        event.data = b"manage_tasks"
        await scheduler_callback(event)

    elif data.startswith("hour_"):
        shour = int(data.split("_")[1])
        user_fsm[user_id]['start_hour'] = shour
        
        buttons = [
            [
                Button.inline("⏱️ 5 Mnt", b"inter_m_5"),
                Button.inline("⏱️ 15 Mnt", b"inter_m_15"),
                Button.inline("⏱️ 30 Mnt", b"inter_m_30")
            ],
            [
                Button.inline("⏳ 1 Jam", b"inter_h_1"),
                Button.inline("⏳ 2 Jam", b"inter_h_2"),
                Button.inline("⏳ 5 Jam", b"inter_h_5")
            ]
        ]
        await event.edit(f"{get_emoji(EMOJI_ID_TIME, '⏰')} <b>LANGKAH 5: Pilih Durasi Pengulangan Pesan</b>", buttons=buttons, parse_mode="html")

    elif data.startswith("inter_"):
        parts = data.split("_")
        itype = "minute" if parts[1] == 'm' else "hour"
        ival = int(parts[2])

        state = user_fsm[user_id]
        
        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO periodic_tasks (title, chat_id, msg_text, photo_path, buttons_json, start_hour, interval_type, interval_val)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
            state['title'], state['chat_id'], state['text'], state.get('photo_path'),
            state.get('buttons_json'), state['start_hour'], itype, ival
        ))
        task_id = c.lastrowid
        conn.commit()
        conn.close()

        if itype == 'minute':
            scheduler.add_job(execute_periodic_job, 'interval', minutes=ival, args=[task_id], id=f"task_{task_id}")
        else:
            scheduler.add_job(execute_periodic_job, 'interval', hours=ival, args=[task_id], id=f"task_{task_id}")

        if not scheduler.running:
            scheduler.start()

        user_fsm.pop(user_id, None)
        await event.edit(
            f"{get_emoji(EMOJI_ID_CHECK, '✅')} <b>PESAN [{state['title']}] (ID #{task_id}) BERHASIL DISIMPAN & DIJALANKAN!</b>",
            buttons=[[Button.inline("🔙 Kembali ke List", b"manage_tasks")]],
            parse_mode="html"
        )

# --- INPUT LISTENER (FSM CONVERSATION) ---
@bot.on(events.NewMessage)
async def input_fsm_handler(event):
    user_id = event.sender_id
    if user_id not in user_fsm or event.text.startswith('/'):
        return

    state = user_fsm[user_id]
    step = state.get('step')

    if step == 'TITLE':
        state['title'] = event.text
        state['step'] = 'TEXT'
        await event.respond(f"{get_emoji(EMOJI_ID_BULLET, '🔹')} <b>LANGKAH 2: Kirim Teks Pesan Berulang</b>", parse_mode="html")

    elif step == 'TEXT':
        state['text'] = event.text
        state['step'] = 'BUTTONS'
        await event.respond(
            f"{get_emoji(EMOJI_ID_BUTTON, '🔘')} <b>LANGKAH 3: Masukkan Custom Buttons</b>\n\n"
            "Format:\n"
            "<code>Tombol 1 - https://link1.com | Tombol 2 - https://link2.com</code>\n\n"
            "<i>Ketik <b>skip</b> jika tanpa tombol.</i>",
            parse_mode="html"
        )

    elif step == 'BUTTONS':
        if event.text.lower() != 'skip':
            state['buttons_json'] = parse_custom_buttons(event.text)
        else:
            state['buttons_json'] = None

        state['step'] = 'HOUR'
        
        btns = []
        row = []
        for h in range(24):
            row.append(Button.inline(f"{h:02d}:00", f"hour_{h}".encode('utf-8')))
            if len(row) == 4:
                btns.append(row)
                row = []
        if row:
            btns.append(row)

        await event.respond(f"{get_emoji(EMOJI_ID_TIME, '⏰')} <b>LANGKAH 4: Pilih Jam Mulai Pengiriman</b>", buttons=btns, parse_mode="html")
