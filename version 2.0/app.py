from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import certifi, re

app = Flask(__name__)
app.secret_key = 'cambialo_por_una_clave_segura'

# MongoDB Atlas
MONGO_URI = "mongodb+srv://isaac:isaac1@cluster0.uu8wq4u.mongodb.net/ticketdb?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client['ticketdb']
users = db['users']
tickets = db['tickets']

# RegEx para nombre/apellido
NAME_REGEX = re.compile(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,50}$')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first     = request.form['first_name'].strip()
        last      = request.form['last_name'].strip()
        username  = request.form['username'].strip()
        password  = request.form['password']
        dob_str   = request.form['date_of_birth']
        gender    = request.form['gender']
        role      = 'cliente'

        if not NAME_REGEX.match(first):
            flash("Nombre inválido: sólo letras y espacios (2–50).", "error")
            return redirect(url_for('register'))
        if not NAME_REGEX.match(last):
            flash("Apellido inválido: sólo letras y espacios (2–50).", "error")
            return redirect(url_for('register'))
        if users.find_one({"username": username}):
            flash("Usuario ya existe", "error")
            return redirect(url_for('register'))

        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
        except ValueError:
            flash("Fecha de nacimiento inválida", "error")
            return redirect(url_for('register'))

        today = datetime.utcnow()
        age_limit = today - timedelta(days=18*365 + 4)
        if dob > age_limit:
            flash("Debes tener al menos 18 años para registrarte.", "error")
            return redirect(url_for('register'))

        users.insert_one({
            "first_name": first,
            "last_name": last,
            "username": username,
            "pass_hash": generate_password_hash(password),
            "role": role,
            "registered_at": today,
            "date_of_birth": dob,
            "gender": gender
        })
        flash("Registro exitoso, ya puedes iniciar sesión", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        usr = users.find_one({"username": u})
        if usr and check_password_hash(usr['pass_hash'], p):
            session['user']       = usr['username']
            session['role']       = usr['role']
            session['first_name'] = usr.get('first_name','')
            session['last_name']  = usr.get('last_name','')
            return redirect(url_for('dashboard'))
        error = "Credenciales inválidas"
    return render_template('login.html', error=error)


@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    role = session['role']
    usr  = session['user']
    fn   = session['first_name']
    ln   = session['last_name']

    # Cliente crea ticket (prioridad media por defecto)
    if role=='cliente' and request.method=='POST':
        tickets.insert_one({
            "cliente": usr,
            "tema": request.form['tema'],
            "descripcion": request.form['descripcion'],
            "status": "abierto",
            "priority": "media",
            "history": [{"actor":usr,"action":"creó ticket","at":datetime.utcnow()}]
        })
        flash("Ticket creado correctamente.", "success")
        return redirect(url_for('dashboard'))

    # Soporte asigna ticket (elige prioridad)
    if role=='soporte' and request.method=='POST':
        tid  = request.form.get('ticket_id')
        prio = request.form.get('priority')
        if tid:
            tickets.update_one(
                {"_id":ObjectId(tid),"status":"abierto"},
                {"$set":{
                    "status":"en progreso",
                    "asignado_a":usr,
                    "priority": prio or "media"
                },
                 "$push":{"history":{"actor":usr,"action":"asignó ticket","at":datetime.utcnow()}}}
            )
            flash("Ticket asignado correctamente.", "success")
        return redirect(url_for('dashboard'))

    # Superadmin asigna/resuelve y crea técnicos
    if role=='superadmin' and request.method=='POST':
        if 'ticket_id' in request.form and 'action' in request.form:
            tid    = request.form['ticket_id']
            action = request.form['action']
            if action=='asignar':
                agent = request.form.get('agent')
                prio  = request.form.get('priority')
                if not agent:
                    flash("Debes seleccionar un agente.", "error")
                else:
                    tickets.update_one(
                        {"_id":ObjectId(tid)},
                        {"$set":{
                            "asignado_a":agent,
                            "status":"en progreso",
                            "priority": prio or "media"
                        },
                         "$push":{"history":{"actor":usr,"action":f"asignó a {agent}","at":datetime.utcnow()}}}
                    )
                    flash(f"Ticket asignado a {agent}.", "success")
            elif action=='resolver':
                tickets.update_one(
                    {"_id":ObjectId(tid)},
                    {"$set":{"status":"resuelto"},
                     "$push":{"history":{"actor":usr,"action":"resolvió ticket","at":datetime.utcnow()}}}
                )
                flash("Ticket marcado como resuelto.", "success")
            return redirect(url_for('dashboard'))

        if 'new_support_username' in request.form:
            new_user = request.form['new_support_username'].strip()
            new_pwd  = request.form['new_support_password']
            if users.find_one({"username":new_user}):
                flash("El usuario ya existe.", "error")
            else:
                users.insert_one({
                    "first_name":"","last_name":"",
                    "username":new_user,
                    "pass_hash":generate_password_hash(new_pwd),
                    "role":"soporte",
                    "registered_at":datetime.utcnow(),
                    "date_of_birth":None,
                    "gender":None
                })
                flash(f"Técnico «{new_user}» creado.", "success")
            return redirect(url_for('dashboard'))

    # Render por rol
    if role=='cliente':
        my = list(tickets.find({"cliente":usr}))
        return render_template('dashboard_cliente.html',
                               first_name=fn, last_name=ln, tickets=my)

    if role=='soporte':
        op  = list(tickets.find({"status":"abierto"}))
        ass = list(tickets.find({"asignado_a":usr}))
        return render_template('dashboard_soporte.html',
                               first_name=fn, last_name=ln,
                               open_tickets=op, assigned=ass)

    # superadmin
    usrs = list(users.find())
    ags  = [u['username'] for u in usrs if u['role']=='soporte']
    allt = list(tickets.find())
    return render_template('dashboard_admin.html',
                           first_name=fn, last_name=ln,
                           users=usrs, agents=ags, tickets=allt)


@app.route('/ticket/<tid>')
def ticket_detail(tid):
    if 'user' not in session:
        return redirect(url_for('login'))
    tkt = tickets.find_one({"_id":ObjectId(tid)})
    if not tkt:
        return "Ticket no existe",404
    return render_template('ticket_detail.html',ticket=tkt)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.after_request
def add_header(response):
    response.headers["Cache-Control"]="no-store, no-cache, must-revalidate, private, max-age=0"
    response.headers["Pragma"]="no-cache"
    response.headers["Expires"]="0"
    return response


if __name__=='__main__':
    app.run(debug=True)
