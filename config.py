import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
OMDB_API_KEY = os.environ.get("OMDB_API_KEY", "")

# First person who deployed the bot -> full control (add/remove admins, edit template)
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
