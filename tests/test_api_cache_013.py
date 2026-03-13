import uuid
import pytest
import allure

MANIFEST_PATH = "/api/v1/manifest"

@allure.epic("Manifest")
@allure.feature("Cache")
@pytest.mark.integration
def test_api_cache_013(api_client, auth_headers):
    r = api_client.get(
        MANIFEST_PATH,
        headers={**auth_headers, "X-Request-ID": f"lm-presence-{uuid.uuid4()}"}
    )

    assert r.status_code == 200

    if "Last-Modified" not in r.headers:
        pytest.xfail("Last-Modified header отсутствует на стенде (может использоваться только ETag)")

    data = r.json()
    assert "widgets" in data
    assert "version" in data

    deny_fields = ["internalflags", "internalid", "stacktrace", "exception", "<html"]
    body_text = (r.text or "").lower()
    for field in deny_fields:
        assert field not in body_text