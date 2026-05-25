from fastapi.testclient import TestClient


def test_create_department(client: TestClient):
    response = client.post("departments/", json={"name": "test"})
    assert response.status_code == 201
