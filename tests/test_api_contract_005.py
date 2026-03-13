import pytest
import allure

ALLOWED_TYPES = {"mfe", "link", "container", "empty"}

@allure.epic("Profile")
@allure.feature("Contract")
@allure.feature("Widgets")
@pytest.mark.integration
def test_api_contract_005_widget_types_real(api_client, valid_prid):
    path = f"/api/v1/employee-profiles/{valid_prid}/manifest"
    
    r = api_client.get(path)

    assert r.status_code == 200
    data = r.json()
    
    # Проверяем наличие списка виджетов
    widgets = data.get("widgets", [])
    assert isinstance(widgets, list)
    assert len(widgets) > 0, "Manifest should contain at least one widget"

    for widget in widgets:
        w_type = widget.get("type")
        assert w_type in ALLOWED_TYPES, f"Unknown widget type: {w_type}"
        
        # Валидация специфичных полей в зависимости от типа
        if w_type == "mfe":
            assert "mfe" in widget, "MFE widget must have an 'mfe' URL field"
        elif w_type == "link":
            assert any(k in widget for k in ("url", "href")), "Link widget must have 'url' or 'href'"
        elif w_type == "container":
            assert isinstance(widget.get("children"), list), "Container must have a 'children' list"

    # Золотой стандарт проверки безопасности
    deny_fields = [
        "internalflags", "internalid", "servicerouting", "debuginfo",
        "backendonly", "requiredpermissions", "internalmeta", "configsource",
        "stacktrace", "exception", "<html"
    ]
    
    raw_text_lower = r.text.lower()
    for field in deny_fields:
        assert field not in raw_text_lower, f"Security leak: found '{field}' in raw response"
        assert field not in data, f"Security leak: found '{field}' in JSON root"

    assert data["profile_id"] == valid_prid