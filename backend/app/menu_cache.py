import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class MenuCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _key_path(self, key: str) -> Path:
        safe = re.sub(r"[^a-z0-9_-]+", "-", key.lower()).strip("-")
        return self.root / f"{safe}.json"

    def get(self, key: str) -> dict | None:
        path = self._key_path(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("Failed reading menu cache for key=%s", key)
            return None

    def set(self, key: str, payload: dict) -> None:
        path = self._key_path(key)
        try:
            path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        except OSError:
            logger.warning("Failed writing menu cache for key=%s", key)
