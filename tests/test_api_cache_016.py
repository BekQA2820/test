import re
import uuid
import pytest
import allure

MANIFEST_PATH = "/api/v1/manifest"

@allure.epic("Manifest")
@allure.feature("Cache")
@pytest.mark.integration
def test_api_cache_016(api_client, auth_headers):
    r1 = api_client.get(
        MANIFEST_PATH,
        headers={**auth_headers, "X-Request-ID": f"weak-etag-1-{uuid.uuid4()}"}
    )
    assert r1.status_code == 200

    etag = r1.headers.get("ETag")
    assert etag is not None

    # делаем weak etag для If-None-Match
    weak_etag = etag if etag.strip().startswith("W/") else f'W/{etag}'

    r2 = api_client.get(
        MANIFEST_PATH,
        headers={
            **auth_headers,
            "If-None-Match": weak_etag,
            "X-Request-ID": f"weak-etag-2-{uuid.uuid4()}",
        },
    )

    assert r2.status_code in (200, 304)

    if r2.status_code == 304:
        assert (r2.content or b"").strip() == b""
        if "ETag" in r2.headers and r2.headers["ETag"]:
            assert re.search(r"[0-9a-f]{32}", r2.headers["ETag"], re.IGNORECASE)

    deny_fields = ["internalflags", "internalid", "stacktrace", "exception", "<html"]
    for resp in (r1, r2):
        body_text = (resp.text or "").lower()
        for field in deny_fields:
            assert field not in body_text