import re
import uuid
import pytest
import allure

MANIFEST_PATH = "/api/v1/manifest"

@allure.epic("Manifest")
@allure.feature("Cache")
@pytest.mark.integration
def test_api_cache_017(api_client, auth_headers):
    cache_key = uuid.uuid4().hex
    path = f"{MANIFEST_PATH}?cache_key={cache_key}"

    r1 = api_client.get(
        path,
        headers={**auth_headers, "X-Request-ID": f"cache-017-1-{uuid.uuid4()}"}
    )
    assert r1.status_code == 200

    r2 = api_client.get(
        path,
        headers={**auth_headers, "X-Request-ID": f"cache-017-2-{uuid.uuid4()}"}
    )
    assert r2.status_code == 200

    # если X-Cache есть - он должен быть валидным
    x_cache = r2.headers.get("X-Cache")
    if x_cache is not None:
        assert x_cache in ("HIT", "MISS")

    data1 = r1.json()
    assert "widgets" in data1
    assert "version" in data1

    etag1 = r1.headers.get("ETag")
    etag2 = r2.headers.get("ETag")

    if etag1 and etag2:
        assert re.search(r"[0-9a-f]{32}", etag1, re.IGNORECASE)
        # если сервер явно сказал HIT - ETag обязаны совпасть
        if x_cache == "HIT":
            assert etag1 == etag2

    deny_fields = ["internalflags", "internalid", "stacktrace", "exception", "<html"]
    for resp in (r1, r2):
        body_text = (resp.text or "").lower()
        for field in deny_fields:
            assert field not in body_text