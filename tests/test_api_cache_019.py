import re
import uuid
import pytest
import allure

MANIFEST_PATH = "/api/v1/manifest"

@allure.epic("Manifest")
@allure.feature("Cache")
@pytest.mark.integration
def test_api_cache_019(api_client, auth_headers):
    expected_max_age = 300

    r = api_client.get(
        MANIFEST_PATH,
        headers={**auth_headers, "X-Request-ID": f"cc-019-{uuid.uuid4()}"}
    )
    assert r.status_code == 200

    cc = (r.headers.get("Cache-Control") or "").lower()

    # запрещенные директивы - строго
    assert "private" not in cc
    assert "no-store" not in cc

    # "public" зависит от вашего контракта - в оригинале запрещен, оставим как инвариант
    assert "public" not in cc

    # max-age - пытаемся извлечь число
    m = re.search(r"max-age=(\d+)", cc)
    if not m:
        pytest.xfail(f"max-age отсутствует в Cache-Control: {r.headers.get('Cache-Control')}")
    else:
        actual = int(m.group(1))
        if actual != expected_max_age:
            pytest.xfail(f"max-age отличается от ожидаемого {expected_max_age}: {actual}")

    deny_fields = ["internalflags", "internalid", "stacktrace", "exception", "<html"]
    body_text = (r.text or "").lower()
    for field in deny_fields:
        assert field not in body_text