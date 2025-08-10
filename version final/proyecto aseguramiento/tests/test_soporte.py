# tests/test_soporte.py
from bson.objectid import ObjectId
import app as app_module

def test_soporte_asigna_y_resuelve(client, user_soporte, user_cliente):
    # crear ticket de cliente
    t = {
        "cliente": "cliente1",
        "tema": "Sin señal",
        "descripcion": "no tengo internet",
        "status": "abierto",
        "priority": "media",
        "asignado_a": None,
        "history": []
    }
    t_id = app_module.tickets.insert_one(t).inserted_id

    # login soporte
    client.post("/login", data={"username": "tecnico1", "password": "secret"}, follow_redirects=True)

    # asignarme (sin 'action' => rama asignación)
    r = client.post("/dashboard", data={"ticket_id": str(t_id), "priority": "alta"}, follow_redirects=True)
    assert r.status_code == 200

    # resolver con solución
    r = client.post("/dashboard",
                    data={"ticket_id": str(t_id),
                          "action": "resolver",
                          "solution": "Se reinició router y quedó OK."},
                    follow_redirects=True)
    assert r.status_code == 200

    doc = app_module.tickets.find_one({"_id": ObjectId(t_id)})
    assert doc["status"] == "resuelto"
    # Debe existir la solución en el history
    assert any(h.get("solution") for h in doc.get("history", []))
