from fastapi.testclient import TestClient


def test_frontend_index_is_served_after_api_routes(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert '<main id="app" class="content" tabindex="-1"></main>' in response.text
