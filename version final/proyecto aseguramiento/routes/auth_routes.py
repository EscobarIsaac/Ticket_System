from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import re
from services.db_service import users
from services.notificacion_service import add_notification

auth_bp = Blueprint("auth", __name__)
NAME_REGEX = re.compile(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,50}$')

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        usr = users.find_one({"username": u})
        if usr and check_password_hash(usr["pass_hash"], p):
            session["user"] = u
            session["role"] = usr["role"]
            session["first_name"] = usr.get("first_name", "")
            session["last_name"] = usr.get("last_name", "")
            flash("Has iniciado sesión.", "success")
            add_notification(u, "Iniciaste sesión correctamente.")
            return redirect(url_for("dashboard.dashboard"))
        error = "Credenciales inválidas"
    return render_template("login.html", error=error)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first = request.form["first_name"].strip()
        last = request.form["last_name"].strip()
        username = request.form["username"].strip()
        password = request.form["password"]
        dob_str = request.form["date_of_birth"]
        gender = request.form["gender"]
        role = "cliente"

        if not NAME_REGEX.match(first) or not NAME_REGEX.match(last):
            flash("Nombre o apellido inválido.", "error")
            return redirect(url_for("auth.register"))
        if users.find_one({"username": username}):
            flash("Usuario ya existe", "error")
            return redirect(url_for("auth.register"))

        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
        except ValueError:
            flash("Fecha inválida", "error")
            return redirect(url_for("auth.register"))

        if dob > datetime.utcnow() - timedelta(days=18*365+4):
            flash("Debes tener al menos 18 años.", "error")
            return redirect(url_for("auth.register"))

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
        return redirect(url_for("auth.login"))

    return render_template("register.html")
