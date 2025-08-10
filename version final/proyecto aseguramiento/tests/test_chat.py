# tests/test_chat.py
import json
from bson.objectid import ObjectId
import app as app_module

def _post_chat(client, payload):
    return client.post("/chat-experto", data=json.dumps(payload), content_type="application/json")

def test_chat_greeting_and_steps(client, user_cliente):
    # login
    client.post("/login", data={"username": "cliente1", "password": "secret"}, follow_redirects=True)

    # crear ticket
    t = app_module.tickets.insert_one({
        "cliente": "cliente1",
        "tema": "Sin señal en casa",
        "descripcion": "no tengo internet",
        "status": "abierto",
        "priority": "media",
        "asignado_a": None,
        "history": []
    }).inserted_id

    # saludo con ticket seleccionado
    r = _post_chat(client, {"ticketId": str(t), "tema": "Sin señal", "descripcion": "hola"})
    assert r.status_code == 200
    data = r.get_json()
    assert "Hola" in data["respuesta"] or "hola" in data["respuesta"]

    # pedir pasos iniciales
    r = _post_chat(client, {"descripcion": "ayuda"})
    assert r.status_code == 200
    assert "Pasos sugeridos" in r.get_json()["respuesta"]

def test_chat_no_funciono_escalado(client, user_cliente):
    client.post("/login", data={"username": "cliente1", "password": "secret"}, follow_redirects=True)
    t = app_module.tickets.insert_one({
        "cliente": "cliente1",
        "tema": "Conexión lenta",
        "descripcion": "lento",
        "status": "abierto",
        "priority": "media",
        "asignado_a": None,
        "history": []
    }).inserted_id

    # seleccionar ticket
    _post_chat(client, {"ticketId": str(t), "tema": "Conexión lenta", "descripcion": "hola"})

    # Avanzar por pasos hasta escalar (4 pasos)
    for _ in range(4):
        r = _post_chat(client, {"descripcion": "no funciono"})
    data = r.get_json()
    # después de agotar pasos, debería escalar
    assert "escalar" in data["respuesta"].lower() or "técnico" in data["respuesta"].lower()

def test_chat_solucionado_cierra_ticket(client, user_cliente):
    client.post("/login", data={"username": "cliente1", "password": "secret"}, follow_redirects=True)
    t = app_module.tickets.insert_one({
        "cliente": "cliente1",
        "tema": "Wifi no conecta",
        "descripcion": "no conecta",
        "status": "abierto",
        "priority": "media",
        "asignado_a": None,
        "history": []
    }).inserted_id

    # seleccionar ticket
    _post_chat(client, {"ticketId": str(t), "tema": "wifi no conecta", "descripcion": "hola"})
    # marcar solucionado
    r = _post_chat(client, {"descripcion": "solucionado"})
    assert r.status_code == 200
    data = r.get_json()
    assert "cerrado" in data["respuesta"].lower() or "resuelto" in data["respuesta"].lower()

    # ticket debe estar resuelto
    tdoc = app_module.tickets.find_one({"_id": ObjectId(t)})
    assert tdoc["status"] == "resuelto"

def test_chat_ticket_ya_resuelto(client, user_cliente):
    client.post("/login", data={"username": "cliente1", "password": "secret"}, follow_redirects=True)
    t = app_module.tickets.insert_one({
        "cliente": "cliente1",
        "tema": "Algo",
        "descripcion": "desc",
        "status": "resuelto",
        "priority": "media",
        "asignado_a": None,
        "history": []
    }).inserted_id

    r = _post_chat(client, {"ticketId": str(t), "tema": "otro", "descripcion": "hola"})
    data = r.get_json()
    assert "ya está resuelto" in data["respuesta"].lower() or "ya esta resuelto" in data["respuesta"].lower()
