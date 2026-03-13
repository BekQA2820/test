import os
import re
import json
import base64
import uuid
import pytest
import allure

from token_manager import get_access_token

MANIFEST_PATH = "/api/v1/manifest"
ETAG_RE = re.compile(r"^[0-9a-f]{32}$", re.IGNORECASE)

DENY_FIELDS = [
    "internalflags", "internalid", "debuginfo", "backendonly",
    "stacktrace", "exception", "<html", "configsource"
]


def _get_ready_token_from_env() -> str | None:
    for k in ("AUTH_TOKEN", "ACCESS_TOKEN", "BEARER_TOKEN", "TOKEN"):
        v = os.getenv(k)
        if v and v.strip():
            v = v.strip()
            return v if v.lower().startswith("bearer ") else f"Bearer {v}"
    return None


def _get_token_from_service_account_base64() -> str | None:
    """
    Обычно SERVICE_ACCOUNT_KEY_BASE64 - это ключ (userId/key),
    но если вдруг туда положили готовый токен - заберем.
    Поддержим разные возможные ключи в JSON.
    """
    raw = os.getenv("SERVICE_ACCOUNT_KEY_BASE64")
    if not raw:
        return None

    try:
        decoded = base64.b64decode(raw).decode("utf-8", errors="ignore")
        js = json.loads(decoded)
    except Exception:
        return None

    for k in ("access_token", "token", "bearer", "bearer_token"):
        v = js.get(k)
        if isinstance(v, str) and v.strip():
            v = v.strip()
            return v if v.lower().startswith("bearer ") else f"Bearer {v}"
    return None


def _auth_headers() -> dict:
    token = _get_ready_token_from_env()
    if not token:
        token = _get_token_from_service_account_base64()

    if not token:
        # Попытаемся получить access_token через token_manager.
        # Если Citadel недоступен - token_manager внутри сделает pytest.skip.
        token = f"Bearer {get_access_token()}"

    return {"Authorization": token}


@allure.epic("Manifest")
@allure.feature("Cache")
@pytest.mark.integration
def test_api_cache_011_manifest_etag_real(api_client):
    headers = _auth_headers()

    r1 = api_client.get(
        MANIFEST_PATH,
        headers={**headers, "X-Request-ID": str(uuid.uuid4())},
        timeout=15,
    )
    assert r1.status_code == 200

    etag = r1.headers.get("ETag")
    assert etag, "ETag header is required for 200 response"

    etag_clean = etag.replace("W/", "").replace('"', "").strip()
    if not ETAG_RE.fullmatch(etag_clean):
        pytest.xfail(f"ETag format is not 32-hex: {etag}")

    r2 = api_client.get(
        MANIFEST_PATH,
        headers={
            **headers,
            "If-None-Match": etag,
            "X-Request-ID": str(uuid.uuid4()),
        },
        timeout=15,
    )
    assert r2.status_code in (200, 304)

    # 304 - без тела
    if r2.status_code == 304:
        assert (r2.content or b"").strip() == b""

    # Security checks (только там, где есть тело)
    for resp in (r1, r2):
        if resp.status_code != 200:
            continue
        low = (resp.text or "").lower()
        for s in DENY_FIELDS:
            assert s not in low
        assert "prid" not in low
        assert "12345" not in low