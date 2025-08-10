from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pyswip import Prolog  # Usamos solo Prolog (evitar PrologError import)
import certifi
import os
import re

# -------------------------------------------------
# Cargar variables de entorno
# -------------------------------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'clave_segura_por_defecto')

# -------------------------------------------------
# Conexión MongoDB
# -------------------------------------------------
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://isaac:isaac1@cluster0.uu8wq4u.mongodb.net/ticketdb?retryWrites=true&w=majority"
)
client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client['ticketdb']
users = db['users']
tickets = db['tickets']
notifications = db['notifications']

# -------------------------------------------------
# Validadores / Utilidades
# -------------------------------------------------
NAME_REGEX = re.compile(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,50}$')

def add_notification(username, message):
    """Crear notificación para un usuario."""
    notifications.insert_one({
        "user": username,
        "message": message,
        "read": False,
        "created_at": datetime.utcnow()
    })

def first_name_of(username: str) -> str:
    u = users.find_one({"username": username})
    if not u:
        return username
    # preferir first_name si existe
    if u.get("first_name"):
        return u["first_name"].split(" ")[0]
    # o partir username
    return username.split(".")[0]

# -------------------------------------------------
# Prolog (carga del archivo .pl)
# -------------------------------------------------
PROLOG = None

def init_prolog():
    """Inicializa Prolog y carga el archivo .pl evitando el problema de backslashes en Windows."""
    global PROLOG
    try:
        PROLOG = Prolog()

        # Definir directorio del proyecto y convertir a slash (POSIX)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        posix_base = base_dir.replace("\\", "/")

        # Establecer directorio de trabajo para Prolog
        wd_query = f"working_directory(_, '{posix_base}')"
        list(PROLOG.query(wd_query))

        # Cargar el archivo relativo (con / siempre)
        rel_path = "sistema_experto/sistemaexperto.pl"
        list(PROLOG.query(f"consult('{rel_path}')"))
        print("[Prolog] Cargado:", rel_path)
    except Exception as e:
        # Prolog es opcional: el chat sigue funcionando con reglas en Python
        print("[Prolog] No se pudo cargar el archivo .pl:", e)

init_prolog()

# -------------------------------------------------
# Reglas del Asistente (Python) – por tema
# -------------------------------------------------
SUGERENCIAS = {
    "sin señal": [
        "Verifica que el router esté encendido y con LEDs normales.",
        "Revisa que el proveedor de Internet no tenga incidencia en tu zona.",
        "Apaga y enciende el router (30–60 segundos).",
        "Prueba con otra red (hotspot) para descartar tu equipo."
    ],
    "caída de red": [
        "Comprueba que el cable WAN/ONT esté firme y sin daño.",
        "Reinicia el modem/ONT y espera 30–60 segundos.",
        "Verifica luces del router: Internet/DSL en verde fijo.",
        "Si hay microcortes, prueba otro cable de red."
    ],
    "conexión lenta": [
        "Cierra descargas/streaming y repite un test de velocidad.",
        "Reinicia el router y coloca el equipo cerca del punto de acceso.",
        "Usa cable en lugar de WiFi para descartar interferencias.",
        "Comprueba que no haya VPN o proxy activados."
    ],
    "wifi no conecta": [
        "Olvida la red y vuelve a conectarte (escribe de nuevo la clave).",
        "Reinicia el router y tu equipo (PC/Móvil).",
        "Prueba en 2.4GHz y 5GHz (si tu router lo soporta).",
        "Cambia el canal del WiFi para evitar interferencias."
    ],
    "otro": [
        "Confirma el mensaje o error exacto que ves.",
        "Indica si el problema pasa en más de un equipo.",
        "Comprueba si con otra red funciona correctamente.",
        "Reinicia el equipo y prueba otra vez."
    ],
}

SALUDOS = {"hola","buenas","buenos días","buenas tardes","buenas noches","que tal","qué tal","saludos"}

def normaliza_txt(s: str) -> str:
    s = s.lower().strip()
    s = s.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
    return s

def tema_normalizado(tema: str) -> str:
    t = normaliza_txt(tema)
    if "senal" in t: return "sin señal"
    if "caida" in t or "caída" in t: return "caída de red"
    if "lenta" in t: return "conexión lenta"
    if "wifi" in t and ("no conecta" in t or "conecta" in t): return "wifi no conecta"
    return "otro"

# -------------------------------------------------
# Rutas base
# -------------------------------------------------
@app.route('/')
def index():
    return redirect(url_for('login'))

# ------------------ Registro ---------------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        first = request.form['first_name'].strip()
        last = request.form['last_name'].strip()
        username = request.form['username'].strip()
        password = request.form['password']
        dob_str = request.form['date_of_birth']
        gender = request.form['gender']
        role = 'cliente'

        if not NAME_REGEX.match(first):
            flash("Nombre inválido.", "error"); return redirect(url_for('register'))
        if not NAME_REGEX.match(last):
            flash("Apellido inválido.", "error"); return redirect(url_for('register'))
        if users.find_one({"username": username}):
            flash("Usuario ya existe", "error"); return redirect(url_for('register'))
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
        except ValueError:
            flash("Fecha de nacimiento inválida", "error"); return redirect(url_for('register'))
        if dob > datetime.utcnow() - timedelta(days=18*365+4):
            flash("Debes tener al menos 18 años.", "error"); return redirect(url_for('register'))

        users.insert_one({
            "first_name": first, "last_name": last, "username": username,
            "pass_hash": generate_password_hash(password),
            "role": role, "registered_at": datetime.utcnow(),
            "date_of_birth": dob, "gender": gender
        })
        add_notification(username, "Bienvenido al sistema de tickets.")
        flash("Registro exitoso.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# ------------------- Login -----------------------
@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        u = request.form['username'].strip()
        p = request.form['password']
        usr = users.find_one({"username": u})
        if usr and check_password_hash(usr['pass_hash'], p):
            session['user'] = u
            session['role'] = usr['role']
            session['first_name'] = usr.get('first_name','')
            session['last_name'] = usr.get('last_name','')
            add_notification(u, "Iniciaste sesión correctamente.")
            flash("Has iniciado sesión.", "success")
            return redirect(url_for('dashboard'))
        error = "Credenciales inválidas"
    return render_template('login.html', error=error)

# ------------------ Dashboard --------------------
@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    usr   = session['user']
    role  = session['role']
    fn    = session.get('first_name','')
    ln    = session.get('last_name','')
    notif_count = notifications.count_documents({"user": usr, "read": False})

    # ---------- CLIENTE ----------
    if role == 'cliente':
        if request.method == 'POST':
            tema = request.form['tema'].strip()
            desc = request.form['descripcion'].strip()
            tickets.insert_one({
                "cliente": usr,
                "tema": tema,
                "descripcion": desc,
                "status": "abierto",
                "priority": "media",
                "asignado_a": None,
                "history": [{"actor": usr, "action": "creó ticket", "at": datetime.utcnow()}]
            })
            add_notification(usr, f"Tu ticket “{tema}” ha sido creado.")
            flash("Ticket creado.", "success")
            return redirect(url_for('dashboard'))

        my = list(tickets.find({"cliente": usr}))
        return render_template('dashboard_cliente.html',
                               first_name=fn, last_name=ln,
                               tickets=my, notif_count=notif_count)

    # ---------- SOPORTE ----------
    if role == 'soporte' and request.method == 'POST':
        tid      = request.form.get('ticket_id')
        action   = request.form.get('action')  # 'asignar' o 'resolver'
        prio     = request.form.get('priority')
        solution = (request.form.get('solution') or "").strip()

        if not tid:
            flash("Falta el ID del ticket.", "error")
            return redirect(url_for('dashboard'))

        t = tickets.find_one({"_id": ObjectId(tid)})
        if not t:
            flash("El ticket no existe.", "error")
            return redirect(url_for('dashboard'))

        if action == 'resolver':
            tickets.update_one(
                {"_id": ObjectId(tid)},
                {"$set": {"status": "resuelto"},
                 "$push": {"history": {
                     "actor": usr,
                     "action": "resolvió ticket",
                     "solution": solution if solution else None,
                     "at": datetime.utcnow()
                 }}}
            )
            notif_msg = f"Tu ticket “{t['tema']}” ha sido resuelto."
            if solution:
                notif_msg += f" Solución: {solution}"
            add_notification(t['cliente'], notif_msg)
            flash("Ticket marcado como resuelto.", "success")
            return redirect(url_for('dashboard'))

        # Asignarme
        tickets.update_one(
            {"_id": ObjectId(tid)},
            {"$set": {
                "status": "en progreso",
                "asignado_a": usr,
                "priority": prio or t.get("priority", "media")
            },
             "$push": {"history": {
                 "actor": usr,
                 "action": "asignó ticket",
                 "at": datetime.utcnow()
             }}}
        )
        add_notification(t['cliente'], f"Tu ticket “{t['tema']}” ha sido asignado a soporte.")
        flash("Ticket asignado.", "success")
        return redirect(url_for('dashboard'))

    if role == 'soporte':
        op  = list(tickets.find({"status":"abierto"}))
        ass = list(tickets.find({"asignado_a": usr, "status": {"$ne":"resuelto"}}))
        return render_template('dashboard_soporte.html',
                               first_name=fn, last_name=ln,
                               open_tickets=op, assigned=ass,
                               notif_count=notif_count)

    # ---------- SUPERADMIN ----------
    if role == 'superadmin' and request.method == 'POST':
        if 'ticket_id' in request.form and 'action' in request.form:
            tid = request.form['ticket_id']
            action = request.form['action']
            t = tickets.find_one({"_id": ObjectId(tid)})
            if action == 'asignar':
                agent = request.form.get('agent')
                prio = request.form.get('priority')
                tickets.update_one(
                    {"_id": ObjectId(tid)},
                    {"$set":{
                        "asignado_a": agent,
                        "status": "en progreso",
                        "priority": prio or "media"
                    },
                     "$push":{"history":{
                         "actor":usr,
                         "action":f"asignó a {agent}",
                         "at":datetime.utcnow()
                     }}} )
                add_notification(t['cliente'], f"Tu ticket “{t['tema']}” fue asignado a {agent}.")
                flash("Ticket asignado.", "success")
            else:
                tickets.update_one(
                    {"_id": ObjectId(tid)},
                    {"$set":{"status":"resuelto"},
                     "$push":{"history":{
                         "actor":usr, "action":"resolvió ticket",
                         "at":datetime.utcnow()
                     }}} )
                add_notification(t['cliente'], f"Tu ticket “{t['tema']}” ha sido resuelto.")
                flash("Ticket resuelto.", "success")
            return redirect(url_for('dashboard'))

        if 'new_support_username' in request.form:
            nu = request.form['new_support_username'].strip()
            pw = request.form['new_support_password']
            if users.find_one({"username": nu}):
                flash("Usuario existe.", "error")
            else:
                users.insert_one({
                    "username": nu, "pass_hash": generate_password_hash(pw),
                    "role": "soporte", "first_name": "", "last_name": "",
                    "registered_at": datetime.utcnow(),
                    "date_of_birth": None, "gender": None
                })
                add_notification(session['user'], f"Técnico “{nu}” añadido.")
                flash("Técnico creado.", "success")
            return redirect(url_for('dashboard'))

    if role == 'superadmin':
        usrs = list(users.find())
        ags = [u['username'] for u in usrs if u['role']=="soporte"]
        allt = list(tickets.find())
        return render_template('dashboard_admin.html',
                               first_name=fn, last_name=ln,
                               users=usrs, agents=ags, tickets=allt,
                               notif_count=notif_count)

    # Cualquier otro rol desconocido
    flash("Rol no reconocido.", "error")
    return redirect(url_for('logout'))

# ---------------- Notificaciones -----------------
@app.route('/notifications')
def notifications_view():
    if 'user' not in session:
        return redirect(url_for('login'))
    usr = session['user']
    notifs = list(notifications.find({"user": usr}).sort("created_at", -1))
    notifications.update_many({"user": usr, "read": False}, {"$set": {"read": True}})
    return render_template('notifications.html', notifs=notifs,
                           first_name=session['first_name'],
                           last_name=session['last_name'],
                           notif_count=0)

# ---------------- Detalle ticket -----------------
@app.route('/ticket/<tid>')
def ticket_detail(tid):
    if 'user' not in session:
        return redirect(url_for('login'))
    t = tickets.find_one({"_id": ObjectId(tid)})
    if not t:
        return "Ticket no existe", 404
    usr = session['user']
    notif_count = notifications.count_documents({"user": usr, "read": False})
    return render_template('ticket_detail.html', ticket=t,
                           first_name=session.get('first_name',''),
                           last_name=session.get('last_name',''),
                           notif_count=notif_count)

# ---------------- Logout -------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------- Cache headers ------------------
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ---------------- Página del chat (opcional UI) --
@app.route('/experto')
def experto_page():
    # Usa templates/experto_chat.html si lo tienes, sino redirige al dashboard
    try:
        return render_template('experto_chat.html')
    except:
        return redirect(url_for('dashboard'))

# ---------------- Chat experto (API) -------------
@app.route('/chat-experto', methods=['POST'])
def chat_experto():
    """
    Body JSON:
    {
      "descripcion": "texto del usuario",
      "ticketId": "abc123",
      "tema": "Conexión lenta"   (opcional; útil si UI lo manda)
    }
    """
    if 'user' not in session:
        return jsonify({"respuesta": "Debes iniciar sesión."}), 401

    data = request.get_json(force=True, silent=True) or {}
    texto = normaliza_txt(data.get('descripcion',''))
    tid   = data.get('ticketId')
    tema_raw = data.get('tema','')

    # Contexto por usuario (en sesión)
    ctx = session.get('chat_ctx') or {}
    # Si llega ticketId/tema, reseteamos contexto
    if tid:
        ctx = {
            "ticket_id": tid,
            "step": 0,
            "closed": False
        }
        # guardamos el tema normalizado
        ctx["tema"] = tema_normalizado(tema_raw) if tema_raw else None

    # Validación ticket
    t = None
    if ctx.get("ticket_id"):
        try:
            t = tickets.find_one({"_id": ObjectId(ctx["ticket_id"])})
        except:
            t = None

    # Si el ticket ya está resuelto
    if t and t.get("status") == "resuelto":
        session['chat_ctx'] = {"closed": True}  # cerrar sesión de chat
        return jsonify({
            "respuesta": "Este ticket ya está resuelto ✅. Por favor, selecciona otro ticket para continuar.",
            "closed": True
        })

    # Saludos
    if any(sal in texto for sal in SALUDOS):
        nombre = first_name_of(session['user'])
        cabecera = f"Hola, {nombre} 👋. "
        if t:
            tema = ctx.get("tema") or tema_normalizado(t.get("tema","otro"))
            pasos = SUGERENCIAS.get(tema, SUGERENCIAS["otro"])
            msg = (f"Veamos tu ticket de *{t.get('tema','Ticket')}*. "
                   f"Pasos sugeridos: 1) {pasos[0]} 2) {pasos[1]} 3) {pasos[2]} 4) {pasos[3]}. "
                   "Si *no funcionó*, escríbeme: *no funcionó*. "
                   "Si *ya quedó*, dime: *solucionado*.")
            session['chat_ctx'] = ctx
            return jsonify({"respuesta": cabecera + msg})
        session['chat_ctx'] = ctx
        return jsonify({"respuesta": cabecera + "¿En qué puedo ayudarte?"})

    # Solucionado
    if any(x in texto for x in ["solucionado", "funciono", "funcionó", "ya quedo", "ya quedó", "listo"]):
        if t:
            tickets.update_one(
                {"_id": t["_id"]},
                {"$set": {"status": "resuelto"},
                 "$push": {"history": {
                     "actor": session['user'],
                     "action": "cerró ticket desde chat",
                     "solution": "Marcado como solucionado por el cliente",
                     "at": datetime.utcnow()
                 }}}
            )
            add_notification(t['cliente'] if t.get('cliente') else session['user'],
                             f"¡Excelente! Tu ticket “{t.get('tema','Ticket')}” fue cerrado como *resuelto*.")
        session['chat_ctx'] = {"closed": True}
        nombre = first_name_of(session['user'])
        return jsonify({"respuesta": f"¡Excelente, {nombre}! Me alegra que se haya solucionado. He cerrado tu ticket ✅.", "closed": True})

    # No funcionó -> siguiente paso o escalar
    if "no funciono" in texto or "no funciona" in texto or "sigue igual" in texto or "no sirv" in texto:
        if t:
            tema = ctx.get("tema") or tema_normalizado(t.get("tema","otro"))
            pasos = SUGERENCIAS.get(tema, SUGERENCIAS["otro"])
            idx = ctx.get("step", 0) + 1  # pasar al siguiente paso
            if idx < len(pasos):
                ctx["step"] = idx
                session['chat_ctx'] = ctx
                return jsonify({"respuesta": f"Intentemos esto: {pasos[idx]}.\nSi no funciona, escribe: *no funcionó*. "
                                             "Si queda listo, escribe: *solucionado*."})
            # si ya no hay más pasos -> escalar a técnico
            tickets.update_one(
                {"_id": t["_id"]},
                {"$set": {"status":"en progreso", "asignado_a": None},
                 "$push": {"history": {
                     "actor": "asistente_virtual",
                     "action": "escaló a técnico",
                     "at": datetime.utcnow()
                 }}}
            )
            add_notification(t['cliente'] if t.get('cliente') else session['user'],
                             "No tengo una solución inmediata. Escalaré tu caso a un técnico.")
            session['chat_ctx'] = {"closed": True}
            return jsonify({"respuesta": "No tengo una solución inmediata. Escalaré tu caso a un técnico. Te contactarán pronto 👨‍🔧.", "closed": True})

        # Si no hay ticket seleccionado
        return jsonify({"respuesta": "Para ayudarte mejor, selecciona un ticket primero."})

    # Si tenemos ticket y aún no se pidió nada, dar el 1er paso
    if t:
        tema = ctx.get("tema") or tema_normalizado(t.get("tema","otro"))
        pasos = SUGERENCIAS.get(tema, SUGERENCIAS["otro"])
        ctx["step"] = ctx.get("step", 0)
        session['chat_ctx'] = ctx
        return jsonify({"respuesta": f"Pasos sugeridos para *{t.get('tema','Ticket')}*:\n1) {pasos[0]}\n2) {pasos[1]}\n3) {pasos[2]}\n4) {pasos[3]}\n"
                                     "Si *no funcionó*, escribe: *no funcionó*. Si se resolvió, escribe: *solucionado*."})

    # Mensaje genérico si no hay nada más
    return jsonify({"respuesta": "¿Me cuentas qué problema tienes o seleccionas un ticket para ayudarte mejor?"})

# =====================  ADMIN: Resolver tickets (vista dedicada)  =====================
@app.route('/admin/resolver', methods=['GET', 'POST'])
def admin_resolver():
    if 'user' not in session or session.get('role') != 'superadmin':
        return redirect(url_for('login'))

    usr = session['user']
    notif_count = notifications.count_documents({"user": usr, "read": False})

    if request.method == 'POST':
        tid = request.form.get('ticket_id')
        action = request.form.get('action')      # 'resolver' / 'asignar'
        solution = (request.form.get('solution') or '').strip()
        prio = (request.form.get('priority') or 'media').strip()
        agent = (request.form.get('agent') or '').strip()

        if not tid:
            flash("Debes seleccionar un ticket.", "error")
            return redirect(url_for('admin_resolver'))

        t = tickets.find_one({"_id": ObjectId(tid)})
        if not t:
            flash("El ticket no existe.", "error")
            return redirect(url_for('admin_resolver'))

        if action == 'resolver':
            tickets.update_one(
                {"_id": t["_id"]},
                {"$set": {"status": "resuelto"},
                 "$push": {"history": {
                     "actor": usr,
                     "action": "resolvió ticket (admin)",
                     "solution": solution if solution else None,
                     "at": datetime.utcnow()
                 }}}
            )
            msg = f"Tu ticket “{t['tema']}” ha sido marcado como *resuelto* por el administrador."
            if solution:
                msg += f" Solución: {solution}"
            add_notification(t['cliente'], msg)
            flash("Ticket resuelto.", "success")
            return redirect(url_for('admin_resolver'))

        if action == 'asignar':
            tickets.update_one(
                {"_id": t["_id"]},
                {"$set": {"asignado_a": agent or None, "priority": prio, "status": "en progreso"},
                 "$push": {"history": {
                     "actor": usr,
                     "action": f"asignó a {agent or '—'}",
                     "at": datetime.utcnow()
                 }}}
            )
            add_notification(t['cliente'], f"Tu ticket “{t['tema']}” fue asignado a {agent}.")
            flash("Ticket asignado.", "success")
            return redirect(url_for('admin_resolver'))

    # listar pendientes (no resueltos)
    pend = list(tickets.find({"status": {"$ne": "resuelto"}}).sort("_id", -1))
    ags = [u['username'] for u in users.find({"role": "soporte"})]

    return render_template(
        'admin_resolver.html',
        first_name=session.get('first_name',''),
        last_name=session.get('last_name',''),
        notif_count=notif_count,
        tickets=pend,
        agents=ags
    )
# =====================  FIN ADMIN: Resolver tickets  =====================

# -------------------------------------------------
# Main
# -------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
