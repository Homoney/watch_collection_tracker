"""Fetch images saves files under settings.UPLOAD_DIR (#202).

Uses the real UPLOAD_DIR (the test DATA_DIR), where uploads are served from."""

import io
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image as PILImage

from app.config import settings
from app.models.watch_image import WatchImage


def _jpeg(width=400, height=300) -> bytes:
    buf = io.BytesIO()
    PILImage.new("RGB", (width, height), color="blue").save(buf, format="JPEG")
    return buf.getvalue()


class TestFetchImagesLocation:
    def test_fetched_images_are_saved_under_upload_dir(
        self, client, auth_headers, test_watch, test_db, monkeypatch
    ):
        from app.utils import google_images

        monkeypatch.setattr(
            google_images,
            "_scrape_google_images",
            lambda query, count: [f"https://images.example/{i}.jpg" for i in range(3)],
        )
        monkeypatch.setattr(
            google_images, "fetch_bytes", lambda url: ("image/jpeg", _jpeg())
        )

        response = client.post(
            f"/api/v1/watches/{test_watch.id}/fetch-images?limit=2",
            headers=auth_headers,
        )

        assert response.status_code == 201, response.text
        images = test_db.query(WatchImage).filter_by(watch_id=test_watch.id).all()
        assert len(images) == 2
        for image in images:
            saved = Path(settings.UPLOAD_DIR) / image.file_path
            assert saved.is_file(), saved

        # The signed link the API returns serves the saved file
        url = response.json()["images"][0]["url"]
        served = client.get(url)
        assert served.status_code == 200
        assert (
            served.content
            == (
                Path(settings.UPLOAD_DIR) / urlsplit(url).path[len("/uploads/") :]
            ).read_bytes()
        )

    def test_url_import_saves_under_upload_dir(self, monkeypatch):
        import asyncio

        from app.utils import google_images

        monkeypatch.setattr(
            google_images, "fetch_bytes", lambda url: ("image/jpeg", _jpeg())
        )

        result = asyncio.run(
            google_images.fetch_watch_images_from_urls(
                ["https://images.example/a.jpg"], "watch-1"
            )
        )

        assert len(result) == 1
        assert (Path(settings.UPLOAD_DIR) / result[0]["file_path"]).is_file()


class TestFetchImagesNothingFound:
    """#205: no results or a failing source is a clean empty answer, not a 500."""

    def _post(self, client, auth_headers, watch):
        return client.post(
            f"/api/v1/watches/{watch.id}/fetch-images", headers=auth_headers
        )

    def _assert_empty(self, response, test_db, watch):
        assert response.status_code == 200, response.text
        assert response.json() == {
            "message": "No images found; you can upload your own",
            "images": [],
        }
        assert test_db.query(WatchImage).filter_by(watch_id=watch.id).count() == 0

    def test_search_finds_nothing(
        self, client, auth_headers, test_watch, test_db, monkeypatch
    ):
        from app.utils import google_images

        monkeypatch.setattr(google_images, "_scrape_google_images", lambda q, n: [])
        self._assert_empty(
            self._post(client, auth_headers, test_watch), test_db, test_watch
        )

    def test_offset_past_the_end(
        self, client, auth_headers, test_watch, test_db, monkeypatch
    ):
        from app.utils import google_images

        monkeypatch.setattr(
            google_images,
            "_scrape_google_images",
            lambda q, n: ["https://i.example/a.jpg"],
        )
        r = client.post(
            f"/api/v1/watches/{test_watch.id}/fetch-images?offset=6",
            headers=auth_headers,
        )
        self._assert_empty(r, test_db, test_watch)

    def test_no_download_succeeds(
        self, client, auth_headers, test_watch, test_db, monkeypatch
    ):
        from app.utils import google_images

        monkeypatch.setattr(
            google_images,
            "_scrape_google_images",
            lambda q, n: [f"https://i.example/{i}.jpg" for i in range(3)],
        )

        def broken(url):
            raise OSError("connection refused")

        monkeypatch.setattr(google_images, "fetch_bytes", broken)
        self._assert_empty(
            self._post(client, auth_headers, test_watch), test_db, test_watch
        )

    def test_source_failure(
        self, client, auth_headers, test_watch, test_db, monkeypatch
    ):
        from app.api.v1 import watches

        def boom(**kwargs):
            raise RuntimeError("image source down")

        monkeypatch.setattr(watches, "fetch_watch_images", boom)
        self._assert_empty(
            self._post(client, auth_headers, test_watch), test_db, test_watch
        )
