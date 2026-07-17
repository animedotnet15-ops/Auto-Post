# Anime/Movie/Series Thumbnail Caption Bot

TMDb / IMDb (via OMDb) poster + auto-formatted caption maker Telegram bot,
with separate Movie and Series flows, custom descriptions, admin settings,
ban/unban, and a start animation.

## 1. Setup

```bash
pip install -r requirements.txt
```

Open `config.py` and fill in your values directly in the file, or set them
as Environment Variables in your hosting platform (Railway/Render/etc.) —
no `.env` file needed either way.

| Variable | Where to get it |
|---|---|
| `API_ID`, `API_HASH` | https://my.telegram.org → API development tools |
| `BOT_TOKEN` | Talk to [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TMDB_API_KEY` | https://www.themoviedb.org/settings/api (free) |
| `OMDB_API_KEY` | https://www.omdbapi.com/apikey.aspx (free, only the key, not the full URL) |
| `OWNER_ID` | Your own Telegram numeric ID — DM [@userinfobot](https://t.me/userinfobot) |
| `OWNER_USERNAME` (optional) | Your @username, shown as the "Owner" button on `/start` |
| `SUPPORT_LINK` (optional) | Support group/channel link, shown as "Support" button |
| `WEBSITE_LINK` (optional) | Website link, shown as "Website" button |

**Build Command:** `pip install -r requirements.txt`
**Start Command:** `python bot.py`

## 2. Run

```bash
python bot.py
```

## 3. User flow

1. `/start` → animated "Start... Starting... Started..." sequence, optional
   sticker, then the welcome message (photo + text + buttons).
2. `/new` (optionally `/new <name>`) → choose **🎬 Movie** or **📺 Series**.
3. Type the name → bot searches TMDb and shows matching titles → tap the
   correct one.
4. Choose poster source: **IMDb** or **TMDB**.
5. Bot shows only **vertical (portrait) poster images** as an album, with
   number buttons underneath → tap the one you want.
6. Choose **🤖 Auto Description** or **✍️ Custom Description**:
   - **Custom** — just type your own caption/HTML, bot posts it as-is with
     the selected image.
   - **Auto** — bot walks you through:
     - **Movie:** Title → Language (multi-select) → Quality (multi-select)
     - **Series:** Title → Year (optional, or Skip) → Season → Episode →
       Language (multi-select) → Quality (multi-select)
7. Bot sends the final photo with a **bold** formatted caption. IMDb rating
   and Genres are pulled automatically from TMDb/OMDb.

## 4. Admin & Owner Commands

| Command | Access | Description |
|---|---|---|
| `/setting` | Admin | Toggle bot ON/OFF, edit welcome photo/text |
| `/addadmin <id or @username>` | Owner | Add an admin |
| `/removeadmin <id or @username>` | Owner | Remove an admin |
| `/adminlist` | Owner | List all admins |
| `/ban <id or @username>` | Admin | Ban a user from using the bot |
| `/unban <id or @username>` | Admin | Unban a user |
| `/setsticker` (reply to a sticker) | Admin | Set the `/start` animation sticker |
| `/removesticker` | Admin | Remove the start-animation sticker |
| `/help` | Everyone | Show command help |

Settings (owner id, admins, banned users, bot status, welcome message,
sticker, templates) are stored in `settings.json`, created automatically on
first run.

## 5. Important limitation to know

- IMDb has no free public API for multiple poster sizes. The **IMDb**
  button uses OMDb (`omdb_api.py`), which only returns **one** poster per
  title. The **TMDB** button gives you the full gallery of vertical
  posters.
- Telegram's Bot API does not support custom-colored inline buttons — all
  buttons use Telegram's default styling.

## 6. Files

- `bot.py` — all bot logic (Pyrogram)
- `config.py` — your API keys/tokens/links go here (or use env vars)
- `database.py` — JSON-based settings/admin/ban/welcome/sticker store
- `tmdb_api.py` — TMDb search/images/details
- `omdb_api.py` — IMDb poster + rating via OMDb
- `settings.json` — auto-created on first run
- 
