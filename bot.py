import logging
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
)

import config
import database as db
import tmdb_api
import omdb_api

logging.basicConfig(level=logging.INFO)

app = Client(
    "animebot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)

# ---- in-memory per-user session state ----
# SESSIONS[user_id] = {step, query, results, media_type, tmdb_id, title, year,
#                       details, source, images, image, season, episode, qualities}
SESSIONS = {}

QUALITY_OPTIONS = ["480p", "720p", "1080p", "2k", "4k"]


def reset(uid):
    SESSIONS.pop(uid, None)


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    reset(message.from_user.id)
    await message.reply_text(
        "✅ **Bot is Alive!**\n\n"
        "I'm an Anime/Movie poster + caption maker bot 🎬\n"
        "To start a new post, type `/new` followed by the name.\n\n"
        "Example: `/new Attack on Titan`",
        parse_mode=enums.ParseMode.MARKDOWN,
    )


# ---------------------------------------------------------------------------
# /new  -> search TMDb
# ---------------------------------------------------------------------------
@app.on_message(filters.command("new"))
async def new_cmd(client, message):
    uid = message.from_user.id
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        SESSIONS[uid] = {"step": "await_query"}
        await message.reply_text("📝 Type the anime/movie name:")
        return
    await do_search(message, parts[1])


async def do_search(message, query):
    uid = message.from_user.id
    try:
        results = tmdb_api.search_multi(query)
    except Exception:
        logging.exception("TMDb search failed")
        await message.reply_text("❌ TMDb search failed (check API key/network).")
        reset(uid)
        return
    if not results:
        await message.reply_text("❌ No results found. Try another name (`/new <name>`).")
        reset(uid)
        return

    SESSIONS[uid] = {"step": "await_pick_result", "results": results}

    buttons = []
    for i, r in enumerate(results):
        title = r.get("title") or r.get("name")
        year = (r.get("release_date") or r.get("first_air_date") or "----")[:4]
        buttons.append(
            [InlineKeyboardButton(f"{title} ({year})", callback_data=f"pick:{i}")]
        )

    await message.reply_text(
        f"🔎 Here are the matches for \"{query}\", select the correct one:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ---------------------------------------------------------------------------
# text handler -> feeds whichever step the user is currently on
# ---------------------------------------------------------------------------
@app.on_message(filters.text & filters.private & ~filters.command(["start", "new", "admin"]))
async def text_router(client, message):
    uid = message.from_user.id
    session = SESSIONS.get(uid)
    if not session:
        return

    step = session.get("step")

    if step == "await_query":
        await do_search(message, message.text)

    elif step == "await_title":
        session["title"] = message.text.strip()
        session["step"] = "await_season"
        await message.reply_text("🌿 Enter the season number (e.g. 1):")

    elif step == "await_season":
        if not message.text.strip().isdigit():
            await message.reply_text("⚠️ Please enter only the season number (e.g. 1)")
            return
        session["season"] = message.text.strip()
        session["step"] = "await_episode"
        await message.reply_text("📂 Enter the episode number (e.g. 5):")

    elif step == "await_episode":
        if not message.text.strip().isdigit():
            await message.reply_text("⚠️ Please enter only the episode number (e.g. 5)")
            return
        session["episode"] = message.text.strip()
        session["qualities"] = set()
        session["step"] = "await_quality"
        await message.reply_text(
            "📥 Select quality (you can select multiple), then press Done:",
            reply_markup=quality_keyboard(session["qualities"]),
        )

    elif step == "await_template" and db.is_admin(uid):
        db.set_template(message.text)
        reset(uid)
        await message.reply_text("✅ Caption template updated!")

    elif step == "await_add_admin" and db.is_owner(uid):
        if not message.text.strip().isdigit():
            await message.reply_text("⚠️ Please enter a numeric user id only.")
            return
        new_id = int(message.text.strip())
        db.add_admin(new_id)
        reset(uid)
        await message.reply_text(f"✅ `{new_id}` added as admin.", parse_mode=enums.ParseMode.MARKDOWN)


# ---------------------------------------------------------------------------
# quality multi-select keyboard
# ---------------------------------------------------------------------------
def quality_keyboard(selected):
    row = []
    for q in QUALITY_OPTIONS:
        label = f"✅ {q}" if q in selected else q
        row.append(InlineKeyboardButton(label, callback_data=f"q:{q}"))
    # 3 per row
    rows = [row[i:i + 3] for i in range(0, len(row), 3)]
    rows.append([InlineKeyboardButton("➡️ Done", callback_data="q:done")])
    return InlineKeyboardMarkup(rows)


# ---------------------------------------------------------------------------
# callback query handler
# ---------------------------------------------------------------------------
@app.on_callback_query()
async def callbacks(client, cq):
    uid = cq.from_user.id
    data = cq.data
    session = SESSIONS.get(uid, {})

    # session expired (e.g. bot restarted) -> ask user to start over instead of crashing
    if not session and not data.startswith("admin:"):
        await cq.answer("⚠️ Session expired, please send /new again.", show_alert=True)
        return

    # ---- pick search result ----
    if data.startswith("pick:"):
        idx = int(data.split(":")[1])
        result = session["results"][idx]
        media_type = result["media_type"]
        tmdb_id = result["id"]
        title = result.get("title") or result.get("name")
        year = (result.get("release_date") or result.get("first_air_date") or "----")[:4]

        try:
            details = tmdb_api.get_details(media_type, tmdb_id)
        except Exception:
            logging.exception("TMDb get_details failed")
            await cq.answer("❌ Failed to fetch TMDb details.", show_alert=True)
            return

        SESSIONS[uid] = {
            "step": "await_source",
            "media_type": media_type,
            "tmdb_id": tmdb_id,
            "title_guess": title,
            "year": year,
            "details": details,
        }

        await cq.message.edit_text(
            f"Selected: **{title} ({year})**\n\nWhere should the poster come from?",
            parse_mode=enums.ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("🎞 IMDb", callback_data="src:imdb"),
                    InlineKeyboardButton("🎬 TMDB", callback_data="src:tmdb"),
                ]]
            ),
        )
        await cq.answer()

    # ---- choose poster source ----
    elif data.startswith("src:"):
        source = data.split(":")[1]
        media_type = session["media_type"]
        tmdb_id = session["tmdb_id"]
        details = session["details"]

        await cq.answer("Loading images...")

        try:
            if source == "tmdb":
                images = tmdb_api.get_vertical_posters(media_type, tmdb_id)
                imdb_rating = details["tmdb_rating"]
            else:
                omdb_data = omdb_api.get_by_imdb_id(details.get("imdb_id"))
                images = [omdb_data["poster"]] if omdb_data and omdb_data.get("poster") else []
                imdb_rating = omdb_data["imdb_rating"] if omdb_data else "N/A"
        except Exception:
            logging.exception("Poster fetch failed")
            await cq.message.reply_text("❌ Failed to fetch poster (check API key/network).")
            return

        if not images:
            await cq.message.reply_text(
                "❌ No vertical images found for this source. Try the other source."
            )
            return

        session["source"] = source
        session["images"] = images
        session["imdb_rating"] = imdb_rating
        session["step"] = "await_image"

        # send as an album so the user can see every option
        media = [InputMediaPhoto(url) for url in images]
        if len(media) == 1:
            await cq.message.reply_photo(media[0].media)
        else:
            await cq.message.reply_media_group(media)

        buttons = [
            InlineKeyboardButton(str(i + 1), callback_data=f"img:{i}")
            for i in range(len(images))
        ]
        rows = [buttons[i:i + 4] for i in range(0, len(buttons), 4)]
        await cq.message.reply_text(
            "👆 Press the number button matching the image you want:",
            reply_markup=InlineKeyboardMarkup(rows),
        )

    # ---- choose the actual image ----
    elif data.startswith("img:"):
        idx = int(data.split(":")[1])
        session["image"] = session["images"][idx]
        session["step"] = "await_title"
        await cq.message.edit_text("✅ Image selected!")
        await cq.message.reply_text("🎬 Enter the title (name only):")
        await cq.answer()

    # ---- quality multi select ----
    elif data.startswith("q:"):
        choice = data.split(":")[1]
        if choice == "done":
            if not session.get("qualities"):
                await cq.answer("Please select at least one quality!", show_alert=True)
                return
            await finalize_post(client, cq, session)
        else:
            quals = session.setdefault("qualities", set())
            if choice in quals:
                quals.remove(choice)
            else:
                quals.add(choice)
            await cq.message.edit_reply_markup(quality_keyboard(quals))
            await cq.answer()

    # ---- admin panel ----
    elif data.startswith("admin:"):
        await handle_admin_callback(client, cq, data)


# ---------------------------------------------------------------------------
# final caption build + send
# ---------------------------------------------------------------------------
async def finalize_post(client, cq, session):
    details = session["details"]
    quality_str = ", ".join(sorted(session["qualities"], key=QUALITY_OPTIONS.index))

    caption = db.get_template().format(
        title=session.get("title", session.get("title_guess", "N/A")),
        season=session.get("season", "N/A"),
        episode=session.get("episode", "N/A"),
        language=details.get("language", "N/A"),
        quality=quality_str,
        imdb=session.get("imdb_rating", "N/A"),
        genres=details.get("genres", "N/A"),
    )

    await client.send_photo(
        cq.message.chat.id,
        photo=session["image"],
        caption=caption,
        parse_mode=enums.ParseMode.MARKDOWN,
    )
    await cq.message.delete()
    await cq.answer("Post ready! 🎉")
    reset(cq.from_user.id)


# ---------------------------------------------------------------------------
# /admin panel
# ---------------------------------------------------------------------------
@app.on_message(filters.command("admin"))
async def admin_cmd(client, message):
    uid = message.from_user.id
    if not db.is_admin(uid):
        await message.reply_text("⛔ You don't have access.")
        return

    buttons = [
        [InlineKeyboardButton("📝 Edit Caption Template", callback_data="admin:edit_template")],
        [InlineKeyboardButton("🔄 Reset Template to Default", callback_data="admin:reset_template")],
        [InlineKeyboardButton("👥 List Admins", callback_data="admin:list")],
    ]
    if db.is_owner(uid):
        buttons.append([InlineKeyboardButton("➕ Add Admin", callback_data="admin:add")])
        buttons.append([InlineKeyboardButton("➖ Remove Admin", callback_data="admin:remove")])

    await message.reply_text(
        "🛠 **Admin Portal**\nSelect an option:",
        parse_mode=enums.ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def handle_admin_callback(client, cq, data):
    uid = cq.from_user.id
    action = data.split(":")[1]

    if not db.is_admin(uid):
        await cq.answer("⛔ Access denied.", show_alert=True)
        return

    if action == "edit_template":
        SESSIONS[uid] = {"step": "await_template"}
        placeholders = "{title} {season} {episode} {language} {quality} {imdb} {genres}"
        await cq.message.reply_text(
            "✏️ Send the new template. You can use these placeholders:\n"
            f"`{placeholders}`\n\n"
            "Current template:\n\n" + db.get_template(),
            parse_mode=enums.ParseMode.MARKDOWN,
        )
        await cq.answer()

    elif action == "reset_template":
        db.reset_template()
        await cq.message.reply_text("✅ Reset to default template.")
        await cq.answer()

    elif action == "list":
        settings = db.get_settings()
        text = f"👑 Owner: `{settings['owner_id']}`\n"
        if settings["admins"]:
            text += "🛡 Admins:\n" + "\n".join(f"- `{a}`" for a in settings["admins"])
        else:
            text += "🛡 Admins: (none)"
        await cq.message.reply_text(text, parse_mode=enums.ParseMode.MARKDOWN)
        await cq.answer()

    elif action == "add":
        if not db.is_owner(uid):
            await cq.answer("⛔ Only the owner can add admins.", show_alert=True)
            return
        SESSIONS[uid] = {"step": "await_add_admin"}
        await cq.message.reply_text("➕ Send the Telegram ID of the user to add:")
        await cq.answer()

    elif action == "remove":
        if not db.is_owner(uid):
            await cq.answer("⛔ Only the owner can remove admins.", show_alert=True)
            return
        settings = db.get_settings()
        if not settings["admins"]:
            await cq.message.reply_text("Admin list is empty.")
            await cq.answer()
            return
        buttons = [
            [InlineKeyboardButton(str(a), callback_data=f"admin:rm:{a}")]
            for a in settings["admins"]
        ]
        await cq.message.reply_text(
            "Who do you want to remove?", reply_markup=InlineKeyboardMarkup(buttons)
        )
        await cq.answer()

    elif action.startswith("rm"):
        # data looks like admin:rm:<id>
        target_id = int(data.split(":")[2])
        db.remove_admin(target_id)
        await cq.message.reply_text(f"✅ `{target_id}` removed.", parse_mode=enums.ParseMode.MARKDOWN)
        await cq.answer()


if __name__ == "__main__":
    print("Bot starting...")
    app.run()
        
