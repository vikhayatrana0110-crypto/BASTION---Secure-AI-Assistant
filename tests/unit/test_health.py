from fastapi.testclient import TestClient

from bastion.main import create_app


def test_healthz():
    client = TestClient(create_app())

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}