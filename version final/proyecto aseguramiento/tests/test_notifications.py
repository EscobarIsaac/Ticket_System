# tests/test_notifications.py
import app as app_module
from datetime import datetime

def test_notifications_mark_read(client, user_cliente):
    # Inyectar notificaciones
    app_module.notifications.insert_many([
        {"user": "cliente1", "message": "n1", "read": False, "created_at": datetime.utcnow()},
        {"user": "cliente1", "message": "n2", "read": False, "created_at": datetime.utcnow()},
    ])

    client.post("/login", data={"username": "cliente1", "password": "secret"}, follow_redirects=True)
    r = client.get("/notifications")
    assert r.status_code == 200

    # Se marcan como leídas
    unread = app_module.notifications.count_documents({"user": "cliente1", "read": False})
    assert unread == 0
