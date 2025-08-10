# tests/test_auth.py
from datetime import datetime

def test_register_and_login_flow(client):
    # GET register
    r = client.get("/register")
    assert r.status_code == 200

    # POST register
    form = {
        "first_name": "Isaac",
        "last_name": "Escobar",
        "username": "isaac",
        "password": "123456",
        "date_of_birth": "1999-01-01",
        "gender": "masculino"
    }
    r = client.post("/register", data=form, follow_redirects=True)
    assert r.status_code == 200
    # Después de registro redirige a login y muestra algo
    assert b"Iniciar Sesi" in r.data or b"Has iniciado sesi" in r.data or b"Registro exitoso" in r.data

    # Credenciales incorrectas
    r = client.post("/login", data={"username": "isaac", "password": "bad"}, follow_redirects=True)
    assert b"Credenciales inv" in r.data

    # Login correcto
    r = client.post("/login", data={"username": "isaac", "password": "123456"}, follow_redirects=True)
    assert r.status_code == 200
    assert b"Dashboard" in r.data or b"Tickets" in r.data
