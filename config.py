import os

# ============================================================
# Bot Config — No .env file needed.
#
# ⚠️ SECURITY: Do NOT commit real secrets in this file to a public
# GitHub repo. Prefer setting them as Environment Variables in your
# hosting platform's dashboard (Railway -> Variables tab). This file
# will use the platform's env vars automatically if they're set,
# and only falls back to the values below if they're not.
# ============================================================

def _get(name, default=""):
    val = os.environ.get(name)
    return val if val else default


# Get this from my.telegram.org (API development tools)
API_ID = int(_get("API_ID", "0") or "0")

# Get this from my.telegram.org
API_HASH = _get("API_HASH", "")

# Get this from @BotFather -> /newbot
BOT_TOKEN = _get("BOT_TOKEN", "")

# https://www.themoviedb.org/settings/api -> free account
TMDB_API_KEY = _get("TMDB_API_KEY", "")

# https://www.omdbapi.com/apikey.aspx -> free
# IMPORTANT: only the key itself goes here, NOT the full URL.
# Wrong:   http://www.omdbapi.com/?i=tt3896198&apikey=xxxxxxxx
# Correct: xxxxxxxx
OMDB_API_KEY = _get("OMDB_API_KEY", "")

# Your own Telegram numeric user id (owner = full control)
# DM @userinfobot to get your ID
OWNER_ID = int(_get("OWNER_ID", "0") or "0")

# ---- optional: used for the /start welcome message buttons ----
# Leave as "" if you don't want a particular button to show.
OWNER_USERNAME = _get("OWNER_USERNAME", "")   # e.g. "yourusername" (no @)
SUPPORT_LINK = _get("SUPPORT_LINK", "")       # e.g. "https://t.me/yoursupportgroup"
WEBSITE_LINK = _get("WEBSITE_LINK", "")       # e.g. "https://yourwebsite.com"

# ---- don't touch anything below this line ----
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

_required = {
    "API_ID": API_ID,
    "API_HASH": API_HASH,
    "BOT_TOKEN": BOT_TOKEN,
    "TMDB_API_KEY": TMDB_API_KEY,
    "OMDB_API_KEY": OMDB_API_KEY,
    "OWNER_ID": OWNER_ID,
}
_missing = [name for name, val in _required.items() if not val]

if _missing:
    raise SystemExit(
        f"\n❌ Missing/empty: {', '.join(_missing)}\n"
        "Set them as Environment Variables in your hosting platform's "
        "dashboard, or fill them in directly below in config.py, then restart.\n"
    )

if "apikey=" in OMDB_API_KEY or OMDB_API_KEY.startswith("http"):
    raise SystemExit(
        "\n❌ OMDB_API_KEY looks like a full URL, not a key.\n"
        "Only put the key itself, e.g. OMDB_API_KEY = \"6c5fce1b\"\n"
    )
    
