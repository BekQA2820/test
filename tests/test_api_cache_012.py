import uuid
import pytest
import allure

MANIFEST_PATH = "/api/v1/employee-profiles/manifest"
REQUIRED_VARY_SUBSETS = ["authorization", "x-roles"]

@allure.epic("Manifest")
@allure.feature("Cache")
@pytest.mark.integration
def test_api_cache_012(api_client, auth_headers):
    # 1) запрос с валидным токеном из фикстуры
    r1 = api_client.get(
        MANIFEST_PATH,
        headers={**auth_headers, "X-Request-ID": f"vary-1-{uuid.uuid4()}"}
    )

    assert r1.status_code == 200

    vary1 = (r1.headers.get("Vary") or "")
    vary1_l = vary1.lower()
    for subset in REQUIRED_VARY_SUBSETS:
        assert subset in vary1_l

    # 2) запрос с "другим токеном"
    # тут намеренно не используем auth_headers, чтобы реально проверить влияние Authorization
    r2 = api_client.get(
        MANIFEST_PATH,
        headers={
            "Authorization": "Bearer manual-test-token",
            "X-Request-ID": f"vary-2-{uuid.uuid4()}",
        }
    )

    # если вдруг токен валиден (внезапно) - проверяем, что vary содержит нужные ключи
    # если не валиден (ожидаемо) - все равно проверяем, что vary не сломан и нет утечек
    vary2 = (r2.headers.get("Vary") or "").lower()
    for subset in REQUIRED_VARY_SUBSETS:
        # не все ошибки обязаны возвращать Vary, но если отдают - он должен быть корректным
        if vary2:
            assert subset in vary2

    if r2.status_code == 200:
        data = r2.json()
        assert "profile_id" in data
        assert "widgets" in data

    deny_fields = [
        "internalflags", "internalid", "backendonly", "stacktrace",
        "exception", "debuginfo", "<html"
    ]

    for resp in (r1, r2):
        raw_lower = (resp.text or "").lower()
        for field in deny_fields:
            assert field not in raw_lower