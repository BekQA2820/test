import uuid
import pytest
import allure

@allure.epic("Manifest")
@allure.feature("Cache")
@pytest.mark.integration
def test_api_cache_004_determinism_real(api_client, auth_header, valid_prid):
    path = f"/api/v1/employee-profiles/{valid_prid}/manifest"
    
    headers = auth_header if isinstance(auth_header, dict) else {"Authorization": auth_header}
    
    r1 = api_client.get(f"{path}?cb={uuid.uuid4().hex}", headers=headers)
    assert r1.status_code == 200
    data1 = r1.json()
    
    r2 = api_client.get(f"{path}?cb={uuid.uuid4().hex}", headers=headers)
    assert r2.status_code == 200
    data2 = r2.json()

    layout1 = data1.get("layout", {})
    layout2 = data2.get("layout", {})
    
    assert isinstance(layout1, dict)
    assert layout1 == layout2
    assert layout1.get("rows", 0) >= 1

    deny_fields = [
        "internalflags", "internalid", "requiredpermissions", 
        "configsource", "stacktrace", "exception", "debuginfo", 
        "backendonly", "internalmeta", "servicerouting", "<html"
    ]
    
    for resp, data in [(r1, data1), (r2, data2)]:
        raw_text_lower = resp.text.lower()
        for field in deny_fields:
            assert field not in raw_text_lower
            assert field not in str(data).lower()
            
        request_id = resp.headers.get("X-Request-ID") or resp.headers.get("x-request-id")
        if request_id:
            try:
                uuid.UUID(str(request_id))
            except ValueError:
                pass