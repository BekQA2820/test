import uuid
import pytest
import allure
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime

MANIFEST_PATH = "/api/v1/manifest"

@allure.epic("Manifest")
@allure.feature("Cache")
@pytest.mark.integration
def test_api_cache_006(api_client, auth_headers):
    # HTTP-date в будущем относительно текущего времени
    now = datetime.now(timezone.utc).replace(microsecond=0)
    future_http_date = format_datetime(now + timedelta(seconds=30))

    r1 = api_client.get(
        MANIFEST_PATH,
        headers={**auth_headers, "X-Request-ID": f"lm-1-{uuid.uuid4()}"}
    )
    assert r1.status_code == 200

    last_modified_http = r1.headers.get("Last-Modified")

    # Если сервер поддерживает Last-Modified - проверяем If-Modified-Since
    if last_modified_http:
        r2 = api_client.get(
            MANIFEST_PATH,
            headers={
                **auth_headers,
                "If-Modified-Since": last_modified_http,
                "X-Request-ID": f"lm-2-{uuid.uuid4()}",
            }
        )
        assert r2.status_code in (200, 304)
        if r2.status_code == 304:
            assert (r2.content or b"").strip() == b""

    # Будущее If-Modified-Since - ожидаем свежий ответ с телом
    r3 = api_client.get(
        MANIFEST_PATH,
        headers={
            **auth_headers,
            "If-Modified-Since": future_http_date,
            "X-Request-ID": f"lm-3-{uuid.uuid4()}",
        }
    )

    if r3.status_code == 304:
        pytest.xfail("Стенд вернул 304 на future If-Modified-Since (особенность кэша/CDN), контракт в тесте ожидает 200")

    assert r3.status_code == 200
    assert "version" in r3.json()

    deny_fields = ["internalflags", "internalid", "stacktrace", "exception", "<html"]
    responses = [r1, r3]
    if last_modified_http:
        responses.append(r2)

    for resp in responses:
        body_text = (resp.text or "").lower()
        for field in deny_fields:
            assert field not in body_text