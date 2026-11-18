"""Reference look-up: WatchBase API, Caliber Corner, links, key setting.

Every outside request goes to a mock transport serving saved responses from
tests/fixtures/spec_lookup; a request the test did not expect fails it.
"""

import os
import stat
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

from app.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.spec_lookup import SpecLookupCache
from app.models.user import User, UserRole
from app.spec_lookup import calibercorner, http, keys, parse

FIX = Path(__file__).parent / "fixtures" / "spec_lookup"
URL = "/api/v1/spec-lookup"
KEY = "test-key-0123456789"


def fixture(name: str) -> str:
    return (FIX / name).read_text()


class Net:
    """Mock network: routes (method, url) to saved answers and records calls."""

    def __init__(self):
        self.routes = {}
        self.calls = []

    def add(self, method, url, status=200, text="", exc=None):
        self.routes[(method, url)] = (status, text, exc)

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        url = str(request.url)
        if (request.method, url) not in self.routes:
            raise AssertionError(f"unexpected request {request.method} {url}")
        status, text, exc = self.routes[(request.method, url)]
        if exc:
            raise exc
        return httpx.Response(status, text=text)

    def wb_body(self, request) -> dict:
        return {k: v[0] for k, v in parse_qs(request.content.decode()).items()}

    def wb_answers(self, search_text, watches=None):
        """WatchBase answers depend on the POST body (id), so route by body."""
        net = self

        def handler(request):
            net.calls.append(request)
            url = str(request.url)
            if url == "https://api.watchbase.com/v1/search/refnr":
                return httpx.Response(200, text=search_text)
            if url == "https://api.watchbase.com/v1/watch":
                wid = net.wb_body(request)["id"]
                return httpx.Response(200, text=(watches or {})[wid])
            return Net.handler(net, request)

        return handler


@pytest.fixture
def net(monkeypatch, tmp_path):
    n = Net()
    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(n.handler))
    monkeypatch.setattr(settings, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "WATCHBASE_API_KEY", "")
    monkeypatch.setattr(calibercorner, "throttle", http.Throttle(0))
    return n


def use_handler(monkeypatch, handler):
    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(handler))


def caliber_corner(net, with_page=True):
    net.add("GET", calibercorner.SITEMAPS[0], text=fixture("cc_sitemap.xml"))
    net.add("GET", calibercorner.SITEMAPS[1], text=fixture("cc_sitemap2.xml"))
    if with_page:
        net.add(
            "GET",
            "https://calibercorner.com/rolex-caliber-3235/",
            text=fixture("cc_rolex_3235.html"),
        )


# ------------------------------------------------------------------ no key


class TestWithoutKey:
    def test_links_only(self, client, auth_headers, test_brand, net):
        r = client.get(
            URL, params={"reference": "126610LN", "brand_id": str(test_brand.id)},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "links_only"
        assert body["fields"] == {}
        labels = [link["label"] for link in body["links"]]
        assert labels == ["WatchBase", "Caliber Corner", "Rolex website"]
        assert "126610LN" in body["links"][0]["url"]
        assert "rolex.com" in body["links"][2]["url"]
        assert net.calls == []  # nothing fetched without a caliber

    def test_caliber_given_gets_movement_facts(
        self, client, auth_headers, test_brand, net
    ):
        caliber_corner(net)
        r = client.get(
            URL,
            params={"reference": "126610LN", "brand_id": str(test_brand.id), "caliber": "3235"},
            headers=auth_headers,
        )
        body = r.json()
        assert body["status"] == "links_only"
        assert body["fields"] == {"power_reserve": 70}
        assert body["sources"]["power_reserve"]["name"] == "Caliber Corner"
        assert body["movement"]["jewels"] == 31
        assert body["movement"]["frequency"].startswith("28,800 bph")
        assert body["links"][1]["url"] == "https://calibercorner.com/rolex-caliber-3235/"
        for call in net.calls:
            assert call.headers["user-agent"].startswith("WatchCollectionTracker/")

    def test_requires_login(self, client, net):
        assert client.get(URL, params={"reference": "126610LN"}).status_code == 401


# ------------------------------------------------------------------ with key


@pytest.fixture
def with_key(net, monkeypatch):
    monkeypatch.setattr(settings, "WATCHBASE_API_KEY", KEY)
    return net


class TestWatchBase:
    def test_single_match_fills_fields(
        self, client, auth_headers, test_brand, with_key, monkeypatch
    ):
        caliber_corner(with_key)
        use_handler(
            monkeypatch,
            with_key.wb_answers(
                fixture("wb_search_126610LN.json"),
                {"31501": fixture("wb_watch_31501.json")},
            ),
        )
        r = client.get(URL, params={"reference": "126610LN"}, headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        f = body["fields"]
        assert f["brand_name"] == "Rolex"
        assert f["model"] == "Submariner Date 41 Steel / Black / Black"
        assert f["movement_type_name"] == "Automatic"
        assert Decimal(str(f["case_diameter"])) == Decimal("41.00")
        assert Decimal(str(f["lug_width"])) == Decimal("21.00")
        assert "case_thickness" not in f  # WatchBase has no height for it
        assert f["water_resistance"] == 300
        assert f["power_reserve"] == 70
        assert f["caliber"] == "3235"
        assert f["crystal"] == "Sapphire"
        assert f["case_material"] == "Stainless Steel"
        assert set(f["complications"]) == {"Date", "Dive Bezel"}
        assert body["sources"]["caliber"] == {
            "name": "WatchBase",
            "url": "https://watchbase.com/rolex/submariner/126610ln-0001",
        }
        assert body["movement"]["source"]["name"] == "Caliber Corner"

    def test_key_only_in_post_body(self, client, auth_headers, with_key, monkeypatch):
        use_handler(monkeypatch, with_key.wb_answers(fixture("wb_search_none.json")))
        client.get(URL, params={"reference": "XYZ123"}, headers=auth_headers)
        (call,) = with_key.calls
        assert call.method == "POST"
        assert KEY not in str(call.url)
        assert with_key.wb_body(call) == {"key": KEY, "format": "json", "q": "XYZ123"}

    def test_several_matches_then_choice(
        self, client, auth_headers, with_key, monkeypatch
    ):
        use_handler(
            monkeypatch,
            with_key.wb_answers(
                fixture("wb_search_SBGE.json"),
                {"31034": fixture("wb_watch_31034.json")},
            ),
        )
        with_key.add("GET", calibercorner.SITEMAPS[0], text=fixture("cc_sitemap.xml"))
        with_key.add("GET", calibercorner.SITEMAPS[1], text=fixture("cc_sitemap2.xml"))
        body = client.get(URL, params={"reference": "SBGE2"}, headers=auth_headers).json()
        assert body["status"] == "choices"
        assert [c["reference"] for c in body["choices"]] == ["SBGE201", "SBGE205", "SBGE209"]
        assert all(c["brand"] == "Grand Seiko" for c in body["choices"])
        # No paid Watch call before the user picks
        assert all(not str(c.url).endswith("/watch") for c in with_key.calls)

        body = client.get(
            URL, params={"reference": "SBGE2", "watchbase_id": 31034}, headers=auth_headers
        ).json()
        assert body["status"] == "ok"
        f = body["fields"]
        assert f["movement_type_name"] == "Spring Drive"
        assert f["water_resistance"] == 100  # 10 bar
        assert f["case_material"] == "Titanium"
        assert "lug_width" not in f
        assert {"GMT", "Power Reserve Indicator", "Date"} <= set(f["complications"])
        # Caliber Corner has no 9R66 page (only 9R65): no movement facts from it
        assert body["movement"]["source"]["name"] == "WatchBase"

    def test_exact_reference_picks_without_asking(
        self, client, auth_headers, with_key, monkeypatch
    ):
        use_handler(
            monkeypatch,
            with_key.wb_answers(
                fixture("wb_search_SBGE.json"),
                {"31034": fixture("wb_watch_31034.json")},
            ),
        )
        with_key.add("GET", calibercorner.SITEMAPS[0], text=fixture("cc_sitemap.xml"))
        with_key.add("GET", calibercorner.SITEMAPS[1], text=fixture("cc_sitemap2.xml"))
        body = client.get(URL, params={"reference": "sbge-201"}, headers=auth_headers).json()
        assert body["status"] == "ok"
        assert body["fields"]["caliber"] == "9R66"

    def test_not_found(self, client, auth_headers, with_key, monkeypatch):
        use_handler(monkeypatch, with_key.wb_answers(fixture("wb_search_none.json")))
        body = client.get(URL, params={"reference": "NOPE99"}, headers=auth_headers).json()
        assert body["status"] == "not_found"
        assert body["message"]
        assert len(body["links"]) >= 2

    @pytest.mark.parametrize("status", [401, 403])
    def test_bad_key(self, client, auth_headers, with_key, status):
        with_key.add("POST", "https://api.watchbase.com/v1/search/refnr", status=status)
        r = client.get(URL, params={"reference": "126610LN"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "bad_key"
        assert KEY not in r.text

    def test_error_answer_about_credits_is_bad_key(self, client, auth_headers, with_key):
        with_key.add(
            "POST",
            "https://api.watchbase.com/v1/search/refnr",
            text='{"error": "Not enough credits"}',
        )
        body = client.get(URL, params={"reference": "126610LN"}, headers=auth_headers).json()
        assert body["status"] == "bad_key"

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"status": 500},
            {"status": 200, "text": "<html>maintenance</html>"},
            {"exc": httpx.ConnectError("down")},
            {"exc": httpx.ReadTimeout("slow")},
        ],
    )
    def test_source_down_is_a_plain_message(self, client, auth_headers, with_key, kwargs):
        with_key.add("POST", "https://api.watchbase.com/v1/search/refnr", **kwargs)
        r = client.get(URL, params={"reference": "126610LN"}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "unavailable"
        assert r.json()["links"]

    def test_repeat_lookup_uses_cache(
        self, client, auth_headers, with_key, monkeypatch, test_db
    ):
        caliber_corner(with_key)
        use_handler(
            monkeypatch,
            with_key.wb_answers(
                fixture("wb_search_126610LN.json"),
                {"31501": fixture("wb_watch_31501.json")},
            ),
        )
        first = client.get(URL, params={"reference": "126610LN"}, headers=auth_headers).json()
        calls = len(with_key.calls)
        assert calls > 0
        second = client.get(URL, params={"reference": "126610ln"}, headers=auth_headers).json()
        assert len(with_key.calls) == calls  # nothing fetched again
        assert second["fields"] == first["fields"]
        assert test_db.query(SpecLookupCache).count() >= 3


# ------------------------------------------------------------------ parsing


class TestParsing:
    def test_caliber_corner_table(self):
        facts = calibercorner.parse_page(fixture("cc_rolex_3235.html"))
        assert facts["power_reserve"] == 70
        assert facts["jewels"] == 31
        assert facts["frequency"] == "28,800 bph (4Hz)"
        assert facts["diameter"] == "28.50"
        assert facts["movement_type"].startswith("Automatic")

    def test_index_and_matching(self):
        index = calibercorner.build_index([fixture("cc_sitemap.xml"), fixture("cc_sitemap2.xml")])
        assert "rolex|3235" in index and len(index) == 5  # /movements/ skipped
        find = calibercorner.find_page
        assert find(index, "Rolex", "3235").endswith("rolex-caliber-3235/")
        assert find(index, "ETA", "2824").endswith("eta-caliber-2824-2/")
        assert find(index, "Seiko", "NH35").endswith("seiko-sii-caliber-nh35a/")
        assert find(index, "Grand Seiko", "9R65").endswith("seiko-caliber-9r65/")
        assert find(index, "Grand Seiko", "9R66") is None
        assert find(index, "Rolex", "") is None

    def test_units(self):
        assert parse.millimetres("41.00 mm") == Decimal("41.00")
        assert parse.millimetres("28,5mm") == Decimal("28.50")
        assert parse.metres("300.00 m") == 300
        assert parse.metres("10 bar") == 100
        assert parse.metres("5 ATM") == 50
        assert parse.metres("330 ft") == 101
        assert parse.hours("~70 hours") == 70
        assert parse.hours("3 days") == 72
        assert parse.movement_type("Manual winding") == "Hand-wound"
        assert parse.movement_type("Quartz") == "Quartz"
        assert parse.movement_type("Spring Drive") == "Spring Drive"
        assert parse.movement_type(None) is None

    def test_throttle_waits_a_second(self):
        now = [100.0]
        slept = []
        t = http.Throttle(1.0, clock=lambda: now[0], sleep=lambda s: slept.append(s))
        t.wait()
        now[0] += 0.25
        t.wait()
        assert slept == [pytest.approx(0.75)]

    def test_caliber_corner_down_skips_quietly(self, net, test_db):
        net.add("GET", calibercorner.SITEMAPS[0], exc=httpx.ConnectError("down"))
        net.add("GET", calibercorner.SITEMAPS[1], exc=httpx.ConnectError("down"))
        assert calibercorner.caliber_facts(test_db, "Rolex", "3235") is None


# ------------------------------------------------------------------ key setting


@pytest.fixture
def admin_headers(test_db):
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        role=UserRole.admin,
    )
    test_db.add(admin)
    test_db.commit()
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(admin.id)})}"}


KEY_URL = "/api/v1/settings/watchbase-key"


class TestKeySetting:
    def test_admin_only(self, client, auth_headers, net):
        assert client.get(KEY_URL, headers=auth_headers).status_code == 403
        r = client.put(KEY_URL, json={"api_key": KEY}, headers=auth_headers)
        assert r.status_code == 403

    def test_set_and_clear(self, client, admin_headers, net, tmp_path):
        assert client.get(KEY_URL, headers=admin_headers).json() == {
            "configured": False,
            "from_environment": False,
        }
        r = client.put(KEY_URL, json={"api_key": f"  {KEY} "}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json() == {"configured": True, "from_environment": False}
        assert KEY not in r.text
        path = tmp_path / keys.KEY_FILE_NAME
        assert path.read_text() == KEY
        assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
        assert keys.get_watchbase_key() == KEY

        r = client.delete(KEY_URL, headers=admin_headers)
        assert r.json()["configured"] is False
        assert not path.exists()

    def test_environment_wins(self, client, admin_headers, net, monkeypatch):
        monkeypatch.setattr(settings, "WATCHBASE_API_KEY", "from-env-key-123")
        keys.save_watchbase_key("from-file-key-456")
        assert keys.get_watchbase_key() == "from-env-key-123"
        assert client.get(KEY_URL, headers=admin_headers).json() == {
            "configured": True,
            "from_environment": True,
        }

    def test_rejects_spaces(self, client, admin_headers, net):
        r = client.put(KEY_URL, json={"api_key": "two words here"}, headers=admin_headers)
        assert r.status_code == 422


# ------------------------------------------------------------------ new fields


class TestNewWatchFields:
    def test_create_search_and_pdf(self, client, auth_headers, test_brand):
        r = client.post(
            "/api/v1/watches/",
            headers=auth_headers,
            json={
                "brand_id": str(test_brand.id),
                "model": "Submariner Date",
                "caliber": "3235",
                "crystal": "Sapphire",
                "case_material": "Oystersteel",
            },
        )
        assert r.status_code == 201, r.text
        w = r.json()
        assert (w["caliber"], w["crystal"], w["case_material"]) == (
            "3235",
            "Sapphire",
            "Oystersteel",
        )
        for term in ("3235", "sapphire", "oyster"):
            found = client.get(
                "/api/v1/watches/", params={"search": term}, headers=auth_headers
            ).json()
            assert found["total"] == 1, term

        r = client.put(
            f"/api/v1/watches/{w['id']}", json={"crystal": "Hesalite"}, headers=auth_headers
        )
        assert r.json()["crystal"] == "Hesalite"

        pdf = client.get(f"/api/v1/watches/{w['id']}/export/pdf", headers=auth_headers)
        assert pdf.status_code == 200
