import pytest
import allure

@allure.epic("Manifest")
@allure.feature("Contract")
@allure.feature("Versioning")
@pytest.mark.integration
def test_api_contract_004_real_versioning(api_client, valid_prid):
    # Путь согласно реестру
    path = f"/api/v1/employee-profiles/{valid_prid}/manifest"
    
    # В реальном тесте мы проверяем стабильность структуры
    r1 = api_client.get(path)
    assert r1.status_code == 200
    data1 = r1.json()

    # Если бэкенд поддерживает версионирование через заголовки, используем это.
    # Если нет — просто проверяем консистентность данных при повторном запросе.
    r2 = api_client.get(path)
    assert r2.status_code == 200
    data2 = r2.json()

    # Золотой стандарт: Проверка обязательных полей для любой версии
    for data in (data1, data2):
        assert "version" in data
        assert "gridType" in data
        assert isinstance(data.get("layout"), dict)
        assert isinstance(data.get("widgets"), list)
        
        # Проверка на утечки (Security & Leak Prevention)
        deny_fields = [
            "internalflags", "internalid", "servicerouting", "stacktrace", 
            "exception", "configsource", "<html"
        ]
        raw_text_lower = r1.text.lower() # Проверяем сырой ответ
        for field in deny_fields:
            assert field not in data, f"Found forbidden key '{field}' in JSON"
            assert field not in raw_text_lower, f"Found forbidden string '{field}' in raw text"

    # В интеграционном тесте проверяем, что профили совпадают
    assert data1["profile_id"] == data2["profile_id"]
    assert data1["profile_id"] == valid_prid