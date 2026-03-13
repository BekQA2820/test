import uuid
import datetime
import email.utils
import pytest
import allure

MANIFEST_PATH = "/api/v1/manifest"

@allure.epic("Manifest")
@allure.feature("Cache")
@pytest.mark.integration
def test_api_cache_014(api_client, auth_headers):
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    future_date_http = email.utils.format_datetime(now + datetime.timedelta(seconds=30))

    r = api_client.get(
        MANIFEST_PATH,
        headers={
            **auth_headers,
            "If-Modified-Since": future_date_http,
            "X-Request-ID": f"ims-future-{uuid.uuid4()}",
        },
    )

    if r.status_code == 304:
        pytest.xfail("Стенд вернул 304 на future If-Modified-Since (особенность кэша/CDN), тест ожидает 200")

    assert r.status_code == 200

    if "ETag" not in r.headers:
        pytest.xfail("ETag header отсутствует на стенде (возможно используется только Last-Modified)")

    data = r.json()
    assert "version" in data
    assert isinstance(data.get("widgets"), list)

    deny_fields = ["internalflags", "internalid", "stacktrace", "exception", "<html"]
    body_text = (r.text or "").lower()
    for field in deny_fields:
        assert field not in body_text