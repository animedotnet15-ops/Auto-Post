import requests
from config import TMDB_API_KEY, TMDB_IMAGE_BASE

BASE = "https://api.themoviedb.org/3"


def search_multi(query: str):
    """Search movies + tv shows (covers anime, since anime is tv/movie on TMDb)."""
    r = requests.get(
        f"{BASE}/search/multi",
        params={"api_key": TMDB_API_KEY, "query": query, "include_adult": False},
        timeout=15,
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    # keep only movie / tv, drop people etc.
    results = [x for x in results if x.get("media_type") in ("movie", "tv")]
    return results[:6]


def get_details(media_type: str, tmdb_id: int):
    r = requests.get(
        f"{BASE}/{media_type}/{tmdb_id}",
        params={"api_key": TMDB_API_KEY, "append_to_response": "external_ids"},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()

    genres = ", ".join(g["name"] for g in data.get("genres", [])) or "N/A"

    languages = []
    for lang in data.get("spoken_languages", []):
        name = lang.get("english_name") or lang.get("name")
        if name:
            languages.append(name)
    language = ", ".join(dict.fromkeys(languages)) or "N/A"

    imdb_id = data.get("external_ids", {}).get("imdb_id") or data.get("imdb_id")
    rating = data.get("vote_average")

    return {
        "genres": genres,
        "language": language,
        "imdb_id": imdb_id,
        "tmdb_rating": round(rating, 1) if rating else "N/A",
    }


def get_vertical_posters(media_type: str, tmdb_id: int):
    """Returns a list of vertical (portrait) poster image URLs from TMDb only."""
    r = requests.get(
        f"{BASE}/{media_type}/{tmdb_id}/images",
        params={"api_key": TMDB_API_KEY},
        timeout=15,
    )
    r.raise_for_status()
    posters = r.json().get("posters", [])
    # keep only vertical/portrait images (height > width) — drop any landscape ones
    posters = [p for p in posters if p.get("height", 1) > p.get("width", 0)]
    # prefer the highest-voted posters first
    posters.sort(key=lambda p: p.get("vote_average", 0), reverse=True)
    urls = [TMDB_IMAGE_BASE + p["file_path"] for p in posters]
    return urls[:8]  # cap to keep the album small
