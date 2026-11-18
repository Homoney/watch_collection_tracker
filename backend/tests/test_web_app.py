"""The built web app is served by FastAPI, with security headers."""

import pytest
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.testclient import TestClient

from app.middleware.security_headers import CSP, SecurityHeadersMiddleware
from app.web import mount_web_app


@pytest.fixture
def dist(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>app</html>")
    (tmp_path / "assets" / "main-abc123.js").write_text("console.log(1);" * 200)
    (tmp_path / "favicon.svg").write_text("<svg/>")
    (tmp_path.parent / "secret.txt").write_text("outside")
    return tmp_path


@pytest.fixture
def web_client(dist):
    app = FastAPI()

    @app.get("/api/v1/ping")
    async def ping():
        return {"ok": True}

    @app.get("/api/v1/items/")
    async def list_items():
        return []

    @app.post("/api/v1/items/", status_code=201)
    async def create_item():
        return {"created": True}

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    assert mount_web_app(app, str(dist)) is True
    return TestClient(app)


def test_no_build_means_no_routes(tmp_path):
    app = FastAPI()
    assert mount_web_app(app, str(tmp_path / "missing")) is False
    assert TestClient(app).get("/").status_code == 404


def test_index_served_at_root_and_for_app_routes(web_client):
    for path in ("/", "/watches/123", "/admin"):
        r = web_client.get(path)
        assert r.status_code == 200, path
        assert r.text == "<html>app</html>"
        assert r.headers["cache-control"] == "no-cache"


def test_real_files_served(web_client):
    r = web_client.get("/favicon.svg")
    assert r.status_code == 200
    assert r.text == "<svg/>"


def test_assets_cached_and_compressed(web_client):
    r = web_client.get("/assets/main-abc123.js", headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200
    assert "immutable" in r.headers["cache-control"]
    assert r.headers["content-encoding"] == "gzip"


def test_api_and_uploads_never_fall_back_to_index(web_client):
    assert web_client.get("/api/v1/ping").json() == {"ok": True}
    for path in ("/api/v1/nope", "/api", "/uploads/x/y.jpg", "/health"):
        assert web_client.get(path).status_code == 404, path


def test_api_path_without_trailing_slash_redirects(web_client):
    # Issue: the web app swallowed /api/v1/saved-searches (no slash) with a
    # 404 instead of FastAPI's usual redirect to /api/v1/saved-searches/
    for method in ("GET", "POST"):
        r = web_client.request(method, "/api/v1/items", follow_redirects=False)
        assert r.status_code == 307, method
        assert r.headers["location"].endswith("/api/v1/items/"), method
    assert web_client.get("/api/v1/items").json() == []
    assert web_client.post("/api/v1/items").status_code == 201


def test_other_methods_on_app_routes_are_not_found(web_client):
    assert web_client.post("/watches/123").status_code == 404


def test_no_escape_from_dist(web_client):
    r = web_client.get("/..%2Fsecret.txt")
    assert "outside" not in r.text


def test_security_headers(web_client):
    r = web_client.get("/")
    assert r.headers["content-security-policy"] == CSP
    assert r.headers["x-frame-options"] == "SAMEORIGIN"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "permissions-policy" in r.headers


def test_no_csp_on_uploads_and_docs(client):
    for path in ("/uploads/x/y.jpg", "/docs"):
        r = client.get(path)
        assert "content-security-policy" not in r.headers, path
        assert r.headers["x-content-type-options"] == "nosniff"


def test_main_app_has_headers(client):
    r = client.get("/health")
    assert r.json() == {"status": "healthy"}
    assert r.headers["content-security-policy"] == CSP
    assert client.get("/api").json()["message"] == "Watch Collection Tracker API"


def test_head_on_web_app_routes(web_client):
    # Uptime monitors and `curl -I` probe with HEAD
    for path in ("/", "/watches/123", "/favicon.svg", "/assets/main-abc123.js"):
        r = web_client.head(path)
        assert r.status_code == 200, path
        assert r.content == b""


def test_head_on_health(client):
    assert client.head("/health").status_code == 200


def test_csp_allows_blob_images():
    # Upload previews and the QR code are blob: URLs
    img_src = next(d for d in CSP.split(";") if d.strip().startswith("img-src"))
    assert "blob:" in img_src.split()
