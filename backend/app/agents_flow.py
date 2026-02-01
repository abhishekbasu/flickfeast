import json
import logging

from agents import Agent, ModelSettings, Runner, function_tool
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

from .config import settings
from .movie_api import MovieApiError, fetch_movie_details
from .recipe_api import RecipeApiError, search_recipes

load_dotenv(override=True)


@function_tool
def get_movie_details(title: str) -> dict[str, str]:
    """Fetch movie details from OMDb or TMDB."""
    return fetch_movie_details(title)


@function_tool
def find_recipes(query: str, limit: int = 3) -> list[dict[str, str]]:
    """Search recipe websites for a query and return recipe summaries."""
    return search_recipes(query, limit)


logger = logging.getLogger(__name__)


class MenuItem(BaseModel):
    name: str
    reason: str


class RecipeItem(BaseModel):
    title: str
    source: str
    url: str


class MenuResponse(BaseModel):
    items: list[MenuItem]
    notes: str = ""
    recipes: list[RecipeItem] = []


movie_food_items = Agent(
    name="MovieFoodItems",
    instructions=(
        "You are given movie details (title, year, plot). "
        "List 5-6 iconic food or drink items that are explicitly shown or mentioned in the film. "
        "Exclude non-food items (e.g., cigarettes). "
        "Use the find_recipes tool to search recipe websites for 2-3 items "
        "that could be served at a party. "
        "Respond ONLY as strict JSON with this schema: "
        '{"items": [{"name": "Item", "reason": "Why it matters"}], '
        '"recipes": [{"title": "Recipe", "source": "Site", "url": "https://..."}], '
        '"notes": "short summary"}'
    ),
    model=settings.openai_model,
    tools=[find_recipes],
    handoff_description="Generate a movie-themed food menu.",
)

menu_formatter = Agent(
    name="MenuFormatter",
    instructions=(
        "You will be given a draft menu response. Convert it to strict JSON that "
        "matches this schema exactly: "
        '{"items": [{"name": "Item", "reason": "Why it matters"}], '
        '"recipes": [{"title": "Recipe", "source": "Site", "url": "https://..."}], '
        '"notes": "short summary"} '
        "Return ONLY JSON. If data is missing, return empty lists and an explanatory notes string."
    ),
    model=settings.openai_model,
)

movie_searcher = Agent(
    name="MovieSearcher",
    instructions=(
        "You confirm the movie exists by calling get_movie_details with the title. "
        "If found, return the movie details to PartyPlanner."
    ),
    tools=[get_movie_details],
    model=settings.openai_model,
    model_settings=ModelSettings(tool_choice="get_movie_details"),
    handoff_description="Verify the movie exists via OMDb/TMDB and pass details forward.",
)

manager = Agent(
    name="PartyPlanner",
    instructions=(
        "You are the manager. Ask MovieSearcher to verify the movie exists and return details. "
        "Then ask MovieFoodItems to build a menu and recipe list based on those details. "
        "Keep responses concise and structured."
    ),
    model=settings.openai_model,
    handoffs=[movie_searcher, movie_food_items],
)


def _extract_json(raw_output: str) -> dict | None:
    cleaned = raw_output.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end >= 0 and end > start:
            cleaned = cleaned[start : end + 1]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def _coerce_menu_payload(payload: dict) -> dict:
    items = payload.get("items", [])
    if items and isinstance(items, list) and isinstance(items[0], str):
        payload["items"] = [{"name": item, "reason": ""} for item in items]
    return payload


def _parse_menu_output(raw_output: str) -> MenuResponse | None:
    parsed = _extract_json(raw_output)
    if parsed is None:
        return None
    parsed = _coerce_menu_payload(parsed)
    try:
        return MenuResponse.model_validate(parsed)
    except ValidationError:
        return None


async def build_menu(movie_title: str) -> dict[str, list[str] | str]:
    try:
        result = await Runner.run(
            manager,
            input=(f"Movie title: {movie_title}. Verify it and build the menu."),
        )
    except MovieApiError as exc:
        logger.exception("Movie lookup failed for menu title=%s", movie_title)
        return {"items": [], "notes": str(exc)}
    except RecipeApiError as exc:
        logger.exception("Recipe lookup failed for title=%s", movie_title)
        return {"items": [], "notes": str(exc)}
    except Exception as exc:
        logger.exception("Agents menu generation failed for title=%s", movie_title)
        return {"items": [], "notes": "Menu generation failed"}

    parsed = _parse_menu_output(result.final_output)
    if not parsed:
        logger.warning(
            "Menu output failed schema validation for title=%s. Attempting repair.",
            movie_title,
        )
        try:
            repair = await Runner.run(
                menu_formatter,
                input=result.final_output,
            )
            parsed = _parse_menu_output(repair.final_output)
        except Exception as exc:
            logger.exception("Menu format repair failed for title=%s", movie_title)
            parsed = None

    if not parsed:
        return {"items": [], "notes": "Menu format invalid"}

    return parsed.model_dump()
