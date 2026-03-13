import pytest
import allure

@allure.epic("Manifest")
@allure.feature("Contract")
@pytest.mark.integration
def test_api_contract_001(api_client, valid_prid):
    # Путь формируем динамически с реальным UUID
    path = f"/api/v1/employee-profiles/{valid_prid}/manifest"
    
    r = api_client.get(path)

    assert r.status_code == 200
    
    data = r.json()
    
    # Проверка обязательных полей контракта
    assert data["profile_id"] == valid_prid
    assert "version" in data
    assert isinstance(data.get("layout"), dict)
    assert isinstance(data.get("widgets"), list)
    
    # Проверка безопасности (Золотой стандарт)
    deny_fields = [
        "internalflags", "internalid", "requiredpermissions", 
        "configsource", "requiredroles", "stacktrace", "exception", "<html"
    ]
    raw_text = r.text.lower()
    
    for field in deny_fields:
        assert field not in data
        assert field not in raw_text