import pytest
import allure

PROFILE_PATH = "/api/v1/employee-profiles/{profile_id}"

@allure.epic("Profile")
@allure.feature("Cache")
@pytest.mark.integration
def test_profile_cache_005_cache_control_no_store(api_client, valid_prid):
    path = PROFILE_PATH.format(profile_id=valid_prid)
    
    r = api_client.get(path)

    assert r.status_code == 200

    cc = r.headers.get("Cache-Control", "").lower()
    assert "no-store" in cc
    
    vary = r.headers.get("Vary", "").lower()
    assert any(h in vary for h in ["authorization", "x-roles"])

    assert "etag" in [h.lower() for h in r.headers.keys()]
    assert "x-request-id" in [h.lower() for h in r.headers.keys()]

    data = r.json()
    # Проверка на соответствие UUID из фикстуры
    assert data.get("profile_id") == valid_prid or data.get("id") == valid_prid
    
    deny_fields = ["internalflags", "internalid", "stacktrace", "exception", "<html"]
    raw_response_lower = r.text.lower()
    
    for field in deny_fields:
        assert field not in data
        assert field not in raw_response_lower