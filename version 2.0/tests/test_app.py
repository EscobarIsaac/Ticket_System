import pytest
from datetime import datetime, timedelta

def register(client, **data):
    return client.post("/register", data=data, follow_redirects=True)

def login(client, username, password):
    return client.post("/login",
                       data={"username": username, "password": password},
                       follow_redirects=True)

def test_register_and_login(client):
    dob = (datetime.utcnow() - timedelta(days=365*20)).strftime("%Y-%m-%d")
    rv = register(client,
                  first_name="María",
                  last_name="López",
                  username="marial",
                  password="pass1234",
                  date_of_birth=dob,
                  gender="femenino")
    text = rv.get_data(as_text=True)
    assert "Registro exitoso" in text

    rv = login(client, "marial", "pass1234")
    text = rv.get_data(as_text=True)
    assert "Bienvenido" in text

def test_protected_dashboard_requires_login(client):
    rv = client.get("/dashboard", follow_redirects=True)
    text = rv.get_data(as_text=True)
    assert "Ingresar" in text
    assert "Usuario" in text

def test_invalid_login_shows_error(client):
    rv = login(client, "sinuser", "1234")
    text = rv.get_data(as_text=True)
    assert "Credenciales inválidas" in text

def test_ticket_creation_and_listing(client):
    dob = (datetime.utcnow() - timedelta(days=365*25)).strftime("%Y-%m-%d")
    register(client, first_name="Luis", last_name="García",
             username="luisg", password="secret12",
             date_of_birth=dob, gender="masculino")
    login(client, "luisg", "secret12")

    rv = client.post("/dashboard", data={
        "tema": "Conexión lenta",
        "descripcion": "La red va muy lenta por las tardes"
    }, follow_redirects=True)
    text = rv.get_data(as_text=True)
    assert "Mis tickets" in text
    assert "Conexión lenta" in text

def test_logout_and_back_button(client):
    dob = (datetime.utcnow() - timedelta(days=365*30)).strftime("%Y-%m-%d")
    register(client, first_name="Ana", last_name="Morales",
             username="anam", password="pwd12345",
             date_of_birth=dob, gender="femenino")
    login(client, "anam", "pwd12345")

    # Logout
    client.get("/logout", follow_redirects=True)

    # Simula pulsar atrás: accede de nuevo a /dashboard
    rv = client.get("/dashboard", follow_redirects=True)
    text = rv.get_data(as_text=True)
    # Debe mostrar el formulario de login de nuevo
    assert "Ingresar" in text
    assert "Contraseña" in text

