from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api import app
from app.auth import COOKIE, hash_password
from app.database import SessionLocal
from app.models import AuditLog, AuthSession, Role, User, ValidationReview

PASSWORD = "Test-password-2026"


def account(client, role=Role.ALUMNI, email="amal@example.com"):
    with SessionLocal() as db:
        user = User(email=email, password_hash=hash_password(PASSWORD), role=role)
        db.add(user)
        db.commit()
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return response


def payload():
    return dict(
        full_name="Amal El Idrissi",
        student_number="E2022-001",
        graduation_year=2022,
        program="Génie numérique",
        employment_status="Ingénieure Data",
        city="Casablanca",
        country="Maroc",
        company="Atlas Digital",
        sector="Numérique",
        consent=True,
    )


def test_registration_cannot_choose_privileged_role(client):
    response = client.post(
        "/api/auth/register", json={"email": "new@example.com", "password": PASSWORD, "role": "ADMIN"}
    )
    assert response.status_code == 201
    assert response.json()["role"] == "ALUMNI"
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "samesite=strict" in response.headers["set-cookie"].lower()
    assert client.get("/api/profiles", headers={"X-Role": "ADMIN"}).status_code == 403


def test_headers_do_not_authenticate(client):
    assert client.get("/api/profiles", headers={"X-Role": "ADMIN"}).status_code == 401
    assert client.post("/api/profiles", json=payload()).status_code == 401


def test_complete_persistent_workflow_and_revocation(client):
    account(client)
    created = client.put("/api/me/profile", json=payload())
    assert created.status_code == 200, created.text
    profile_id = created.json()["id"]
    assert created.json()["status"] == "PENDING"
    assert client.get("/api/directory").json() == []
    alumni_cookie = client.cookies.get(COOKIE)
    with TestClient(app) as service:
        account(service, Role.SERVICE, "service@example.com")
        review = f"/api/profiles/{profile_id}/review"
        assert service.post(review, json={"decision": "APPROVED"}).status_code == 422
        assert service.post(review, json={"decision": "CORRECTION", "comment": ""}).status_code == 422
        assert (
            service.post(review, json={"decision": "CORRECTION", "comment": "Vérifier le métier"}).status_code
            == 200
        )
        assert client.get("/api/me/profile").json()["review"]["comment"] == "Vérifier le métier"
        assert client.put("/api/me/profile", json=payload()).status_code == 200
        assert service.post(f"/api/profiles/{profile_id}/duplicates/checked").status_code == 200
        assert service.post(review, json={"decision": "APPROVED"}).json()["status"] == "VALIDATED"
        stats = service.get("/api/dashboard").json()
        assert stats["validated_count"] == 1
        assert stats["median_days"] is not None
        # Another HTTP session reads the same persisted data, with only public fields exposed.
        rows = client.get("/api/directory?q=Amal&country=Maroc&graduation_year=2022").json()
        assert len(rows) == 1
        assert "email" not in rows[0] and "student_number" not in rows[0] and "review" not in rows[0]
        assert client.post("/api/me/consent/revoke").status_code == 200
        assert service.get("/api/directory").json() == []
        assert service.get("/api/dashboard").json()["validated_count"] == 0
        assert service.post(review, json={"decision": "APPROVED"}).status_code == 422
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.set(COOKIE, alumni_cookie)
    assert client.get("/api/auth/me").status_code == 401
    with SessionLocal() as db:
        assert len(list(db.scalars(select(ValidationReview)))) == 2
        assert "CONSENT_REVOKED" in [a.action for a in db.scalars(select(AuditLog))]


@pytest.mark.parametrize("role", [Role.DIRECTION, Role.ALUMNI])
def test_non_service_cannot_review_or_export(client, role):
    account(client, role)
    assert client.post("/api/profiles/missing/review", json={"decision": "APPROVED"}).status_code == 403
    assert client.get("/api/export").status_code == 403
    assert client.get("/api/audit").status_code == 403


def test_profile_is_owned_by_logged_in_account(client):
    account(client)
    own_id = client.put("/api/me/profile", json=payload()).json()["id"]
    with TestClient(app) as other:
        account(other, email="other@example.com")
        assert other.get("/api/me/profile").json() is None
        assert other.put("/api/me/profile", json=payload()).status_code == 409
        assert (
            other.put("/api/me/profile", json=payload() | {"student_number": "E2022-002"}).status_code == 200
        )
        assert other.get("/api/me/profile").json()["id"] != own_id
    assert client.get("/api/me/profile").json()["id"] == own_id


def test_import_and_export_permissions_and_formula_neutralization(client):
    account(client, Role.ADMIN)
    data = payload() | {"email": "import@example.com", "consent": False, "company": "=1+1"}
    assert client.post("/api/profiles", json=data | {"consent": True}).status_code == 422
    assert client.post("/api/profiles", json=data).status_code == 201
    assert client.post("/api/profiles", json=data).status_code == 409
    exported = client.get("/api/export?country=Maroc")
    assert exported.status_code == 200
    assert "'=1+1" in exported.text
    assert "import@example.com" not in client.get("/api/export?country=France").text
    assert client.get("/api/directory").json() == []


def test_invalid_expired_and_logged_out_sessions(client):
    account(client)
    with SessionLocal() as db:
        session = db.scalar(select(AuthSession))
        session.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)
        db.commit()
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.set(COOKIE, "invalid.jwt.token")
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.clear()
    assert (
        client.post(
            "/api/auth/login", json={"email": "amal@example.com", "password": "wrong-password"}
        ).status_code
        == 401
    )


def test_campaign_targets_only_old_profiles_and_tracks_confirmation(client):
    account(client)
    client.put("/api/me/profile", json=payload())
    with SessionLocal() as db:
        from app.models import AlumniProfile

        profile = db.scalar(select(AlumniProfile))
        profile.last_confirmed_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=400)
        db.commit()
    with TestClient(app) as service:
        account(service, Role.SERVICE, "service@example.com")
        response = service.post(
            "/api/campaigns", json={"name": "Relance annuelle", "message": "Merci de confirmer votre profil."}
        )
        assert response.status_code == 201
        assert response.json()["recipient_count"] == 1
        assert service.get("/api/campaigns").json()[0]["responses"] == 0
        client.put("/api/me/profile", json=payload())
        assert service.get("/api/campaigns").json()[0]["responses"] == 1
