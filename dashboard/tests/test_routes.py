def login(client, code):
    return client.post("/login", data={"code": code})


def test_login_page_is_public(client):
    assert client.get("/login").status_code == 200


def test_dashboard_redirects_without_session(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_login_with_correct_code(client):
    response = login(client, "1234")
    assert response.status_code == 302
    assert client.get("/").status_code == 200


def test_login_with_wrong_code(client):
    assert login(client, "0000").status_code == 401


def test_login_locks_after_five_failures(client):
    statuses = [login(client, "0000").status_code for _ in range(5)]
    assert statuses == [401, 401, 401, 401, 429]
    assert login(client, "1234").status_code == 429


def test_logout_clears_session(logged_client):
    logged_client.get("/logout")
    assert logged_client.get("/").status_code == 302


def test_api_requires_session(client):
    for response in (client.get("/api/timeline"), client.post("/api/terminal", json={"command": "help"})):
        assert response.status_code == 401
        assert response.get_json() == {"error": "unauthorized"}


def test_timeline_endpoint(logged_client):
    payload = logged_client.get("/api/timeline").get_json()
    assert len(payload["points"]) == 4
    assert len(payload["visits"]) == 1
    assert len(payload["activities"]) == 1


def test_preview_rejects_path_traversal(logged_client):
    assert logged_client.get("/api/images/..%2F..%2Fapp%2Fconfig.py").status_code == 404
