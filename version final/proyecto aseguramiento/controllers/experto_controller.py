from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app
from datetime import datetime
from pyswip import Prolog
import os

experto_bp = Blueprint('experto', __name__, url_prefix='/experto')

# -------- Helpers de acceso a BD ----------
def _db():
    client = current_app.config['MONGO_CLIENT']
    return client['ticketdb']

def _notifications():
    return _db()['notifications']

def _tickets():
    return _db()['tickets']

def notif_count_for(user):
    return _notifications().count_documents({"user": user, "read": False})

# -------- Carga de Prolog (una sola vez) ----------
PROLOG = Prolog()
PROLOG_LOADED = False

def ensure_prolog_loaded():
    """Consulta el archivo sistemaexperto.pl una sola vez, usando ruta absoluta segura."""
    global PROLOG_LOADED
    if PROLOG_LOADED:
        return
    base = current_app.root_path  # raíz del proyecto (donde está app.py)
    pl_path = os.path.join(base, 'sistemaexperto', 'sistemaexperto.pl')
    if not os.path.exists(pl_path):
        raise FileNotFoundError(f"No se encontró el sistema experto: {pl_path}")
    PROLOG.consult(pl_path)
    PROLOG_LOADED = True

# -------- Rutas ----------
@experto_bp.get('/chat')
def chat():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    return render_template(
        'experto_chat.html',
        first_name=session.get('first_name', ''),
        last_name=session.get('last_name', ''),
        notif_count=notif_count_for(user),
        # Pasamos la URL real del POST al template para evitar 404 de rutas
        chat_post_url=url_for('experto.chat_experto')
    )

@experto_bp.post('/chat-experto')
def chat_experto():
    if 'user' not in session:
        return jsonify({"respuesta": "No autenticado."}), 401

    data = request.get_json(silent=True) or {}
    descripcion = (data.get('descripcion') or '').strip().lower()
    if not descripcion:
        return jsonify({"respuesta": "Por favor escribe tu problema."}), 400

    ensure_prolog_loaded()

    # Sanitizar comillas para consulta Prolog
    qtext = descripcion.replace("'", "\\'")
    respuesta = None
    for r in PROLOG.query(f"responder('{qtext}', R).", maxresult=1):
        respuesta = r.get('R')
        break

    # Fallback: si no hay respuesta, avisar y escalar
    if not respuesta:
        respuesta = ("No tengo una solución automática para tu caso. "
                     "He generado una notificación y un técnico te ayudará pronto.")

        # Notificar al cliente
        _notifications().insert_one({
            "user": session['user'],
            "message": f"Tu consulta '{descripcion}' fue derivada a soporte.",
            "read": False,
            "created_at": datetime.utcnow()
        })

        # Elevar prioridad del último ticket abierto del cliente (si existe)
        t = _tickets().find_one(
            {"cliente": session['user'], "status": "abierto"},
            sort=[('_id', -1)]
        )
        if t:
            _tickets().update_one(
                {"_id": t["_id"]},
                {"$set": {"priority": "alta"},
                 "$push": {"history": {"actor": "sistema_experto",
                                       "action": "sugirió escalamiento a soporte",
                                       "at": datetime.utcnow()}}}
            )

    return jsonify({"respuesta": str(respuesta)})
