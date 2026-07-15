import json
import os
from config import OWNER_ID

DB_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_TEMPLATE = (
    "🎬 **Title** : {title}\n"
    "🌿 **Season** : {season} | 📂 **Episode** {episode}\n\n"
    "🌐 **Language** : {language}\n"
    "📥 **Quality** : {quality}\n"
    "🌟 **Imdb** : {imdb}\n"
    "⭕ **Genres** : {genres}"
)

DEFAULT_DATA = {
    "owner_id": OWNER_ID,
    "admins": [],          # list of admin user_ids (owner is always allowed too)
    "caption_template": DEFAULT_TEMPLATE,
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


def get_template() -> str:
    return _load()["caption_template"]


def set_template(template: str):
    data = _load()
    data["caption_template"] = template
    _save(data)


def reset_template():
    set_template(DEFAULT_TEMPLATE)
