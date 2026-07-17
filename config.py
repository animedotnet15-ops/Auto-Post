# ============================================================
# Bot Config — No .env file needed. Fill your keys directly below.
# ============================================================

# Get this from my.telegram.org (API development tools)
API_ID = 38484181         # e.g. 1234567 (number, no quotes)
API_HASH = "004516cc7835d8a332e1cb5717393ff3"        # e.g. "abcd1234efgh5678"

# Get this from @BotFather -> /newbot
BOT_TOKEN = "8968039109:AAEq0Swe6qc3cBEoN17cpggqHz40JxqE9-k"

# https://www.themoviedb.org/settings/api -> free account
TMDB_API_KEY = "ca38bb741c5b47dc78a7e3189daf22fb"

# https://www.omdbapi.com/apikey.aspx -> free (for IMDb data)
OMDB_API_KEY = "http://www.omdbapi.com/?i=tt3896198&apikey=6c5fce1b"

# Your own Telegram numeric user id (owner = full control)
# DM @userinfobot to get your ID
OWNER_ID = 8337976117

# ---- don't touch anything below this line ----
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

if not all([API_ID, API_HASH, BOT_TOKEN, TMDB_API_KEY, OMDB_API_KEY, OWNER_ID]):
    raise SystemExit(
        "\n❌ One or more of API_ID / API_HASH / BOT_TOKEN / TMDB_API_KEY / "
        "OMDB_API_KEY / OWNER_ID is missing in config.py.\n"
        "Open config.py, fill in the values, then restart the bot.\n"
    )
  
