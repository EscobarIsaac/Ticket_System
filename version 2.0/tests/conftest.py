import os, sys
# Inserta el directorio padre (donde está app.py) en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import app as flask_app
from pymongo import MongoClient
import certifi

# URI de tu clúster Atlas (pruebas)
TEST_MONGO_URI = "mongodb+srv://isaac:isaac@pruebas.oryf5lt.mongodb.net/?retryWrites=true&w=majority&appName=Pruebas"

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })

    client = MongoClient(TEST_MONGO_URI, tls=True, tlsCAFile=certifi.where())
    flask_app.db = client["ticketdb_test"]
    flask_app.users = flask_app.db["users"]
    flask_app.tickets = flask_app.db["tickets"]

    flask_app.users.delete_many({})
    flask_app.tickets.delete_many({})

    yield flask_app

    client.drop_database("ticketdb_test")

@pytest.fixture
def client(app):
    return app.test_client()
