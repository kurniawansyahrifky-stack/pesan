import json
from telethon import Button
from config import OWNER_IDS

def IS_OWNER(user_id: int) -> bool:
    return user_id in OWNER_IDS

def get_emoji(emoji_id: str, fallback: str = "✨") -> str:
    """Fungsi pembentuk Tag HTML Emoji Premium"""
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

def parse_custom_buttons(button_raw_str: str):
    """
    Format parser tombol kustom unlimited:
    Tombol 1 - https://link.com [primary] | Tombol 2 - https://link.com [danger]
    Gunakan 'baris baru' untuk pindah baris tombol.
    """
    if not button_raw_str or not button_raw_str.strip():
        return None

    rows = []
    lines = button_raw_str.strip().split('\n')
    
    for line in lines:
        row = []
        items = line.split('|')
        for item in items:
            if '-' in item:
                style = "primary" # Default style telethon
                raw = item.strip()
                
                if '[danger]' in raw:
                    style = "danger"
                    raw = raw.replace('[danger]', '')
                elif '[success]' in raw:
                    style = "success"
                    raw = raw.replace('[success]', '')
                elif '[primary]' in raw:
                    style = "primary"
                    raw = raw.replace('[primary]', '')

                parts = raw.split('-', 1)
                text = parts[0].strip()
                url = parts[1].strip()
                row.append({"text": text, "url": url, "style": style})
        if row:
            rows.append(row)
            
    return json.dumps(rows) if rows else None
