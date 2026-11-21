import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    return app.test_client()


def test_shorten_returns_six_char_code_and_short_url(client):
    res = client.post("/api/shorten", json={"url": "https://example.com/a/very/long/path"})
    assert res.status_code == 201
    body = res.get_json()
    assert len(body["code"]) == 6
    assert body["short_url"].endswith("/" + body["code"])


def test_rejects_invalid_url(client):
    res = client.post("/api/shorten", json={"url": "not a url"})
    assert res.status_code == 400


def test_rejects_non_http_scheme(client):
    res = client.post("/api/shorten", json={"url": "ftp://example.com/file"})
    assert res.status_code == 400


def test_codes_are_unique(client):
    codes = {client.post("/api/shorten", json={"url": "https://example.com"}).get_json()["code"] for _ in range(50)}
    assert len(codes) == 50


def test_redirects_to_original(client):
    code = client.post("/api/shorten", json={"url": "https://example.com/x"}).get_json()["code"]
    res = client.get(f"/{code}")
    assert res.status_code == 302
    assert res.headers["Location"] == "https://example.com/x"


def test_unknown_code_is_404(client):
    assert client.get("/zzzzzz").status_code == 404


def test_list_and_delete(client):
    code = client.post("/api/shorten", json={"url": "https://example.com"}).get_json()["code"]
    assert client.get("/api/urls").get_json()["total"] == 1
    assert client.delete(f"/api/urls/{code}").status_code == 204
    assert client.get("/api/urls").get_json()["total"] == 0
