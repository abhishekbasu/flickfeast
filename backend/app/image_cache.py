import base64
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DiskImageCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _key_path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.root / f"{digest}.png"

    def get(self, key: str) -> str | None:
        path = self._key_path(key)
        if not path.exists():
            return None
        try:
            data = path.read_bytes()
            encoded = base64.b64encode(data).decode("ascii")
            return f"data:image/png;base64,{encoded}"
        except OSError as exc:
            logger.warning("Failed reading image cache for key=%s", key)
            return None

    def set(self, key: str, data_uri: str) -> None:
        if not data_uri.startswith("data:image/png;base64,"):
            return
        path = self._key_path(key)
        try:
            raw = data_uri.split(",", 1)[1]
            payload = base64.b64decode(raw)
            path.write_bytes(payload)
        except (OSError, ValueError) as exc:
            logger.warning("Failed writing image cache for key=%s", key)
