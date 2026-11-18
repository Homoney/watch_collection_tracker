"""Reference photo from WatchBase (#205 part 2): saved through the image
pipeline as a private, labelled copy; never replaces the owner's photos.

Network answers come from tests/fixtures/spec_lookup (no live calls).
"""

from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from app.config import settings
from app.models.watch_image import ImageSourceEnum, WatchImage
from app.spec_lookup import http, photos
from app.utils import pdf_export, safe_fetch

FIX = Path(__file__).parent / "fixtures" / "spec_lookup"
LG = "https://cdn.watchbase.com/watch/lg/rolex/submariner/126610ln-0001-3f.png"
MD = "https://cdn.watchbase.com/watch/md/rolex/submariner/126610ln-0001-3f.png"


def fx(name):
    return (FIX / name).read_text()


@pytest.fixture
def wb(monkeypatch, tmp_path, mock_upload_dir):
    """WatchBase API from fixtures; image server answers from `images`."""
    state = {"search": fx("wb_search_126610LN.json"), "watch_status": 200, "api_calls": []}
    images = {LG: ("image/png", (FIX / "wb_photo_126610ln.png").read_bytes())}
    fetched = []

    def api(request):
        state["api_calls"].append(request)
        body = {k: v[0] for k, v in parse_qs(request.content.decode()).items()}
        if str(request.url).endswith("/search/refnr"):
            return httpx.Response(200, text=state["search"])
        if state["watch_status"] != 200:
            return httpx.Response(state["watch_status"])
        return httpx.Response(200, text=fx(f"wb_watch_{body['id']}.json"))

    def fetch_bytes(url, headers=None, **kw):
        fetched.append((url, headers))
        if url not in images:
            raise ValueError("HTTP 404")
        return images[url]

    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(api))
    monkeypatch.setattr(safe_fetch, "fetch_bytes", fetch_bytes)
    monkeypatch.setattr(photos, "throttle", http.Throttle(0))
    monkeypatch.setattr(settings, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "WATCHBASE_API_KEY", "test-key-0123456789")
    return {"state": state, "images": images, "fetched": fetched}


def post(client, headers, watch, body=None):
    return client.post(
        f"/api/v1/watches/{watch.id}/reference-photo", json=body, headers=headers
    )


def refs(db, watch):
    return db.query(WatchImage).filter_by(watch_id=watch.id).all()


class TestReferencePhoto:
    def test_saved_as_labelled_private_copy(
        self, client, auth_headers, test_watch, test_db, wb
    ):
        test_watch.reference_number = "126610LN"
        test_db.commit()
        r = post(client, auth_headers, test_watch, {"watchbase_id": 31501})
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["status"] == "saved"
        img = body["image"]
        assert img["source"] == "reference_photo"
        assert img["source_url"] == "https://watchbase.com/rolex/submariner/126610ln-0001"
        assert img["is_primary"] is True  # the watch had no photos
        assert img["width"] == 480 and img["mime_type"] == "image/jpeg"
        assert (Path(settings.UPLOAD_DIR) / img["file_path"]).is_file()
        # Large size asked first, with the honest User-Agent
        url, headers = wb["fetched"][0]
        assert url == LG
        assert headers["User-Agent"].startswith("WatchCollectionTracker/")

    def test_never_replaces_the_owners_photo(
        self, client, auth_headers, test_watch, test_db, wb
    ):
        own = WatchImage(
            watch_id=test_watch.id, file_path="x/own.jpg", file_name="own.jpg",
            file_size=1, mime_type="image/jpeg", is_primary=True, sort_order=0,
            source=ImageSourceEnum.USER_UPLOAD,
        )
        test_db.add(own)
        test_db.commit()
        r = post(client, auth_headers, test_watch, {"watchbase_id": 31501})
        assert r.status_code == 201
        assert r.json()["image"]["is_primary"] is False
        assert r.json()["image"]["sort_order"] == 1
        test_db.refresh(own)
        assert own.is_primary is True

    def test_one_per_watch_and_removable(
        self, client, auth_headers, test_watch, test_db, wb
    ):
        first = post(client, auth_headers, test_watch, {"watchbase_id": 31501})
        again = post(client, auth_headers, test_watch, {"watchbase_id": 31501})
        assert again.status_code == 200
        assert again.json()["status"] == "exists" and again.json()["image"] is None
        image_id = first.json()["image"]["id"]
        d = client.delete(
            f"/api/v1/watches/{test_watch.id}/images/{image_id}", headers=auth_headers
        )
        assert d.status_code in (200, 204)
        assert refs(test_db, test_watch) == []

    def test_falls_back_to_medium_size(self, client, auth_headers, test_watch, wb):
        wb["images"][MD] = wb["images"].pop(LG)
        r = post(client, auth_headers, test_watch, {"watchbase_id": 31501})
        assert r.status_code == 201
        assert [u for u, _ in wb["fetched"]] == [LG, MD]

    def test_uses_reference_number_when_one_match(
        self, client, auth_headers, test_watch, test_db, wb
    ):
        test_watch.reference_number = "126610LN"
        test_db.commit()
        r = post(client, auth_headers, test_watch)
        assert r.status_code == 201
        assert r.json()["image"]["source"] == "reference_photo"

    @pytest.mark.parametrize(
        "setup, status",
        [
            ("no_key", "no_key"),
            ("no_reference", "no_reference"),
            ("choices", "choices"),
            ("not_found", "none"),
            ("no_photo_on_server", "none"),
            ("too_small", "none"),
            ("bad_key", "bad_key"),
            ("down", "unavailable"),
        ],
    )
    def test_plain_message_when_no_photo(
        self, client, auth_headers, test_watch, test_db, wb, monkeypatch, setup, status
    ):
        test_watch.reference_number = "126610LN"
        body = None
        if setup == "no_key":
            monkeypatch.setattr(settings, "WATCHBASE_API_KEY", "")
        elif setup == "no_reference":
            test_watch.reference_number = None
        elif setup == "choices":
            wb["state"]["search"] = fx("wb_search_SBGE.json")
            test_watch.reference_number = "SBGE2"
        elif setup == "not_found":
            wb["state"]["search"] = fx("wb_search_none.json")
        elif setup == "no_photo_on_server":
            wb["images"].clear()
        elif setup == "too_small":
            wb["images"][LG] = ("image/png", (FIX / "wb_photo_small.png").read_bytes())
        elif setup == "bad_key":
            wb["state"]["watch_status"] = 403
            body = {"watchbase_id": 31501}
        elif setup == "down":
            wb["state"]["watch_status"] = 502
            body = {"watchbase_id": 31501}
        test_db.commit()

        r = post(client, auth_headers, test_watch, body)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == status
        assert r.json()["image"] is None
        assert r.json()["message"]
        assert refs(test_db, test_watch) == []

    def test_watch_without_photo_in_catalogue(
        self, client, auth_headers, test_watch, wb, monkeypatch
    ):
        # SBGE201's fixture has no images: nothing is downloaded
        r = post(client, auth_headers, test_watch, {"watchbase_id": 31034})
        assert r.json()["status"] == "none"
        assert wb["fetched"] == []

    def test_only_watchbase_image_server(self):
        w = {"images": ["https://evil.example/x.png", "http://cdn.watchbase.com/a.png"]}
        assert photos.watchbase.photo_urls(w) == []
        w = {"images": ["http://cdn.watchbase.com/watch/md/a.png"]}
        assert photos.watchbase.photo_urls(w) == []

    def test_other_users_watch(self, client, auth_headers2, test_watch, wb):
        r = post(client, auth_headers2, test_watch, {"watchbase_id": 31501})
        assert r.status_code == 404

    def test_lookup_says_photo_available(self, client, auth_headers, wb):
        body = client.get(
            "/api/v1/spec-lookup", params={"reference": "126610LN"}, headers=auth_headers
        ).json()
        # Caliber Corner is not routed here; the look-up still answers
        assert body["status"] == "ok"
        assert body["watchbase_id"] == 31501
        assert body["has_photo"] is True

    def test_old_google_route_is_gone(self, client, auth_headers, test_watch):
        r = client.post(
            f"/api/v1/watches/{test_watch.id}/fetch-images", headers=auth_headers
        )
        assert r.status_code in (404, 405)


def test_pdf_leaves_out_reference_photos(monkeypatch, tmp_path):
    asked = []
    monkeypatch.setattr(pdf_export.os.path, "exists", lambda p: asked.append(p) or False)
    data = {
        "brand": {"name": "Rolex"}, "model": "Sub",
        "images": [{"file_path": "w/ref.jpg", "is_primary": True, "source": "reference_photo"}],
    }
    pdf_export.generate_watch_pdf(data, upload_dir=str(tmp_path))
    assert not any(p.endswith("ref.jpg") for p in asked)
    data["images"].append({"file_path": "w/own.jpg", "is_primary": False, "source": "user_upload"})
    pdf_export.generate_watch_pdf(data, upload_dir=str(tmp_path))
    assert any(p.endswith("own.jpg") for p in asked)
