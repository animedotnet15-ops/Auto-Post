import os

# ============================================================
# Bot Config — No .env file needed.
#
# Two ways to set your keys, both work without a .env file:
#
# 1) Hosting platform (Railway / Render / Koyeb / etc.):
#    Set these as Environment Variables in the platform's dashboard.
#    They will be picked up automatically.
#
# 2) Running locally:
#    Just fill in the values directly below.
# ============================================================

def _get(name, default=""):
    return os.environ.get(name, default)


# Get this from my.telegram.org (API development tools)
API_ID = int(_get("API_ID", "0"))          # e.g. 1234567
API_HASH = _get("API_HASH", "")             # e.g. "abcd1234efgh5678"

# Get this from @BotFather -> /newbot
BOT_TOKEN = _get("BOT_TOKEN", "")

# https://www.themoviedb.org/settings/api -> free account
TMDB_API_KEY = _get("TMDB_API_KEY", "")

# https://www.omdbapi.com/apikey.aspx -> free (for IMDb data)
OMDB_API_KEY = _get("OMDB_API_KEY", "")

# Your own Telegram numeric user id (owner = full control)
# DM @userinfobot to get your ID
OWNER_ID = int(_get("OWNER_ID", "0"))

# ---- don't touch anything below this line ----
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

if not all([API_ID, API_HASH, BOT_TOKEN, TMDB_API_KEY, OMDB_API_KEY, OWNER_ID]):
    raise SystemExit(
        "\n❌ One or more of API_ID / API_HASH / BOT_TOKEN / TMDB_API_KEY / "
        "OMDB_API_KEY / OWNER_ID is missing.\n"
        "Either set them as Environment Variables in your hosting platform's "
        "dashboard, or fill them in directly in config.py, then restart the bot.\n"
    )
    
