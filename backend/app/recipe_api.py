import logging

import requests

from .config import settings


class RecipeApiError(Exception):
    pass


logger = logging.getLogger(__name__)


def search_recipes(query: str, limit: int = 5) -> list[dict[str, str]]:
    if settings.spoonacular_api_key:
        return _search_spoonacular(query, limit)
    return _search_mealdb(query, limit)


def _search_spoonacular(query: str, limit: int) -> list[dict[str, str]]:
    try:
        response = requests.get(
            "https://api.spoonacular.com/recipes/complexSearch",
            params={
                "query": query,
                "number": limit,
                "apiKey": settings.spoonacular_api_key,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        detail = ""
        if hasattr(exc, "response") and exc.response is not None:
            detail = (
                f" status={exc.response.status_code} body={exc.response.text[:500]}"
            )
        logger.exception("Spoonacular request failed for query=%s.%s", query, detail)
        raise RecipeApiError("Recipe search failed") from exc

    recipes = []
    for item in data.get("results", [])[:limit]:
        recipes.append(
            {
                "title": item.get("title", ""),
                "source": "Spoonacular",
                "url": item.get("sourceUrl", ""),
            }
        )
    return recipes


def _search_mealdb(query: str, limit: int) -> list[dict[str, str]]:
    try:
        response = requests.get(
            "https://www.themealdb.com/api/json/v1/1/search.php",
            params={"s": query},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        detail = ""
        if hasattr(exc, "response") and exc.response is not None:
            detail = (
                f" status={exc.response.status_code} body={exc.response.text[:500]}"
            )
        logger.exception("MealDB request failed for query=%s.%s", query, detail)
        raise RecipeApiError("Recipe search failed") from exc

    meals = data.get("meals") or []
    recipes = []
    for item in meals[:limit]:
        recipes.append(
            {
                "title": item.get("strMeal", ""),
                "source": "TheMealDB",
                "url": item.get("strSource", "") or item.get("strYoutube", ""),
            }
        )
    return recipes
