import json
import os
from config import OWNER_ID

DB_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_WELCOME_TEXT = (
    "🎬 **Rᴇᴀᴅʏ Tᴏ Mᴀᴋᴇ Tʜᴜᴍʙɴᴀɪʟs Tʜᴀᴛ Hɪᴛ Dɪғғᴇʀᴇɴᴛ ❔**\n\n"
    "➡️ **I'ᴍ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ Tʜᴜᴍʙɴᴀɪʟ Cʀᴇᴀᴛᴏʀ 🤖**\n"
    "➡️ **Sᴘᴇᴄɪᴀʟɪᴢɪɴɢ ɪɴ ᴇʏᴇ-ᴄᴀᴛᴄʜɪɴɢ ᴅᴇsɪɢɴs ᴛʜᴀᴛ ᴅʀɪᴠᴇ ᴄʟɪᴄᴋs 🖼️**\n\n"
    "☸️ **Wʜᴀᴛ Cᴀɴ I Cʀᴇᴀᴛᴇ ❔**\n\n"
    "➡️ **Aɴɪᴍᴇ Tʜᴜᴍʙɴᴀɪʟs 🎌**\n"
    "➡️ **Mᴏᴠɪᴇ Tʜᴜᴍʙɴᴀɪʟs 🎥**\n"
    "➡️ **Sᴇʀɪᴇs/Sʜᴏᴡ Tʜᴜᴍʙɴᴀɪʟs 📺**\n"
    "➡️ **Cᴜsᴛᴏᴍ Dᴇsɪɢɴs ✨**\n\n"
    "☸️ **Hᴏᴡ Tᴏ Sᴛᴀʀᴛ ❔**\n\n"
    "➡️ **Sᴇʟᴇᴄᴛ ᴀ ᴄᴀᴛᴇɢᴏʀʏ ʙᴇʟᴏᴡ 🚨**\n"
    "➡️ **Sᴇɴᴅ ᴍᴇ ᴅᴇᴛᴀɪʟs & ᴡᴀᴛᴄʜ ᴛʜᴇ ᴍᴀɢɪᴄ 🚀**\n\n"
    "👇 **Pɪᴄᴋ ʏᴏᴜʀ ᴛʜᴜᴍʙɴᴀɪʟ ᴛʏᴘᴇ**"
)

DEFAULT_MOVIE_TEMPLATE = (
    "🎬 **Title** : **{title} {year}**\n\n"
    "🌐 **Language** : **{language}**\n\n"
    "📥 **Quality** : **{quality}**\n\n"
    "🌟 **Imdb** : **{imdb}**\n\n"
    "💢 **Genres** : **{genres}**"
)

DEFAULT_SERIES_TEMPLATE = (
    "📺 **Title** : **{title}**\n"
    "🌿 **Season** : **{season}** | 📂 **Episode** : **{episode}**\n\n"
    "🌐 **Language** : **{language}**\n"
    "📥 **Quality** : **{quality}**\n"
    "🌟 **IMDb** : **{imdb}**\n"
    "💢 **Genres** : **{genres}**"
)

DEFAULT_DATA = {
    "owner_id": OWNER_ID,
    "admins": [],            # list of admin user_ids (owner is always allowed too)
    "banned": [],            # list of banned user_ids
    "bot_status": "on",      # "on" / "off"
    "welcome_photo": None,   # file_id or None
    "welcome_text": DEFAULT_WELCOME_TEXT,
    "sticker_id": None,      # file_id or None
    "movie_template": DEFAULT_MOVIE_TEMPLATE,
    "series_template": DEFAULT_SERIES_TEMPLATE,
}


def _load():
    if not os.path.exists(DB_FILE):
        _save(DEFAULT_DATA)
        return dict(DEFAULT_DATA)
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # backfill any missing keys (e.g. after an update)
    for k, v in DEFAULT_DATA.items():
        data.setdefault(k, v)
    return data


def _save(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_settings():
    return _load()


# ---------------- owner / admin ----------------

def is_owner(user_id: int) -> bool:
    return user_id == _load()["owner_id"]


def is_admin(user_id: int) -> bool:
    data = _load()
    return user_id == data["owner_id"] or user_id in data["admins"]


def add_admin(user_id: int):
    data = _load()
    if user_id not in data["admins"]:
        data["admins"].append(user_id)
        _save(data)


def remove_admin(user_id: int):
    data = _load()
    if user_id in data["admins"]:
        data["admins"].remove(user_id)
        _save(data)


def list_admins():
    return _load()["admins"]


# ---------------- ban / unban ----------------

def is_banned(user_id: int) -> bool:
    return user_id in _load()["banned"]


def ban_user(user_id: int):
    data = _load()
    if user_id not in data["banned"]:
        data["banned"].append(user_id)
        _save(data)


def unban_user(user_id: int):
    data = _load()
    if user_id in data["banned"]:
        data["banned"].remove(user_id)
        _save(data)


def list_banned():
    return _load()["banned"]


# ---------------- bot status ----------------

def get_bot_status() -> str:
    return _load()["bot_status"]


def set_bot_status(status: str):
    data = _load()
    data["bot_status"] = status
    _save(data)


def toggle_bot_status() -> str:
    data = _load()
    data["bot_status"] = "off" if data["bot_status"] == "on" else "on"
    _save(data)
    return data["bot_status"]


# ---------------- welcome message ----------------

def get_welcome_photo():
    return _load()["welcome_photo"]


def set_welcome_photo(file_id: str):
    data = _load()
    data["welcome_photo"] = file_id
    _save(data)


def get_welcome_text() -> str:
    return _load()["welcome_text"]


def set_welcome_text(text: str):
    data = _load()
    data["welcome_text"] = text
    _save(data)


def reset_welcome_text():
    set_welcome_text(DEFAULT_WELCOME_TEXT)


# ---------------- sticker ----------------

def get_sticker():
    return _load()["sticker_id"]


def set_sticker(file_id: str):
    data = _load()
    data["sticker_id"] = file_id
    _save(data)


def remove_sticker():
    data = _load()
    data["sticker_id"] = None
    _save(data)


# ---------------- caption templates ----------------

def get_movie_template() -> str:
    return _load()["movie_template"]


def get_series_template() -> str:
    return _load()["series_template"]
