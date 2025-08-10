from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from datetime import datetime
from bson.objectid import ObjectId

cliente_bp = Blueprint('cliente', __name__, url_prefix='/cliente')

# --- Helpers de acceso a BD ---
def _db():
    client = current_app.config['MONGO_CLIENT']
    return client['ticketdb']

def _tickets():
    return _db()['tickets']

def _notifications():
    return _db()['notifications']

def notif_count_for(user):
    return _notifications().count_documents({"user": user, "read": False})

def add_notification(username, message):
    _notifications().insert_one({
        "user": username,
        "message": message,
        "read": False,
        "created_at": datetime.utcnow()
    })

# --- Dashboard del cliente: ver + crear tickets ---
@cliente_bp.route('/', methods=['GET', 'POST'])
def dashboard_cliente():
    if 'user' not in session or session.get('role') != 'cliente':
        return redirect(url_for('login'))

    usr = session['user']
    fn  = session.get('first_name', '')
    ln  = session.get('last_name', '')

    if request.method == 'POST':
        tema = (request.form.get('tema') or '').strip()
        desc = (request.form.get('descripcion') or '').strip()

        if not tema or not desc:
            flash("Completa tema y descripción.", "error")
            return redirect(url_for('cliente.dashboard_cliente'))

        # Insertar ticket
        _tickets().insert_one({
            "cliente": usr,
            "tema": tema,
            "descripcion": desc,
            "status": "abierto",
            "priority": "media",
            "asignado_a": None,
            "created_at": datetime.utcnow(),
            "history": [{
                "actor": usr,
                "action": "creó ticket",
                "at": datetime.utcnow()
            }]
        })
        flash("Ticket creado correctamente.", "success")
        add_notification(usr, f"Tu ticket “{tema}” ha sido creado.")
        return redirect(url_for('cliente.dashboard_cliente'))

    # Listado de mis tickets (últimos primero)
    my_tickets = list(_tickets().find({"cliente": usr}).sort("created_at", -1))
    return render_template(
        'dashboard_cliente.html',
        first_name=fn, last_name=ln,
        tickets=my_tickets,
        notif_count=notif_count_for(usr)
    )

# --- Detalle del ticket ---
@cliente_bp.get('/ver/<tid>')
def ticket_detail(tid):
    if 'user' not in session or session.get('role') != 'cliente':
        return redirect(url_for('login'))

    t = _tickets().find_one({"_id": ObjectId(tid), "cliente": session['user']})
    if not t:
        flash("Ticket no encontrado.", "error")
        return redirect(url_for('cliente.dashboard_cliente'))

    return render_template(
        'ticket_detail.html',
        ticket=t,
        first_name=session.get('first_name', ''),
        last_name=session.get('last_name', '')
    )
