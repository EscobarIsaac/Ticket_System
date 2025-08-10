# tests/conftest.py
import os
import sys
import pytest
import mongomock
from datetime import datetime
from bson.objectid import ObjectId

# --- AÑADIR RAÍZ DEL PROYECTO AL sys.path ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import app as app_module  # ahora sí encuentra app.py en la raíz


@pytest.fixture(scope="session")
def test_app():
    # Forzamos modo testing
    app_module.app.config['TESTING'] = True

    # Crear cliente Mongo en memoria y reemplazar colecciones globales
    mock_client = mongomock.MongoClient()
    mock_db = mock_client['ticketdb']

    app_module.client = mock_client
    app_module.db = mock_db
    app_module.users = mock_db['users']
    app_module.tickets = mock_db['tickets']
    app_module.notifications = mock_db['notifications']

    yield app_module.app


@pytest.fixture()
def client(test_app):
    # Limpia colecciones antes de cada test
    app_module.users.delete_many({})
    app_module.tickets.delete_many({})
    app_module.notifications.delete_many({})
    return test_app.test_client()


# ---------- Helpers de fábrica de datos ----------

def create_user(role="cliente", username="user1", password="secret", first="Ana", last="Pérez"):
    from werkzeug.security import generate_password_hash
    return {
        "first_name": first,
        "last_name": last,
        "username": username,
        "pass_hash": generate_password_hash(password),
        "role": role,
        "registered_at": datetime.utcnow(),
        "date_of_birth": datetime(1990, 1, 1),
        "gender": "femenino"
    }

@pytest.fixture()
def user_cliente():
    u = create_user(role="cliente", username="cliente1")
    app_module.users.insert_one(u)
    return u

@pytest.fixture()
def user_soporte():
    u = create_user(role="soporte", username="tecnico1", first="Luis", last="García")
    app_module.users.insert_one(u)
    return u

@pytest.fixture()
def user_admin():
    u = create_user(role="superadmin", username="admin1", first="Root", last="Admin")
    app_module.users.insert_one(u)
    return u


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)


def create_ticket(cliente_username="cliente1", tema="Sin señal en casa", descripcion="no tengo internet"):
    t = {
        "cliente": cliente_username,
        "tema": tema,
        "descripcion": descripcion,
        "status": "abierto",
        "priority": "media",
        "asignado_a": None,
        "history": [{"actor": cliente_username, "action": "creó ticket", "at": datetime.utcnow()}]
    }
    res = app_module.tickets.insert_one(t)
    t["_id"] = res.inserted_id
    return t
