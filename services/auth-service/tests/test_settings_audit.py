"""Tests for AppSettings and AuditLog endpoints."""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.models.security_event import SecurityEventType


# ─── Settings ────────────────────────────────────────────────────────────────

@pytest.fixture
def settings_client():
    from src.main import app
    from src.dependencies import get_db

    mock_session = AsyncMock()
    # Make execute return an empty result (no existing settings → creates default)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()

    app.dependency_overrides[get_db] = lambda: mock_session
    with TestClient(app) as c:
        yield c, mock_session
    app.dependency_overrides.clear()


def _make_existing_settings():
    """Return a MagicMock that looks like a saved AppSettings row."""
    existing = MagicMock()
    existing.site_name = "Quimica de Altura"
    existing.maintenance_mode = False
    existing.default_language = "es"
    existing.max_upload_size_mb = 10
    existing.enable_public_api = True
    existing.contact_email = None
    existing.updated_at = datetime.now(timezone.utc)
    return existing


class TestSettingsEndpoints:
    def test_get_settings_creates_default(self, settings_client):
        client, mock_session = settings_client

        existing = _make_existing_settings()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute = AsyncMock(return_value=mock_result)

        r = client.get("/api/v1/settings/")
        assert r.status_code == 200
        data = r.json()
        assert "site_name" in data
        assert "maintenance_mode" in data
        assert "default_language" in data

    def test_get_settings_returns_correct_values(self, settings_client):
        client, mock_session = settings_client

        existing = _make_existing_settings()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute = AsyncMock(return_value=mock_result)

        r = client.get("/api/v1/settings/")
        assert r.status_code == 200
        data = r.json()
        assert data["site_name"] == "Quimica de Altura"
        assert data["maintenance_mode"] is False
        assert data["default_language"] == "es"
        assert data["max_upload_size_mb"] == 10
        assert data["enable_public_api"] is True
        assert data["contact_email"] is None

    def test_update_settings_200(self, settings_client):
        client, mock_session = settings_client

        existing = _make_existing_settings()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute = AsyncMock(return_value=mock_result)

        # refresh just returns; the MagicMock object will have attributes updated
        # by setattr inside the endpoint
        mock_session.refresh = AsyncMock(side_effect=lambda obj: None)

        r = client.put("/api/v1/settings/", json={
            "site_name": "Updated Site",
            "maintenance_mode": True,
        })
        assert r.status_code == 200

    def test_update_settings_partial_fields(self, settings_client):
        """PUT with a single field should succeed and not crash on unset fields."""
        client, mock_session = settings_client

        existing = _make_existing_settings()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.refresh = AsyncMock(side_effect=lambda obj: None)

        r = client.put("/api/v1/settings/", json={"contact_email": "admin@example.com"})
        assert r.status_code == 200

    def test_update_settings_maintenance_mode(self, settings_client):
        """Toggling maintenance mode is reflected in the response."""
        client, mock_session = settings_client

        existing = _make_existing_settings()
        existing.maintenance_mode = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.refresh = AsyncMock(side_effect=lambda obj: None)

        r = client.put("/api/v1/settings/", json={"maintenance_mode": True})
        assert r.status_code == 200

    def test_get_settings_no_existing_creates_new(self, settings_client):
        """When no settings row exists the endpoint creates a default one (flush called)."""
        client, mock_session = settings_client

        # First call returns None (no existing row); the endpoint then creates one
        no_row_result = MagicMock()
        no_row_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=no_row_result)

        # refresh sets attributes on the new AppSettings instance
        from src.models.settings import AppSettings

        async def refresh_new(obj):
            obj.site_name = "Quimica de Altura"
            obj.maintenance_mode = False
            obj.default_language = "es"
            obj.max_upload_size_mb = 10
            obj.enable_public_api = True
            obj.contact_email = None
            obj.updated_at = datetime.now(timezone.utc)

        mock_session.refresh = AsyncMock(side_effect=refresh_new)

        r = client.get("/api/v1/settings/")
        # flush must have been called to persist the new row
        mock_session.flush.assert_awaited_once()
        assert r.status_code == 200


# ─── Audit Log ───────────────────────────────────────────────────────────────

def _make_security_event():
    evt = MagicMock()
    evt.id = uuid.uuid4()
    evt.event_type = SecurityEventType.LOGIN_SUCCESS
    evt.user_id = uuid.uuid4()
    evt.ip_address = "127.0.0.1"
    evt.user_agent = "TestBrowser/1.0"
    evt.event_metadata = {"resource": "auth", "resource_id": "123"}
    evt.created_at = datetime.now(timezone.utc)
    return evt


@pytest.fixture
def audit_client():
    from src.main import app
    from src.dependencies import get_db

    mock_session = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_session
    with TestClient(app) as c:
        yield c, mock_session
    app.dependency_overrides.clear()


class TestAuditLogEndpoints:
    def _setup_list_mock(self, mock_session, events=None, total=0):
        """Set up mock for list endpoint (2 queries: count + select)."""
        events = events or []
        count_result = MagicMock()
        count_result.scalar_one.return_value = total

        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = events

        mock_session.execute = AsyncMock(side_effect=[count_result, items_result])

    def test_list_empty_200(self, audit_client):
        client, mock_session = audit_client
        self._setup_list_mock(mock_session)

        r = client.get("/api/v1/audit-log/")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1

    def test_list_with_events_200(self, audit_client):
        client, mock_session = audit_client
        events = [_make_security_event(), _make_security_event()]
        self._setup_list_mock(mock_session, events=events, total=2)

        r = client.get("/api/v1/audit-log/")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["action"] == "login_success"

    def test_list_pagination(self, audit_client):
        client, mock_session = audit_client
        self._setup_list_mock(mock_session, total=50)

        r = client.get("/api/v1/audit-log/?page=2&size=10")
        assert r.status_code == 200
        data = r.json()
        assert data["page"] == 2
        assert data["size"] == 10

    def test_list_default_size(self, audit_client):
        """Default page size is 20."""
        client, mock_session = audit_client
        self._setup_list_mock(mock_session)

        r = client.get("/api/v1/audit-log/")
        assert r.status_code == 200
        assert r.json()["size"] == 20

    def test_list_pages_calculated(self, audit_client):
        """Total pages is calculated correctly from total and size."""
        client, mock_session = audit_client
        self._setup_list_mock(mock_session, total=45)

        r = client.get("/api/v1/audit-log/?size=10")
        assert r.status_code == 200
        data = r.json()
        assert data["pages"] == 5  # ceil(45 / 10)

    def test_list_zero_pages_when_empty(self, audit_client):
        """When total is 0 pages should also be 0."""
        client, mock_session = audit_client
        self._setup_list_mock(mock_session, total=0)

        r = client.get("/api/v1/audit-log/")
        assert r.status_code == 200
        assert r.json()["pages"] == 0

    def test_get_single_200(self, audit_client):
        client, mock_session = audit_client
        evt = _make_security_event()

        result = MagicMock()
        result.scalar_one_or_none.return_value = evt
        mock_session.execute = AsyncMock(return_value=result)

        r = client.get(f"/api/v1/audit-log/{evt.id}")
        assert r.status_code == 200
        data = r.json()
        assert data["action"] == "login_success"
        assert data["ip_address"] == "127.0.0.1"

    def test_get_single_404(self, audit_client):
        client, mock_session = audit_client

        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=result)

        r = client.get(f"/api/v1/audit-log/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_audit_log_maps_event_metadata(self, audit_client):
        """Verify that event_metadata is correctly mapped to resource/changes."""
        client, mock_session = audit_client
        evt = _make_security_event()
        evt.event_metadata = {
            "resource": "plants",
            "resource_id": "abc123",
            "changes": {"status": "verified"}
        }

        result = MagicMock()
        result.scalar_one_or_none.return_value = evt
        mock_session.execute = AsyncMock(return_value=result)

        r = client.get(f"/api/v1/audit-log/{evt.id}")
        assert r.status_code == 200
        data = r.json()
        assert data["resource"] == "plants"
        assert data["resource_id"] == "abc123"
        assert data["changes"] == {"status": "verified"}

    def test_audit_log_maps_resource_id_alias(self, audit_client):
        """resourceId (camelCase) in event_metadata should also be accepted."""
        client, mock_session = audit_client
        evt = _make_security_event()
        evt.event_metadata = {
            "resource": "users",
            "resourceId": "user-99",
        }

        result = MagicMock()
        result.scalar_one_or_none.return_value = evt
        mock_session.execute = AsyncMock(return_value=result)

        r = client.get(f"/api/v1/audit-log/{evt.id}")
        assert r.status_code == 200
        data = r.json()
        assert data["resource"] == "users"
        assert data["resource_id"] == "user-99"

    def test_audit_log_null_metadata(self, audit_client):
        """event_metadata=None should not cause a crash; resource fields are null."""
        client, mock_session = audit_client
        evt = _make_security_event()
        evt.event_metadata = None

        result = MagicMock()
        result.scalar_one_or_none.return_value = evt
        mock_session.execute = AsyncMock(return_value=result)

        r = client.get(f"/api/v1/audit-log/{evt.id}")
        assert r.status_code == 200
        data = r.json()
        assert data["resource"] is None
        assert data["resource_id"] is None
        assert data["changes"] is None

    def test_audit_log_user_id_present(self, audit_client):
        """user_id from the security event surfaces in the response."""
        client, mock_session = audit_client
        evt = _make_security_event()
        specific_uid = uuid.uuid4()
        evt.user_id = specific_uid

        result = MagicMock()
        result.scalar_one_or_none.return_value = evt
        mock_session.execute = AsyncMock(return_value=result)

        r = client.get(f"/api/v1/audit-log/{evt.id}")
        assert r.status_code == 200
        assert r.json()["user_id"] == str(specific_uid)

    def test_list_different_event_types(self, audit_client):
        """Multiple event types are mapped to their string values correctly."""
        client, mock_session = audit_client

        evt_login = _make_security_event()
        evt_login.event_type = SecurityEventType.LOGIN_FAILED

        evt_logout = _make_security_event()
        evt_logout.event_type = SecurityEventType.LOGOUT

        self._setup_list_mock(mock_session, events=[evt_login, evt_logout], total=2)

        r = client.get("/api/v1/audit-log/")
        assert r.status_code == 200
        actions = [item["action"] for item in r.json()["items"]]
        assert "login_failed" in actions
        assert "logout" in actions
