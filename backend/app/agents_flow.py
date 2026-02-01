import json

from agents import Agent, ModelSettings, Runner, function_tool

from .config import settings
from .movie_api import MovieApiError, fetch_movie_details


@function_tool
def get_movie_details(title: str) -> dict[str, str]:
    """Fetch movie details from OMDb or TMDB."""
    return fetch_movie_details(title)


movie_food_items = Agent(
    name="MovieFoodItems",
    instructions=(
        "You are given movie details (title, year, plot). "
        "List 5-8 iconic food or drink items shown or strongly associated with the film. "
        "Respond as JSON: {\"items\": [..], \"notes\": \"short summary\"}."
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


def _parse_menu_output(raw_output: str) -> dict[str, list[str] | str]:
    try:
        parsed = json.loads(raw_output)
        if isinstance(parsed, dict) and "items" in parsed:
            return {
                "items": [str(item) for item in parsed.get("items", [])],
                "notes": str(parsed.get("notes", "")),
            }
    except json.JSONDecodeError:
        pass

    lines = [line.strip("- ") for line in raw_output.splitlines() if line.strip()]
    return {"items": lines, "notes": ""}


async def build_menu(movie_title: str) -> dict[str, list[str] | str]:
    try:
        result = await Runner.run(
            manager,
            input=(
                f"Movie title: {movie_title}. "
                "Verify it and build the menu."
            ),
        )
    except MovieApiError as exc:
        return {"items": [], "notes": str(exc)}

    return _parse_menu_output(result.final_output)
