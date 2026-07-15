import requests
from config import OMDB_API_KEY

BASE = "https://www.omdbapi.com/"


def get_by_imdb_id(imdb_id: str):
    """
    NOTE: OMDb's free tier only returns ONE poster per title (IMDb itself
    has no public multi-image API). So when the user picks the "Imdb"
    source they will see a single vertical poster instead of a gallery.
    If you need a real multi-image IMDb gallery you'd need a paid
    third-party IMDb API and can swap it in here.
    """
    if not imdb_id:
        return None
    r = requests.get(
        BASE, params={"apikey": OMDB_API_KEY, "i": imdb_id}, timeout=15
    )
    r.raise_for_status()
    data = r.json()
    if data.get("Response") != "True":
        return None
    poster = data.get("Poster")
    return {
        "poster": poster if poster and poster != "N/A" else None,
        "imdb_rating": data.get("imdbRating", "N/A"),
    }
