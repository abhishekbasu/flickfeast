import asyncio
import json
import logging
from pathlib import Path

from agents import Agent, ModelSettings, RunConfig, Runner, function_tool
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from .config import settings
from .image_cache import DiskImageCache
from .menu_cache import MenuCache
from .movie_api import MovieApiError, fetch_movie_details
from .recipe_api import RecipeApiError, search_recipes

load_dotenv(override=True)

logger = logging.getLogger(__name__)
async_openai_client = AsyncOpenAI()
_image_cache: dict[str, str] = {}
_image_cache_order: list[str] = []
_IMAGE_CACHE_MAX = 100
disk_cache = DiskImageCache(Path(__file__).resolve().parents[1] / "cache" / "images")
menu_cache = MenuCache(Path(__file__).resolve().parents[1] / "cache" / "menus")


@function_tool
def get_movie_details(title: str) -> dict[str, str]:
    """Fetch movie details from OMDb or TMDB."""
    return fetch_movie_details(title)


@function_tool
def find_recipe(query: str) -> dict[str, str]:
    """Search recipe websites and return the top recipe."""
    results = search_recipes(query, limit=1)
    return results[0] if results else {"title": "", "source": "", "url": ""}


@function_tool
async def generate_food_image(item_name: str) -> dict[str, str]:
    """Generate a food image via OpenAI and cache it on disk."""
    cache_key = item_name.strip().lower()
    if cache_key:
        cached = disk_cache.get(cache_key)
        if cached:
            return {"image_key": cache_key}

    prompt = (
        "Studio-lit food photography, overhead view of "
        f"{item_name}, appetizing, high detail, soft shadows."
    )
    try:
        response = await async_openai_client.images.generate(
            model=settings.openai_image_model,
            prompt=prompt,
            size="1024x1024",
        )
        image_b64 = response.data[0].b64_json
    except Exception as exc:
        logger.exception("OpenAI image generation failed for item=%s", item_name)
        raise
    data_uri = f"data:image/png;base64,{image_b64}"
    if cache_key:
        disk_cache.set(cache_key, data_uri)
        return {"image_key": cache_key}
    return {"image_key": ""}


class MenuItem(BaseModel):
    name: str
    reason: str
    image_data: str | None = None


class RecipeItem(BaseModel):
    title: str
    source: str
    url: str
    ingredients: list[str] = []
    steps: list[str] = []


class MenuResponse(BaseModel):
    items: list[MenuItem]
    notes: str = ""


movie_food_items = Agent(
    name="MovieFoodItems",
    instructions=(
        "You are given movie details (title, year, plot). "
        "List exactly 5 iconic food or drink items that are explicitly shown or mentioned in the film. "
        "Exclude non-food items (e.g., cigarettes). "
        "Respond ONLY as strict JSON with this schema: "
        '{"items": [{"name": "Item", "reason": "Why it matters"}], '
        '"notes": "short summary"}'
    ),
    model=settings.openai_model,
    handoff_description="Generate a movie-themed food menu.",
)

food_photo_generator = Agent(
    name="FoodPhotoGenerator",
    instructions=(
        "You generate a single appetizing food photo for a given item. "
        "Call generate_food_image with the item name and return JSON: "
        '{"image_key": "cache-key"}'
    ),
    model=settings.openai_model,
    tools=[generate_food_image],
)

menu_formatter = Agent(
    name="MenuFormatter",
    instructions=(
        "You will be given a draft menu response. Convert it to strict JSON that "
        "matches this schema exactly: "
        '{"items": [{"name": "Item", "reason": "Why it matters"}], '
        '"notes": "short summary"} '
        "Return ONLY JSON. If data is missing, return empty lists and an explanatory notes string."
    ),
    model=settings.openai_model,
)

recipe_agent = Agent(
    name="RecipeAgent",
    instructions=(
        "You receive a single menu item and must return exactly one recipe. "
        "Call find_recipe exactly once with the item name to find a source, then respond immediately. "
        "Then generate a concise recipe with ingredients and steps. "
        "Respond ONLY as strict JSON: "
        '{"title": "Recipe", "source": "Site", "url": "https://...", '
        '"ingredients": ["..."], "steps": ["..."]}'
    ),
    model=settings.openai_model,
    tools=[find_recipe],
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
        "Then ask MovieFoodItems to build a menu based on those details. "
        "Keep responses concise and structured."
    ),
    model=settings.openai_model,
    handoffs=[movie_searcher, movie_food_items, food_photo_generator, recipe_agent],
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
    if isinstance(payload.get("items"), list):
        payload["items"] = payload["items"][:5]
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
    cached_menu = menu_cache.get(movie_title)
    if cached_menu:
        logger.info("Menu cache hit for title=%s", movie_title)
        menu_payload = cached_menu
    else:
        menu_payload = None
    if menu_payload is None:
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
            logger.debug("Raw menu output: %s", str(result.final_output)[:2000])
            try:
                repair = await Runner.run(
                    menu_formatter,
                    input=result.final_output,
                )
                logger.debug("Repaired menu output: %s", str(repair.final_output)[:2000])
                parsed = _parse_menu_output(repair.final_output)
            except Exception as exc:
                logger.exception("Menu format repair failed for title=%s", movie_title)
                parsed = None

        if not parsed or not parsed.items:
            logger.warning("Menu items missing for title=%s. Retrying with direct food agent.", movie_title)
            try:
                details = fetch_movie_details(movie_title)
                retry = await Runner.run(
                    movie_food_items,
                    input=(
                        f"Movie title: {details.get('title')} ({details.get('year')}). "
                        f"Plot: {details.get('plot')}"
                    ),
                    max_turns=2,
                )
                parsed = _parse_menu_output(retry.final_output)
            except Exception:
                logger.exception("Direct menu retry failed for title=%s", movie_title)
                parsed = None

        if not parsed or not parsed.items:
            return {"items": [], "notes": "No menu items were provided."}

        menu_payload = parsed.model_dump()
    async def _fetch_image(item: dict) -> str | None:
        if item.get("image_data"):
            return item.get("image_data")
        cache_key = item.get("name", "").strip().lower()
        if cache_key and cache_key in _image_cache:
            return _image_cache[cache_key]
        if cache_key:
            cached = disk_cache.get(cache_key)
            if cached:
                _image_cache[cache_key] = cached
                _image_cache_order.append(cache_key)
                return cached
        try:
            photo = await Runner.run(
                food_photo_generator,
                input=f"Food item: {item.get('name', '')}",
                run_config=RunConfig(tracing_disabled=True),
            )
            if isinstance(photo.final_output, dict):
                parsed_photo = photo.final_output
            else:
                parsed_photo = _extract_json(photo.final_output) or photo.final_output
            if isinstance(parsed_photo, dict) and parsed_photo.get("image_key"):
                cached = disk_cache.get(parsed_photo["image_key"])
                if cached:
                    if cache_key:
                        _image_cache[cache_key] = cached
                        _image_cache_order.append(cache_key)
                        if len(_image_cache_order) > _IMAGE_CACHE_MAX:
                            oldest = _image_cache_order.pop(0)
                            _image_cache.pop(oldest, None)
                    return cached
        except Exception:
            logger.exception("Image generation failed for item=%s", item.get("name"))
        return None

    async def _fallback_recipe(item_name: str) -> dict[str, str]:
        seed = search_recipes(item_name, limit=1)
        seed = seed[0] if seed else {"title": "", "source": "", "url": ""}
        title = seed.get("title") or item_name
        source = seed.get("source", "")
        url = seed.get("url", "")
        return {
            "title": title,
            "source": source,
            "url": url,
            "ingredients": [
                f"{item_name} base ingredient",
                "Seasoning to taste",
                "Optional garnish",
            ],
            "steps": [
                f"Prepare the {item_name} ingredients.",
                "Cook until done and season to taste.",
                "Plate and add garnish.",
            ],
        }

    async def _fetch_recipe(item_name: str) -> dict[str, str]:
        try:
            run = await Runner.run(
                recipe_agent,
                input=f"Menu item: {item_name}",
                max_turns=4,
                run_config=RunConfig(tracing_disabled=True),
            )
            payload = run.final_output if isinstance(run.final_output, dict) else _extract_json(run.final_output)
            if isinstance(payload, dict) and payload.get("title"):
                return payload
        except Exception:
            logger.exception("Recipe generation failed for item=%s", item_name)
        return await _fallback_recipe(item_name)

    items = menu_payload.get("items", [])
    image_tasks = [_fetch_image(item) for item in items]
    recipe_tasks = [_fetch_recipe(item.get("name", "")) for item in items]
    image_results, recipes = await asyncio.gather(
        asyncio.gather(*image_tasks),
        asyncio.gather(*recipe_tasks),
    )
    for item, image_data in zip(items, image_results, strict=False):
        if image_data:
            item["image_data"] = image_data

    for item, recipe in zip(items, recipes, strict=False):
        if recipe.get("title"):
            item["recipe"] = recipe

    menu_cache.set(movie_title, menu_payload)
    return menu_payload
