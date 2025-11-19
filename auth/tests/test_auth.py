
def test_register_success(client):
    response = client.post("/auth/register", json={
        "username": "alg",
        "email": "alg.alg@alg.ru",
        "password": "12345678",
    })
    assert response.status_code == 200
    assert response.json() == {"message": "User successfully created"}


def test_register_duplicate_username(client, fake_db):
    response = client.post("/auth/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "secrettt",
    })
    assert response.status_code == 400
    assert "already registered" in response.text

