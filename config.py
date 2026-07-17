# ============================================================
# Bot Config — No .env file needed. Fill your keys directly below.
# ============================================================

# Get this from my.telegram.org (API development tools)
API_ID = 0          # e.g. 1234567 (number, no quotes)
API_HASH = ""        # e.g. "abcd1234efgh5678"

# Get this from @BotFather -> /newbot
BOT_TOKEN = ""

# https://www.themoviedb.org/settings/api -> free account
TMDB_API_KEY = ""

# https://www.omdbapi.com/apikey.aspx -> free (for IMDb data)
OMDB_API_KEY = ""

# Your own Telegram numeric user id (owner = full control)
# DM @userinfobot to get your ID
OWNER_ID = 0

# ---- don't touch anything below this line ----
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

if not all([API_ID, API_HASH, BOT_TOKEN, TMDB_API_KEY, OMDB_API_KEY, OWNER_ID]):
    raise SystemExit(
        "\n❌ One or more of API_ID / API_HASH / BOT_TOKEN / TMDB_API_KEY / "
        "OMDB_API_KEY / OWNER_ID is missing in config.py.\n"
        "Open config.py, fill in the values, then restart the bot.\n"
    )
  
