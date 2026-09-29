def test_dashboard_is_open_without_login(client):
    assert client.get("/").status_code == 200


def test_login_routes_were_removed(client):
    assert client.get("/login").status_code == 404
    assert client.get("/logout").status_code == 404


def test_timeline_endpoint(client):
    payload = client.get("/api/timeline").get_json()
    assert len(payload["points"]) == 4
    assert len(payload["visits"]) == 1
    assert len(payload["activities"]) == 1


def test_preview_rejects_path_traversal(client):
    assert client.get("/api/images/..%2F..%2Fapp%2Fconfig.py").status_code == 404
