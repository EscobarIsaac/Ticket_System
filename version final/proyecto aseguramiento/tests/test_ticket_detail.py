# tests/test_ticket_detail.py
from bson.objectid import ObjectId

def test_ticket_detail_404(client, user_cliente):
    client.post("/login", data={"username": "cliente1", "password": "secret"}, follow_redirects=True)
    fake_id = str(ObjectId())
    r = client.get(f"/ticket/{fake_id}")
    # En tu app devuelve "Ticket no existe", 404
    assert r.status_code in (200, 404)  # por si template envuelve
    assert b"Ticket no existe" in r.data or r.status_code == 404
