import requests

from .config import settings


class MovieApiError(Exception):
    pass


def fetch_movie_details(title: str) -> dict[str, str]:
    if settings.omdb_api_key:
        return _fetch_omdb(title)
    if settings.tmdb_api_key:
        return _fetch_tmdb(title)
    raise MovieApiError("OMDB_API_KEY or TMDB_API_KEY must be configured")


def _fetch_omdb(title: str) -> dict[str, str]:
    try:
        response = requests.get(
            "https://www.omdbapi.com/",
            params={
                "t": title,
                "plot": "full",
                "type": "movie",
                "apikey": settings.omdb_api_key,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise MovieApiError("OMDb request failed") from exc
    if data.get("Response") != "True":
        raise MovieApiError(data.get("Error", "Movie not found"))
    return {
        "title": data.get("Title", ""),
        "year": data.get("Year", ""),
        "plot": data.get("Plot", ""),
        "imdb_id": data.get("imdbID", ""),
    }


def _fetch_tmdb(title: str) -> dict[str, str]:
    try:
        response = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"query": title, "include_adult": "false"},
            headers={"Authorization": f"Bearer {settings.tmdb_api_key}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise MovieApiError("TMDB request failed") from exc
    results = data.get("results", [])
    if not results:
        raise MovieApiError("Movie not found")
    movie = results[0]
    return {
        "title": movie.get("title", ""),
        "year": (movie.get("release_date", "") or "")[:4],
        "plot": movie.get("overview", ""),
        "imdb_id": "",
    }
