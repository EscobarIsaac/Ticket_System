from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import certifi, re
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'clave_segura_por_defecto')

# Conexión MongoDB
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://isaac:isaac1@cluster0.uu8wq4u.mongodb.net/ticketdb?retryWrites=true&w=majority"
)
client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client['ticketdb']
users = db['users']
tickets = db['tickets']
notifications = db['notifications']

# Validación de nombre
NAME_REGEX = re.compile(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,50}$')

# Ruta raíz
@app.route('/')
def index():
    return redirect(url_for('login'))

# Función para agregar notificaciones
def add_notification(username, message):
    notifications.insert_one({
        "user": username,
        "message": message,
        "read": False,
        "created_at": datetime.utcnow()
    })

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
            flash("Nombre inválido.", "error")
            return redirect(url_for('register'))
        if not NAME_REGEX.match(last):
            flash("Apellido inválido.", "error")
            return redirect(url_for('register'))
        if users.find_one({"username": username}):
            flash("Usuario ya existe", "error")
            return redirect(url_for('register'))

        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
        except ValueError:
            flash("Fecha de nacimiento inválida", "error")
            return redirect(url_for('register'))

        if dob > datetime.utcnow() - timedelta(days=18*365+4):
            flash("Debes tener al menos 18 años.", "error")
            return redirect(url_for('register'))

        users.insert_one({
            "first_name": first,
            "last_name": last,
            "username": username,
            "pass_hash": generate_password_hash(password),
            "role": role,
            "registered_at": datetime.utcnow(),
            "date_of_birth": dob,
            "gender": gender
        })
        flash("Registro exitoso.", "success")
        add_notification(username, "Bienvenido al sistema de tickets.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        usr = users.find_one({"username": u})
        if usr and check_password_hash(usr['pass_hash'], p):
            session['user'] = u
            session['role'] = usr['role']
            session['first_name'] = usr.get('first_name','')
            session['last_name'] = usr.get('last_name','')
            flash("Has iniciado sesión.", "success")
            add_notification(u, "Iniciaste sesión correctamente.")
            return redirect(url_for('dashboard'))
        error = "Credenciales inválidas"
    return render_template('login.html', error=error)

@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    usr = session['user']
    role = session['role']
    fn = session['first_name']
    ln = session['last_name']
    notif_count = notifications.count_documents({"user": usr, "read": False})

    if role == 'cliente' and request.method == 'POST':
        tema = request.form['tema']
        desc = request.form['descripcion']
        tickets.insert_one({
            "cliente": usr,
            "tema": tema,
            "descripcion": desc,
            "status": "abierto",
            "priority": "media",
            "history": [{"actor": usr, "action": "creó ticket", "at": datetime.utcnow()}]
        })
        flash("Ticket creado.", "success")
        add_notification(usr, f"Tu ticket “{tema}” ha sido creado.")
        return redirect(url_for('dashboard'))

    if role == 'soporte' and request.method == 'POST':
        tid = request.form.get('ticket_id')
        prio = request.form.get('priority')
        if tid:
            t = tickets.find_one({"_id": ObjectId(tid)})
            tickets.update_one(
                {"_id": ObjectId(tid)},
                {"$set":{
                    "status":"en progreso",
                    "asignado_a": usr,
                    "priority": prio or "media"
                },
                 "$push":{"history":{"actor":usr,"action":"asignó ticket","at":datetime.utcnow()}}}
            )
            flash("Ticket asignado.", "success")
            add_notification(t['cliente'], f"Tu ticket “{t['tema']}” ha sido asignado.")
        return redirect(url_for('dashboard'))

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
                     "$push":{"history":{"actor":usr,"action":f"asignó a {agent}","at":datetime.utcnow()}}}
                )
                flash("Ticket asignado.", "success")
                add_notification(t['cliente'], f"Tu ticket “{t['tema']}” fue asignado a {agent}.")
            else:
                tickets.update_one(
                    {"_id": ObjectId(tid)},
                    {"$set":{"status":"resuelto"},
                     "$push":{"history":{"actor":usr,"action":"resolvió ticket","at":datetime.utcnow()}}}
                )
                flash("Ticket resuelto.", "success")
                add_notification(t['cliente'], f"Tu ticket “{t['tema']}” ha sido resuelto.")
            return redirect(url_for('dashboard'))
        if 'new_support_username' in request.form:
            nu = request.form['new_support_username'].strip()
            pw = request.form['new_support_password']
            if users.find_one({"username": nu}):
                flash("Usuario existe.", "error")
            else:
                users.insert_one({
                    "username": nu,
                    "pass_hash": generate_password_hash(pw),
                    "role": "soporte",
                    "first_name": "", "last_name": "",
                    "registered_at": datetime.utcnow(),
                    "date_of_birth": None, "gender": None
                })
                flash("Técnico creado.", "success")
                add_notification(usr, f"Técnico “{nu}” añadido.")
            return redirect(url_for('dashboard'))

    if role == 'cliente':
        my = list(tickets.find({"cliente": usr}))
        return render_template('dashboard_cliente.html',
                               first_name=fn, last_name=ln,
                               tickets=my, notif_count=notif_count)
    if role == 'soporte':
        op = list(tickets.find({"status":"abierto"}))
        ass = list(tickets.find({"asignado_a": usr}))
        return render_template('dashboard_soporte.html',
                               first_name=fn, last_name=ln,
                               open_tickets=op, assigned=ass,
                               notif_count=notif_count)
    usrs = list(users.find())
    ags = [u['username'] for u in usrs if u['role']=="soporte"]
    allt = list(tickets.find())
    return render_template('dashboard_admin.html',
                           first_name=fn, last_name=ln,
                           users=usrs, agents=ags, tickets=allt,
                           notif_count=notif_count)

@app.route('/notifications')
def notifications_view():
    if 'user' not in session:
        return redirect(url_for('login'))
    usr = session['user']
    notifs = list(notifications.find({"user": usr}).sort("created_at", -1))
    notifications.update_many({"user": usr, "read": False}, {"$set": {"read": True}})
    return render_template('notifications.html', notifs=notifs,
                           first_name=session['first_name'],
                           last_name=session['last_name'])

@app.route('/ticket/<tid>')
def ticket_detail(tid):
    if 'user' not in session:
        return redirect(url_for('login'))
    t = tickets.find_one({"_id": ObjectId(tid)})
    if not t:
        return "Ticket no existe", 404
    return render_template('ticket_detail.html', ticket=t,
                           first_name=session['first_name'],
                           last_name=session['last_name'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    app.run(debug=True)
