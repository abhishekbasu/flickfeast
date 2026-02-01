import json
import logging
from typing import Any

from agents import Agent, ModelSettings, Runner, function_tool
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

from .config import settings
from .movie_api import MovieApiError, fetch_movie_details

load_dotenv(override=True)


@function_tool
def get_movie_details(title: str) -> dict[str, str]:
    """Fetch movie details from OMDb or TMDB."""
    return fetch_movie_details(title)


logger = logging.getLogger(__name__)



class MenuItem(BaseModel):
    name: str
    reason: str


class MenuResponse(BaseModel):
    items: list[MenuItem]
    notes: str = ""


movie_food_items = Agent(
    name="MovieFoodItems",
    instructions=(
        "You are given movie details (title, year, plot). "
        "List 5-6 iconic food or drink items that are explicitly shown or mentioned in the film. "
        "Exclude non-food items (e.g., cigarettes). "
        "Respond as strict JSON with this schema: "
        '{"items": [{"name": "Item", "reason": "Why it matters"}], "notes": "short summary"}'
    ),
    model=settings.openai_model,
    handoff_description="Generate a movie-themed food menu.",
)

movie_searcher = Agent(
    name="MovieSearcher",
    instructions=(
        "You confirm the movie exists by calling get_movie_details with the title. "
        "If found, respond with the movie details and then hand off to MovieFoodItems."
    ),
    tools=[get_movie_details],
    model=settings.openai_model,
    model_settings=ModelSettings(tool_choice="get_movie_details"),
    handoff_description="Verify the movie exists via OMDb/TMDB and pass details forward.",
    handoffs=[movie_food_items],
)

manager = Agent(
    name="MenuManager",
    instructions=(
        "You are the manager. Ask MovieSearcher to verify the movie exists, then "
        "have MovieFoodItems produce a menu based on the verified details. "
        "Keep responses concise and structured."
    ),
    model=settings.openai_model,
    handoffs=[movie_searcher],
)


def _parse_menu_output(raw_output: str) -> MenuResponse | None:
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        return None

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
    except Exception as exc:
        logger.exception("Agents menu generation failed for title=%s", movie_title)
        return {"items": [], "notes": "Menu generation failed"}

    parsed = _parse_menu_output(result.final_output)
    if not parsed:
        logger.warning("Menu output failed schema validation for title=%s", movie_title)
        return {"items": [], "notes": "Menu format invalid"}

    return parsed.model_dump()
