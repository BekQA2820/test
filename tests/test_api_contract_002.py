import pytest
import allure

@allure.epic("Manifest")
@allure.feature("Contract")
@pytest.mark.integration
def test_api_contract_002_real_manifest(api_client, valid_prid):
    path = f"/api/v1/employee-profiles/{valid_prid}/manifest"
    
    r = api_client.get(path)

    assert r.status_code == 200
    
    data = r.json()
    raw_text_lower = r.text.lower()
    
    # Золотой стандарт проверки безопасности (Security & Leak Prevention)
    deny_fields = [
        "internalflags", "internalid", "servicerouting", "debuginfo",
        "backendonly", "requiredpermissions", "internalmeta", "configsource",
        "stacktrace", "exception", "<html"
    ]
    
    for field in deny_fields:
        assert field not in raw_text_lower, f"Security leak: forbidden string '{field}' found in raw response"
        assert field not in data, f"Security leak: forbidden key '{field}' found in JSON root"

    # Проверка бизнес-логики контракта
    assert data["profile_id"] == valid_prid
    assert "version" in data
    assert isinstance(data.get("widgets"), list)