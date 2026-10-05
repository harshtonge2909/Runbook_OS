def test_api_login(client, engineer_user):
    response = client.post("/api/auth/login", json={
        "email": engineer_user.email,
        "password": "EngineerPass123!"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "token" in data["data"]


def test_api_get_runbooks_with_bearer_token(client, engineer_token):
    response = client.get("/api/runbooks", headers={
        "Authorization": f"Bearer {engineer_token}"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "runbooks" in data["data"]


def test_api_create_runbook(client, engineer_token):
    response = client.post("/api/runbooks", headers={
        "Authorization": f"Bearer {engineer_token}"
    }, json={
        "title": "API Created Runbook",
        "description": "Created via Flask REST API endpoint",
        "steps": [
            {
                "order": 1,
                "title": "API Step 1",
                "instructions": "uptime",
                "expectedOutcome": "load average < 2.0"
            }
        ]
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["title"] == "API Created Runbook"


def test_api_dashboard_stats(client, engineer_token):
    response = client.get("/api/dashboard/stats", headers={
        "Authorization": f"Bearer {engineer_token}"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "totalRunbooks" in data["data"]
    assert "totalUsers" in data["data"]


def test_api_audit_logs(client, admin_token):
    response = client.get("/api/audit", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
