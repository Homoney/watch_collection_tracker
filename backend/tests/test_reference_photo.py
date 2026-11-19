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
from app.spec_lookup import grandseiko, http, photos, public
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
        if setup == "no_reference":
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


OG = "https://cdn.watchbase.com/watch/rolex/submariner/126610ln-0001-78.jpg"
PAGE = "https://watchbase.com/rolex/submariner/126610ln-0001"


@pytest.fixture
def site(monkeypatch, tmp_path, mock_upload_dir):
    """No key: WatchBase's public search and watch page from saved copies."""
    state = {"search": fx("site_search_126610LN.json"), "page_status": 200, "calls": []}
    images = {OG: ("image/jpeg", (FIX / "wb_photo_126610ln.png").read_bytes())}
    fetched = []

    def site_answer(request):
        state["calls"].append(request)
        assert request.url.host == "watchbase.com"
        assert request.headers["User-Agent"].startswith("WatchCollectionTracker/")
        if request.url.path == "/filter/results":
            return httpx.Response(200, text=state["search"])
        if state["page_status"] != 200:
            return httpx.Response(state["page_status"])
        return httpx.Response(200, text=fx("site_page_126610ln.html"))

    def fetch_bytes(url, headers=None, **kw):
        fetched.append(url)
        if url not in images:
            raise ValueError("HTTP 404")
        return images[url]

    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(site_answer))
    monkeypatch.setattr(safe_fetch, "fetch_bytes", fetch_bytes)
    monkeypatch.setattr(photos, "throttle", http.Throttle(0))
    monkeypatch.setattr(settings, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "WATCHBASE_API_KEY", "")
    return {"state": state, "images": images, "fetched": fetched}


class TestReferencePhotoWithoutKey:
    def test_saved_from_the_public_page(
        self, client, auth_headers, test_watch, test_db, site
    ):
        test_watch.reference_number = "126610LN"
        test_db.commit()
        r = post(client, auth_headers, test_watch)
        assert r.status_code == 201, r.text
        img = r.json()["image"]
        assert img["source"] == "reference_photo"
        assert img["source_url"] == PAGE
        assert site["fetched"] == [OG]  # the page's og:image
        paths = [c.url.path for c in site["state"]["calls"]]
        assert paths == ["/filter/results", "/rolex/submariner/126610ln-0001"]
        assert site["state"]["calls"][0].url.params["q"] == "126610LN"

    def test_search_is_cached(self, client, auth_headers, test_watch, test_db, site):
        test_watch.reference_number = "126610LN"
        test_db.commit()
        post(client, auth_headers, test_watch)
        test_db.query(WatchImage).delete()
        test_db.commit()
        site["state"]["calls"].clear()
        assert post(client, auth_headers, test_watch).status_code == 201
        assert [c.url.path for c in site["state"]["calls"]] == [
            "/rolex/submariner/126610ln-0001"
        ]

    def test_falls_back_to_search_thumbnail(
        self, client, auth_headers, test_watch, test_db, site
    ):
        test_watch.reference_number = "126610LN"
        test_db.commit()
        site["images"].clear()
        thumb = "https://cdn.watchbase.com/watch/md/rolex/submariner/126610ln-0001-78.jpg"
        site["images"][thumb] = ("image/jpeg", (FIX / "wb_photo_126610ln.png").read_bytes())
        r = post(client, auth_headers, test_watch)
        assert r.status_code == 201
        assert site["fetched"] == [OG, thumb.replace("/md/", "/lg/"), thumb]

    @pytest.mark.parametrize(
        "reference, setup, status",
        [
            ("5711/1A", None, "choices"),
            ("ZZQ99999X", "none", "none"),
            ("126610LN", "page_down", "unavailable"),
            ("126610LN", "bad_answer", "unavailable"),
            (None, None, "no_reference"),
        ],
    )
    def test_plain_message(
        self, client, auth_headers, test_watch, test_db, site, reference, setup, status
    ):
        test_watch.reference_number = reference
        test_db.commit()
        if reference == "5711/1A":
            site["state"]["search"] = fx("site_search_5711-1A.json")
        if setup == "none":
            site["state"]["search"] = fx("site_search_none.json")
        elif setup == "page_down":
            site["state"]["page_status"] = 503
        elif setup == "bad_answer":
            site["state"]["search"] = "<html>not json</html>"
        r = post(client, auth_headers, test_watch)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == status
        assert r.json()["message"]
        assert refs(test_db, test_watch) == []

    def test_exact_reference_picks_one_of_several(self):
        found = public.parse_search(fx("site_search_5711-1A.json"))
        assert len(found) == 5
        assert public.pick(found, "5711/1A") is None
        chosen = public.pick(found, "5711/1A-014")
        assert chosen["url"] == "https://watchbase.com/patek-philippe/nautilus/5711-1a-014"

    def test_only_watchbase_pages_and_image_server(self):
        bad = (
            '{"numWatches":2,"watchesHtml":"'
            '<a href=\\"https://evil.example/x\\" class=\\"item-block watch-block\\">'
            "</a>"
            '<a href=\\"http://watchbase.com/x\\" class=\\"item-block watch-block\\">'
            '</a>"}'
        )
        assert public.parse_search(bad) == []
        page = '<meta property="og:image" content="https://evil.example/a.jpg" />'
        assert public.og_image(page) is None
        assert public.og_image(fx("site_page_126610ln.html")) == OG


GS_PAGE = "https://www.grand-seiko.com/us-en/collections/sbge253g"
GS_PHOTO = (
    "https://www.grand-seiko.com/us-en/-/media/Images/GlobalEn/GrandSeiko/Home/"
    "collections/Products/SBGE253/01_SBGE253_4pc.jpg"
)


class TestReferencePhotoGrandSeiko:
    """WatchBase has no SBGE253: the photo named by grand-seiko.com's page."""

    @pytest.fixture
    def gs_watch(self, test_db, test_watch):
        from app.models.reference import Brand

        brand = Brand(name="Grand Seiko")
        test_db.add(brand)
        test_db.commit()
        test_watch.brand_id = brand.id
        test_watch.reference_number = "SBGE253"
        test_db.commit()
        test_db.refresh(test_watch)
        return test_watch

    @pytest.mark.parametrize("key", ["test-key-0123456789", ""])
    def test_saved_from_the_brand_page(
        self, client, auth_headers, gs_watch, test_db, wb, monkeypatch, key
    ):
        monkeypatch.setattr(settings, "WATCHBASE_API_KEY", key)
        monkeypatch.setattr(grandseiko, "throttle", http.Throttle(0))
        wb["state"]["search"] = fx("wb_search_none.json")
        wb["images"][GS_PHOTO] = ("image/png", (FIX / "wb_photo_126610ln.png").read_bytes())

        def net(request):
            url = str(request.url)
            if url == GS_PAGE:
                return httpx.Response(200, text=fx("gs_sbge253g.html"))
            if url.startswith("https://watchbase.com/filter/results"):
                return httpx.Response(200, text=fx("site_search_none.json"))
            if url.startswith("https://api.watchbase.com/"):
                return httpx.Response(200, text=fx("wb_search_none.json"))
            raise AssertionError(f"unexpected request {url}")

        monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(net))
        r = post(client, auth_headers, gs_watch)
        assert r.status_code == 201, r.text
        image = r.json()["image"]
        assert image["source"] == "reference_photo"
        assert image["source_url"] == GS_PAGE
        assert [u for u, _ in wb["fetched"]] == [GS_PHOTO]

    def test_only_product_photos_from_the_brand_site(self):
        page = fx("gs_sbge253g.html")
        logo = page.replace(
            "collections/Products/SBGE253/01_SBGE253_4pc.jpg", "GrandSeikoLogo/x.jpg"
        )
        assert grandseiko.parse_page(logo, "sbge253")["photo"] is None
        evil = page.replace("https://www.grand-seiko.com/", "https://evil.example/")
        assert grandseiko.parse_page(evil, "sbge253")["photo"] is None


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
