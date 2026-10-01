def payload():
    return {
        "email": "amal@example.com",
        "student_number": "E2022-001",
        "graduation_year": 2022,
        "program": "Génie numérique",
        "employment_status": "Ingénieure Data",
        "city": "Casablanca",
        "country": "Maroc",
        "consent": True,
    }


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_profile_workflow_and_dashboard(client):
    created = client.post("/api/profiles", json=payload())
    assert created.status_code == 201
    profile_id = created.json()["id"]
    assert created.json()["status"] == "PENDING"

    listed = client.get("/api/profiles", headers={"X-Role": "SERVICE"})
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    reviewed = client.post(
        f"/api/profiles/{profile_id}/review",
        json={"decision": "APPROVED", "comment": "Profil complet"},
        headers={"X-Role": "SERVICE"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "VALIDATED"

    dashboard = client.get("/api/dashboard", headers={"X-Role": "DIRECTION"})
    assert dashboard.status_code == 200
    assert dashboard.json()["validated_count"] == 1


def test_duplicate_and_missing_consent_are_rejected(client):
    no_consent = payload() | {"consent": False}
    assert client.post("/api/profiles", json=no_consent).status_code == 422
    assert client.post("/api/profiles", json=payload()).status_code == 201
    assert client.post("/api/profiles", json=payload()).status_code == 409


def test_role_access_is_enforced(client):
    response = client.get("/api/profiles", headers={"X-Role": "ALUMNI"})
    assert response.status_code == 403
