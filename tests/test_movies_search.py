from fastapi.testclient import TestClient

from backend.app import movie_api
from backend.app.config import settings
from backend.app.main import app


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload



def test_search_tmdb_uses_bearer_token(monkeypatch):
    settings.omdb_api_key = ""
    settings.tmdb_api_key = "eyJ.test.token"
    settings.tmdb_read_access_token = ""

    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["url"] = url
        captured["params"] = params or {}
        captured["headers"] = headers or {}
        return DummyResponse({"results": [{"title": "Inception", "release_date": "2010-07-16"}]})

    monkeypatch.setattr(movie_api.requests, "get", fake_get)

    client = TestClient(app)
    response = client.get("/movies/search", params={"query": "incep"})

    assert response.status_code == 200
    assert captured["headers"].get("Authorization") == "Bearer eyJ.test.token"
    assert "api_key" not in captured["params"]


def test_search_tmdb_uses_api_key(monkeypatch):
    settings.omdb_api_key = ""
    settings.tmdb_api_key = "my-v3-key"
    settings.tmdb_read_access_token = ""

    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["params"] = params or {}
        captured["headers"] = headers or {}
        return DummyResponse({"results": []})

    monkeypatch.setattr(movie_api.requests, "get", fake_get)

    client = TestClient(app)
    response = client.get("/movies/search", params={"query": "matrix"})

    assert response.status_code == 200
    assert captured["params"].get("api_key") == "my-v3-key"
    assert "Authorization" not in captured["headers"]


def test_search_tmdb_prefers_read_access_token(monkeypatch):
    settings.omdb_api_key = ""
    settings.tmdb_api_key = "my-v3-key"
    settings.tmdb_read_access_token = "read-access-token"

    captured = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["params"] = params or {}
        captured["headers"] = headers or {}
        return DummyResponse({"results": []})

    monkeypatch.setattr(movie_api.requests, "get", fake_get)

    client = TestClient(app)
    response = client.get("/movies/search", params={"query": "alien"})

    assert response.status_code == 200
    assert captured["headers"].get("Authorization") == "Bearer read-access-token"
    assert "api_key" not in captured["params"]
