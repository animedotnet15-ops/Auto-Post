# Anime/Movie Caption Bot

TMDb / IMDb (via OMDb) poster + auto-formatted caption maker Telegram bot.

## 1. Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

| Variable | Where to get it |
|---|---|
| `API_ID`, `API_HASH` | https://my.telegram.org → API development tools |
| `BOT_TOKEN` | Talk to [@BotFather](https://t.me/BotFather) → `/newbot` |
| `TMDB_API_KEY` | https://www.themoviedb.org/settings/api (free) |
| `OMDB_API_KEY` | https://www.omdbapi.com/apikey.aspx (free, 1000 req/day) |
| `OWNER_ID` | Your own Telegram numeric ID — DM [@userinfobot](https://t.me/userinfobot) |

## 2. Run

```bash
python bot.py
```

## 3. How it works (matches the flow you asked for)

1. `/start` → bot replies "Bot is Alive" ✅
2. `/new <anime or movie name>` (or just `/new`, bot will then ask for the name)
3. Bot searches TMDb and shows the matching titles → tap the correct one
4. Bot shows two buttons: **IMDb** / **TMDB** — pick where the poster comes from
5. Bot sends all available **vertical poster images** as an album, then number
   buttons under it → tap the number of the image you want
6. Bot asks step by step:
   - Title (name only)
   - Season (number only)
   - Episode (number only)
   - Quality → multiple choice buttons (480p / 720p / 1080p / 2k / 4k), tick as
     many as you want, then **Done**
7. Bot sends the final photo with the **bold** formatted caption:

```
🎬 Title : {title}
🌿 Season : {season} | 📂 Episode {episode}

🌐 Language : {language}
📥 Quality : {quality}
🌟 Imdb : {imdb rating}
⭕ Genres : {genres}
```

`Language`, `Imdb rating`, and `Genres` are pulled automatically from
TMDb/OMDb — you don't have to type them.

## 4. Admin Portal

`/admin` — only visible to the **owner** (from `.env`) and any admins the
owner has added.

- **Edit Caption Template** — send a new template using placeholders:
  `{title} {season} {episode} {language} {quality} {imdb} {genres}`
  This changes the output format for everyone using the bot.
- **Reset Template to Default**
- **List Admins**
- **Add / Remove Admin** — owner only

Settings (owner id, admin list, current template) are stored in
`settings.json`, created automatically on first run.

## 5. Important limitation to know

IMDb has no free public API for multiple poster sizes. The **IMDb** button
uses OMDb (`omdb_api.py`), which only returns **one** poster per title. The
**TMDB** button gives you the full gallery of vertical posters. If you later
get access to a paid IMDb image API, just swap the logic inside
`omdb_api.py`.

## 6. Files

- `bot.py` — all bot logic (Pyrogram)
- `config.py` — reads `.env`
- `database.py` — JSON-based settings/admin store
- `tmdb_api.py` — TMDb search/images/details
- `omdb_api.py` — IMDb poster + rating via OMDb
- `settings.json` — auto-created, holds owner/admins/template
- 
