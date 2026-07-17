import asyncio
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
SESSIONS = {}

QUALITY_OPTIONS = ["480p", "720p", "1080p", "2k", "4k"]
LANGUAGE_OPTIONS = ["Tamil", "Hindi", "Telugu", "English", "Japanese"]

HELP_TEXT = (
    "📖 **Hᴇʟᴘ — Hᴏᴡ Tᴏ Usᴇ Tʜɪs Bᴏᴛ**\n\n"
    "**/start** — show the welcome message\n"
    "**/new** — create a new Movie/Series thumbnail post\n"
    "**/help** — show this help message\n\n"
    "**Admin/Owner only:**\n"
    "**/setting** — bot status + welcome message settings\n"
    "**/addadmin** `<id or @username>` — add an admin (owner only)\n"
    "**/removeadmin** `<id or @username>` — remove an admin (owner only)\n"
    "**/adminlist** — list all admins (owner only)\n"
    "**/ban** `<id or @username>` — ban a user\n"
    "**/unban** `<id or @username>` — unban a user\n"
    "**/setsticker** — reply to a sticker to set the start-animation sticker\n"
    "**/removesticker** — remove the start-animation sticker"
)


def reset(uid):
    SESSIONS.pop(uid, None)


async def resolve_user_id(client, arg: str):
    """Resolve a command argument (numeric id or @username) to a user id."""
    arg = arg.strip()
    if arg.startswith("@"):
        arg = arg[1:]
    if arg.isdigit():
        return int(arg)
    try:
        user = await client.get_users(arg)
        return user.id
    except Exception:
        return None


# =============================================================================
# /start
# =============================================================================
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    uid = message.from_user.id
    reset(uid)

    if db.is_banned(uid):
        await message.reply_text("🚫 You are banned from using this bot.")
        return

    if db.get_bot_status() == "off" and not db.is_admin(uid):
        await message.reply_text("🔴 Bot is currently under maintenance. Please try again later.")
        return

    name = message.from_user.first_name or "there"
    status_msg = await message.reply_text(f"Hᴇʏ {name} 👋 Sᴛᴀʀᴛ...")
    await asyncio.sleep(1)
    await status_msg.edit_text("Sᴛᴀʀᴛɪɴɢ...")
    await asyncio.sleep(1)
    await status_msg.edit_text("Sᴛᴀʀᴛᴇᴅ ...")
    await asyncio.sleep(1)

    sticker_id = db.get_sticker()
    if sticker_id:
        try:
            sticker_msg = await message.reply_sticker(sticker_id)
            await asyncio.sleep(3)
            await sticker_msg.delete()
        except Exception:
            logging.exception("Failed to send/delete start sticker")

    try:
        await status_msg.delete()
    except Exception:
        pass

    buttons = []
    row1 = []
    if config.OWNER_USERNAME:
        row1.append(InlineKeyboardButton("👑 Owner", url=f"https://t.me/{config.OWNER_USERNAME}"))
    if config.SUPPORT_LINK:
        row1.append(InlineKeyboardButton("‼️ Support", url=config.SUPPORT_LINK))
    if row1:
        buttons.append(row1)
    row2 = []
    if config.WEBSITE_LINK:
        row2.append(InlineKeyboardButton("🌐 Website", url=config.WEBSITE_LINK))
    row2.append(InlineKeyboardButton("📖 Help", callback_data="help:show"))
    buttons.append(row2)

    welcome_text = db.get_welcome_text()
    welcome_photo = db.get_welcome_photo()
    markup = InlineKeyboardMarkup(buttons)

    if welcome_photo:
        await message.reply_photo(welcome_photo, caption=welcome_text, reply_markup=markup, parse_mode=enums.ParseMode.MARKDOWN)
    else:
        await message.reply_text(welcome_text, reply_markup=markup, parse_mode=enums.ParseMode.MARKDOWN)


# =============================================================================
# /help
# =============================================================================
@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    await message.reply_text(HELP_TEXT, parse_mode=enums.ParseMode.MARKDOWN)


# =============================================================================
# /new -> choose Movie / Series
# =============================================================================
@app.on_message(filters.command("new"))
async def new_cmd(client, message):
    uid = message.from_user.id
    if db.is_banned(uid):
        await message.reply_text("🚫 You are banned from using this bot.")
        return
    if db.get_bot_status() == "off" and not db.is_admin(uid):
        await message.reply_text("🔴 Bot is currently under maintenance. Please try again later.")
        return

    parts = message.text.split(None, 1)
    pending_query = parts[1] if len(parts) > 1 else None

    SESSIONS[uid] = {"step": "await_kind", "pending_query": pending_query}
    await message.reply_text(
        "👇 Select the type:",
        reply_markup=InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("🎬 Movie", callback_data="kind:movie"),
                InlineKeyboardButton("📺 Series", callback_data="kind:series"),
            ]]
        ),
    )


async def do_search(message, uid, query):
    session = SESSIONS.get(uid, {})
    kind = session.get("media_kind", "movie")
    tmdb_type = "movie" if kind == "movie" else "tv"

    try:
        results = tmdb_api.search_multi(query)
    except Exception:
        logging.exception("TMDb search failed")
        await message.reply_text("❌ TMDb search failed (check API key/network).")
        reset(uid)
        return

    results = [r for r in results if r.get("media_type") == tmdb_type]
    if not results:
        await message.reply_text("❌ No results found. Try another name (`/new <name>`).")
        reset(uid)
        return

    session["step"] = "await_pick_result"
    session["results"] = results

    buttons = []
    for i, r in enumerate(results):
        title = r.get("title") or r.get("name")
        year = (r.get("release_date") or r.get("first_air_date") or "----")[:4]
        buttons.append([InlineKeyboardButton(f"{title} ({year})", callback_data=f"pick:{i}")])

    await message.reply_text(
        f"🔎 Here are the matches for \"{query}\", select the correct one:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# =============================================================================
# text handler -> feeds whichever step the user is currently on
# =============================================================================
@app.on_message(filters.text & filters.private & ~filters.command(
    ["start", "new", "help", "setting", "addadmin", "removeadmin", "adminlist",
     "ban", "unban", "setsticker", "removesticker"]
))
async def text_router(client, message):
    uid = message.from_user.id
    session = SESSIONS.get(uid)
    if not session:
        return

    step = session.get("step")

    if step == "await_query":
        await do_search(message, uid, message.text)

    elif step == "await_custom_desc":
        await finalize_post(client, message, session, custom_text=message.text)

    elif step == "await_title":
        session["title"] = message.text.strip()
        if session["media_kind"] == "series":
            session["step"] = "await_year"
            await message.reply_text(
                "📅 Enter the year (optional):",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⛷️ Skip", callback_data="year:skip")]]
                ),
            )
        else:
            session["languages"] = set()
            session["step"] = "await_language"
            await message.reply_text(
                "🌐 Select language(s), then press Done:",
                reply_markup=language_keyboard(session["languages"]),
            )

    elif step == "await_year":
        session["year"] = message.text.strip()
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
        session["languages"] = set()
        session["step"] = "await_language"
        await message.reply_text(
            "🌐 Select language(s), then press Done:",
            reply_markup=language_keyboard(session["languages"]),
        )

    elif step == "await_welcome_text" and db.is_admin(uid):
        db.set_welcome_text(message.text)
        reset(uid)
        await message.reply_text("✅ Welcome text updated!")

    elif step == "await_add_admin" and db.is_owner(uid):
        target_id = await resolve_user_id(client, message.text)
        if not target_id:
            await message.reply_text("⚠️ Couldn't resolve that user. Send a numeric id or @username.")
            return
        db.add_admin(target_id)
        reset(uid)
        await message.reply_text(f"✅ `{target_id}` added as admin.", parse_mode=enums.ParseMode.MARKDOWN)


# =============================================================================
# photo handler -> used for /setting welcome photo upload
# =============================================================================
@app.on_message(filters.photo & filters.private)
async def photo_router(client, message):
    uid = message.from_user.id
    session = SESSIONS.get(uid)
    if not session or session.get("step") != "await_welcome_photo" or not db.is_admin(uid):
        return
    file_id = message.photo.file_id
    db.set_welcome_photo(file_id)
    reset(uid)
    await message.reply_text("✅ Welcome photo updated!")


# =============================================================================
# multi-select keyboards
# =============================================================================
def quality_keyboard(selected):
    row = [InlineKeyboardButton(f"✅ {q}" if q in selected else q, callback_data=f"q:{q}") for q in QUALITY_OPTIONS]
    rows = [row[i:i + 3] for i in range(0, len(row), 3)]
    rows.append([InlineKeyboardButton("➡️ Done", callback_data="q:done")])
    return InlineKeyboardMarkup(rows)


def language_keyboard(selected):
    row = [InlineKeyboardButton(f"✅ {l}" if l in selected else l, callback_data=f"lang:{l}") for l in LANGUAGE_OPTIONS]
    rows = [row[i:i + 2] for i in range(0, len(row), 2)]
    rows.append([InlineKeyboardButton("➡️ Done", callback_data="lang:done")])
    return InlineKeyboardMarkup(rows)


# =============================================================================
# callback query handler
# =============================================================================
@app.on_callback_query()
async def callbacks(client, cq):
    uid = cq.from_user.id
    data = cq.data
    session = SESSIONS.get(uid, {})

    if data == "help:show":
        await cq.message.reply_text(HELP_TEXT, parse_mode=enums.ParseMode.MARKDOWN)
        await cq.answer()
        return

    if not session and not data.startswith(("admin:", "cfg:")):
        await cq.answer("⚠️ Session expired, please send /new again.", show_alert=True)
        return

    # ---- movie / series ----
    if data.startswith("kind:"):
        kind = data.split(":")[1]
        session["media_kind"] = kind
        pending_query = session.get("pending_query")
        if pending_query:
            session["step"] = "await_pick_result"
            await cq.message.edit_text(f"🔎 Searching \"{pending_query}\"...")
            await do_search(cq.message, uid, pending_query)
        else:
            session["step"] = "await_query"
            label = "movie" if kind == "movie" else "series"
            await cq.message.edit_text(f"📝 Type the {label} name:")
        await cq.answer()

    # ---- pick search result ----
    elif data.startswith("pick:"):
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

        session.update({
            "step": "await_source",
            "media_type": media_type,
            "tmdb_id": tmdb_id,
            "title_guess": title,
            "year": year,
            "details": details,
        })

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
            await cq.message.reply_text("❌ No vertical images found for this source. Try the other source.")
            return

        session["source"] = source
        session["images"] = images
        session["imdb_rating"] = imdb_rating
        session["step"] = "await_image"

        media = [InputMediaPhoto(url) for url in images]
        if len(media) == 1:
            await cq.message.reply_photo(media[0].media)
        else:
            await cq.message.reply_media_group(media)

        buttons = [InlineKeyboardButton(str(i + 1), callback_data=f"img:{i}") for i in range(len(images))]
        rows = [buttons[i:i + 4] for i in range(0, len(buttons), 4)]
        await cq.message.reply_text(
            "👆 Press the number button matching the vertical image you want:",
            reply_markup=InlineKeyboardMarkup(rows),
        )

    # ---- choose the actual image ----
    elif data.startswith("img:"):
        idx = int(data.split(":")[1])
        session["image"] = session["images"][idx]
        session["step"] = "await_desc_mode"
        await cq.message.edit_text("✅ Image selected!")
        await cq.message.reply_text(
            "✏️ Description type?",
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("🤖 Auto Description", callback_data="desc:auto"),
                    InlineKeyboardButton("✍️ Custom Description", callback_data="desc:custom"),
                ]]
            ),
        )
        await cq.answer()

    # ---- description mode ----
    elif data.startswith("desc:"):
        mode = data.split(":")[1]
        if mode == "custom":
            session["step"] = "await_custom_desc"
            await cq.message.edit_text("✍️ Send the custom description/caption now (HTML/markdown allowed):")
        else:
            session["step"] = "await_title"
            label = "🎬 Enter the title (name only):" if session["media_kind"] == "movie" else "📺 Enter the title (name only):"
            await cq.message.edit_text(label)
        await cq.answer()

    # ---- year skip (series) ----
    elif data == "year:skip":
        session["year"] = ""
        session["step"] = "await_season"
        await cq.message.edit_text("🌿 Enter the season number (e.g. 1):")
        await cq.answer()

    # ---- language multi select ----
    elif data.startswith("lang:"):
        choice = data.split(":")[1]
        if choice == "done":
            if not session.get("languages"):
                await cq.answer("Please select at least one language!", show_alert=True)
                return
            session["qualities"] = set()
            session["step"] = "await_quality"
            await cq.message.edit_text(
                "📥 Select quality(s), then press Done:",
                reply_markup=quality_keyboard(session["qualities"]),
            )
            await cq.answer()
        else:
            langs = session.setdefault("languages", set())
            if choice in langs:
                langs.remove(choice)
            else:
                langs.add(choice)
            await cq.message.edit_reply_markup(language_keyboard(langs))
            await cq.answer()

    # ---- quality multi select ----
    elif data.startswith("q:"):
        choice = data.split(":")[1]
        if choice == "done":
            if not session.get("qualities"):
                await cq.answer("Please select at least one quality!", show_alert=True)
                return
            await finalize_post(client, cq.message, session)
            await cq.answer()
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

    # ---- settings panel ----
    elif data.startswith("cfg:"):
        await handle_settings_callback(client, cq, data)


# =============================================================================
# final caption build + send
# =============================================================================
async def finalize_post(client, message_or_cq_msg, session, custom_text=None):
    uid = None
    chat_id = message_or_cq_msg.chat.id
    image = session.get("image")

    if custom_text is not None:
        caption = custom_text
    elif session["media_kind"] == "movie":
        details = session["details"]
        quality_str = ", ".join(sorted(session["qualities"], key=QUALITY_OPTIONS.index))
        language_str = ", ".join(sorted(session["languages"], key=LANGUAGE_OPTIONS.index))
        caption = db.get_movie_template().format(
            title=session.get("title", session.get("title_guess", "N/A")),
            year=session.get("year", ""),
            language=language_str,
            quality=quality_str,
            imdb=session.get("imdb_rating", "N/A"),
            genres=details.get("genres", "N/A"),
        )
    else:
        details = session["details"]
        quality_str = ", ".join(sorted(session["qualities"], key=QUALITY_OPTIONS.index))
        language_str = ", ".join(sorted(session["languages"], key=LANGUAGE_OPTIONS.index))
        caption = db.get_series_template().format(
            title=session.get("title", session.get("title_guess", "N/A")),
            season=session.get("season", "N/A"),
            episode=session.get("episode", "N/A"),
            language=language_str,
            quality=quality_str,
            imdb=session.get("imdb_rating", "N/A"),
            genres=details.get("genres", "N/A"),
        )

    await client.send_photo(
        chat_id,
        photo=image,
        caption=caption,
        parse_mode=enums.ParseMode.MARKDOWN,
    )
    await message_or_cq_msg.reply_text("Post ready! 🎉")

    # find the session owner to reset (works for both message.reply and cq.message paths)
    for user_id, s in list(SESSIONS.items()):
        if s is session:
            reset(user_id)
            break


# =============================================================================
# /setting (admin) — bot status + welcome message
# =============================================================================
@app.on_message(filters.command("setting"))
async def setting_cmd(client, message):
    uid = message.from_user.id
    if not db.is_admin(uid):
        await message.reply_text("⛔ You don't have access.")
        return

    status = db.get_bot_status()
    status_label = "🟢 ON" if status == "on" else "🔴 OFF"

    buttons = [
        [InlineKeyboardButton(f"⚙️ Bot Status: {status_label}", callback_data="cfg:toggle_status")],
        [InlineKeyboardButton("👋 Welcome Message", callback_data="cfg:welcome_menu")],
    ]
    await message.reply_text(
        "🛠 **Settings**",
        parse_mode=enums.ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def handle_settings_callback(client, cq, data):
    uid = cq.from_user.id
    if not db.is_admin(uid):
        await cq.answer("⛔ Access denied.", show_alert=True)
        return

    action = data.split(":")[1]

    if action == "toggle_status":
        new_status = db.toggle_bot_status()
        status_label = "🟢 ON" if new_status == "on" else "🔴 OFF"
        buttons = [
            [InlineKeyboardButton(f"⚙️ Bot Status: {status_label}", callback_data="cfg:toggle_status")],
            [InlineKeyboardButton("👋 Welcome Message", callback_data="cfg:welcome_menu")],
        ]
        await cq.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
        await cq.answer(f"Bot is now {status_label}")

    elif action == "welcome_menu":
        buttons = [
            [InlineKeyboardButton("🖼 Custom Photo", callback_data="cfg:welcome_photo")],
            [InlineKeyboardButton("📝 Custom Text", callback_data="cfg:welcome_textbtn")],
        ]
        await cq.message.edit_text("👋 **Welcome Message Settings**", parse_mode=enums.ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
        await cq.answer()

    elif action == "welcome_photo":
        SESSIONS[uid] = {"step": "await_welcome_photo"}
        await cq.message.reply_text("🖼 Send the new welcome photo now:")
        await cq.answer()

    elif action == "welcome_textbtn":
        SESSIONS[uid] = {"step": "await_welcome_text"}
        await cq.message.reply_text(
            "📝 Send the new welcome text now.\n\nCurrent text:\n\n" + db.get_welcome_text(),
            parse_mode=enums.ParseMode.MARKDOWN,
        )
        await cq.answer()


# =============================================================================
# admin management commands (owner only)
# =============================================================================
@app.on_message(filters.command("addadmin"))
async def addadmin_cmd(client, message):
    uid = message.from_user.id
    if not db.is_owner(uid):
        await message.reply_text("⛔ Only the owner can add admins.")
        return
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        SESSIONS[uid] = {"step": "await_add_admin"}
        await message.reply_text("➕ Send the Telegram ID or @username of the user to add:")
        return
    target_id = await resolve_user_id(client, parts[1])
    if not target_id:
        await message.reply_text("⚠️ Couldn't resolve that user.")
        return
    db.add_admin(target_id)
    await message.reply_text(f"✅ `{target_id}` added as admin.", parse_mode=enums.ParseMode.MARKDOWN)


@app.on_message(filters.command("removeadmin"))
async def removeadmin_cmd(client, message):
    uid = message.from_user.id
    if not db.is_owner(uid):
        await message.reply_text("⛔ Only the owner can remove admins.")
        return
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.reply_text("Usage: `/removeadmin <id or @username>`", parse_mode=enums.ParseMode.MARKDOWN)
        return
    target_id = await resolve_user_id(client, parts[1])
    if not target_id:
        await message.reply_text("⚠️ Couldn't resolve that user.")
        return
    db.remove_admin(target_id)
    await message.reply_text(f"✅ `{target_id}` removed from admins.", parse_mode=enums.ParseMode.MARKDOWN)


@app.on_message(filters.command("adminlist"))
async def adminlist_cmd(client, message):
    uid = message.from_user.id
    if not db.is_owner(uid):
        await message.reply_text("⛔ Only the owner can view the admin list.")
        return
    settings = db.get_settings()
    text = f"👑 Owner: `{settings['owner_id']}`\n"
    if settings["admins"]:
        text += "🛡 Admins:\n" + "\n".join(f"- `{a}`" for a in settings["admins"])
    else:
        text += "🛡 Admins: (none)"
    await message.reply_text(text, parse_mode=enums.ParseMode.MARKDOWN)


# =============================================================================
# ban / unban (owner + admin)
# =============================================================================
@app.on_message(filters.command("ban"))
async def ban_cmd(client, message):
    uid = message.from_user.id
    if not db.is_admin(uid):
        await message.reply_text("⛔ You don't have access.")
        return
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.reply_text("Usage: `/ban <id or @username>`", parse_mode=enums.ParseMode.MARKDOWN)
        return
    target_id = await resolve_user_id(client, parts[1])
    if not target_id:
        await message.reply_text("⚠️ Couldn't resolve that user.")
        return
    if db.is_owner(target_id) or db.is_admin(target_id):
        await message.reply_text("⚠️ You can't ban an owner/admin.")
        return
    db.ban_user(target_id)
    await message.reply_text(f"🚫 `{target_id}` has been banned.", parse_mode=enums.ParseMode.MARKDOWN)


@app.on_message(filters.command("unban"))
async def unban_cmd(client, message):
    uid = message.from_user.id
    if not db.is_admin(uid):
        await message.reply_text("⛔ You don't have access.")
        return
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.reply_text("Usage: `/unban <id or @username>`", parse_mode=enums.ParseMode.MARKDOWN)
        return
    target_id = await resolve_user_id(client, parts[1])
    if not target_id:
        await message.reply_text("⚠️ Couldn't resolve that user.")
        return
    db.unban_user(target_id)
    await message.reply_text(f"✅ `{target_id}` has been unbanned.", parse_mode=enums.ParseMode.MARKDOWN)


# =============================================================================
# sticker set / remove (owner + admin)
# =============================================================================
@app.on_message(filters.command("setsticker"))
async def setsticker_cmd(client, message):
    uid = message.from_user.id
    if not db.is_admin(uid):
        await message.reply_text("⛔ You don't have access.")
        return
    if not message.reply_to_message or not message.reply_to_message.sticker:
        await message.reply_text("↩️ Reply to a sticker with `/setsticker` to set it.", parse_mode=enums.ParseMode.MARKDOWN)
        return
    file_id = message.reply_to_message.sticker.file_id
    db.set_sticker(file_id)
    await message.reply_text("✅ Start-animation sticker set!")


@app.on_message(filters.command("removesticker"))
async def removesticker_cmd(client, message):
    uid = message.from_user.id
    if not db.is_admin(uid):
        await message.reply_text("⛔ You don't have access.")
        return
    db.remove_sticker()
    await message.reply_text("✅ Start-animation sticker removed.")


if __name__ == "__main__":
    print("Bot starting...")
    app.run()
