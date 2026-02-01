import logging

import requests

from .config import settings


class MovieApiError(Exception):
    pass


logger = logging.getLogger(__name__)

def fetch_movie_details(title: str) -> dict[str, str]:
    if settings.omdb_api_key:
        logger.info("Using OMDb lookup for title=%s", title)
        return _fetch_omdb(title)
    if settings.tmdb_api_key:
        logger.info("Using TMDB lookup for title=%s", title)
        return _fetch_tmdb(title)
    raise MovieApiError("OMDB_API_KEY or TMDB_API_KEY must be configured")


def search_movies(query: str) -> list[dict[str, str]]:
    if settings.omdb_api_key:
        logger.info("Using OMDb search for query=%s", query)
        return _search_omdb(query)
    if settings.tmdb_api_key:
        logger.info("Using TMDB search for query=%s", query)
        return _search_tmdb(query)
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
        detail = ""
        if hasattr(exc, "response") and exc.response is not None:
            detail = f" status={exc.response.status_code} body={exc.response.text[:500]}"
        logger.exception("OMDb request failed for title=%s.%s", title, detail)
        raise MovieApiError("OMDb request failed") from exc
    if data.get("Response") != "True":
        raise MovieApiError(data.get("Error", "Movie not found"))
    return {
        "title": data.get("Title", ""),
        "year": data.get("Year", ""),
        "plot": data.get("Plot", ""),
        "imdb_id": data.get("imdbID", ""),
    }


def _tmdb_request_config(query: str) -> tuple[dict[str, str], dict[str, str]]:
    headers: dict[str, str] = {}
    params = {"query": query, "include_adult": "false"}
    token = settings.tmdb_read_access_token.strip()
    if token:
        if token.startswith("Bearer "):
            headers["Authorization"] = token
        else:
            headers["Authorization"] = f"Bearer {token}"
        return headers, params

    token = settings.tmdb_api_key.strip()
    if token:
        if token.startswith("Bearer "):
            headers["Authorization"] = token
        elif token.startswith("eyJ"):
            headers["Authorization"] = f"Bearer {token}"
        else:
            params["api_key"] = token
    return headers, params


def _fetch_tmdb(title: str) -> dict[str, str]:
    headers, params = _tmdb_request_config(title)
    try:
        response = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params=params,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        detail = ""
        if hasattr(exc, "response") and exc.response is not None:
            detail = f" status={exc.response.status_code} body={exc.response.text[:500]}"
        logger.exception("TMDB request failed for title=%s.%s", title, detail)
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


def _search_omdb(query: str) -> list[dict[str, str]]:
    try:
        response = requests.get(
            "https://www.omdbapi.com/",
            params={
                "s": query,
                "type": "movie",
                "apikey": settings.omdb_api_key,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        detail = ""
        if hasattr(exc, "response") and exc.response is not None:
            detail = f" status={exc.response.status_code} body={exc.response.text[:500]}"
        logger.exception("OMDb request failed for query=%s.%s", query, detail)
        raise MovieApiError("OMDb request failed") from exc

    if data.get("Response") != "True":
        return []

    results = []
    for item in data.get("Search", []):
        results.append(
            {
                "title": item.get("Title", ""),
                "year": item.get("Year", ""),
                "imdb_id": item.get("imdbID", ""),
                "poster": item.get("Poster", ""),
            }
        )
    return results


def _search_tmdb(query: str) -> list[dict[str, str]]:
    headers, params = _tmdb_request_config(query)
    try:
        response = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params=params,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        detail = ""
        if hasattr(exc, "response") and exc.response is not None:
            detail = f" status={exc.response.status_code} body={exc.response.text[:500]}"
        logger.exception("TMDB request failed for query=%s.%s", query, detail)
        raise MovieApiError("TMDB request failed") from exc

    results = []
    for item in data.get("results", []):
        poster_path = item.get("poster_path") or ""
        poster_url = f"https://image.tmdb.org/t/p/w185{poster_path}" if poster_path else ""
        results.append(
            {
                "title": item.get("title", ""),
                "year": (item.get("release_date", "") or "")[:4],
                "imdb_id": "",
                "poster": poster_url,
            }
        )
    return results
