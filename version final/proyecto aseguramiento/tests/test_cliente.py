# tests/test_cliente.py
import app as app_module

def test_cliente_crea_ticket(client, user_cliente):
    # Login
    r = client.post("/login", data={"username": "cliente1", "password": "secret"}, follow_redirects=True)
    assert r.status_code == 200

    # Crear ticket
    form = {"tema": "Conexión lenta", "descripcion": "va muy lento"}
    r = client.post("/dashboard", data=form, follow_redirects=True)
    assert r.status_code == 200

    # Verifica en DB
    tcount = app_module.tickets.count_documents({"cliente": "cliente1"})
    assert tcount == 1
