from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from bson.objectid import ObjectId
from services.db_service import tickets, users
from services.notificacion_service import add_notification

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    usr = session["user"]
    role = session["role"]
    fn = session["first_name"]
    ln = session["last_name"]
    notif_count = tickets.database.notifications.count_documents({"user": usr, "read": False})

    # Cliente crea ticket
    if role == "cliente" and request.method == "POST":
        tema = request.form["tema"]
        desc = request.form["descripcion"]
        tickets.insert_one({
            "cliente": usr,
            "tema": tema,
            "descripcion": desc,
            "status": "abierto",
            "priority": "media",
            "history": [{"actor": usr, "action": "creó ticket", "at": tickets.database.datetime.utcnow()}]
        })
        flash("Ticket creado.", "success")
        add_notification(usr, f"Tu ticket “{tema}” ha sido creado.")
        return redirect(url_for("dashboard.dashboard"))

    # Soporte asigna ticket
    if role == "soporte" and request.method == "POST":
        tid = request.form.get("ticket_id")
        prio = request.form.get("priority")
        if tid:
            t = tickets.find_one({"_id": ObjectId(tid)})
            tickets.update_one(
                {"_id": ObjectId(tid)},
                {"$set": {
                    "status": "en progreso",
                    "asignado_a": usr,
                    "priority": prio or "media"
                },
                 "$push": {"history": {"actor": usr, "action": "asignó ticket", "at": tickets.database.datetime.utcnow()}}}
            )
            flash("Ticket asignado.", "success")
            add_notification(t["cliente"], f"Tu ticket “{t['tema']}” ha sido asignado.")
        return redirect(url_for("dashboard.dashboard"))

    # Superadmin asigna/resuelve tickets y crea técnicos
    if role == "superadmin" and request.method == "POST":
        if "ticket_id" in request.form and "action" in request.form:
            tid = request.form["ticket_id"]
            action = request.form["action"]
            t = tickets.find_one({"_id": ObjectId(tid)})
            if action == "asignar":
                agent = request.form.get("agent")
                prio = request.form.get("priority")
                tickets.update_one(
                    {"_id": ObjectId(tid)},
                    {"$set": {
                        "asignado_a": agent,
                        "status": "en progreso",
                        "priority": prio or "media"
                    },
                     "$push": {"history": {"actor": usr, "action": f"asignó a {agent}", "at": tickets.database.datetime.utcnow()}}}
                )
                flash("Ticket asignado.", "success")
                add_notification(t["cliente"], f"Tu ticket “{t['tema']}” fue asignado a {agent}.")
            else:
                tickets.update_one(
                    {"_id": ObjectId(tid)},
                    {"$set": {"status": "resuelto"},
                     "$push": {"history": {"actor": usr, "action": "resolvió ticket", "at": tickets.database.datetime.utcnow()}}}
                )
                flash("Ticket resuelto.", "success")
                add_notification(t["cliente"], f"Tu ticket “{t['tema']}” ha sido resuelto.")
            return redirect(url_for("dashboard.dashboard"))

        if "new_support_username" in request.form:
            nu = request.form["new_support_username"].strip()
            pw = request.form["new_support_password"]
            if users.find_one({"username": nu}):
                flash("Usuario existe.", "error")
            else:
                users.insert_one({
                    "username": nu,
                    "pass_hash": tickets.database.generate_password_hash(pw),
                    "role": "soporte",
                    "first_name": "", "last_name": "",
                    "registered_at": tickets.database.datetime.utcnow(),
                    "date_of_birth": None, "gender": None
                })
                flash("Técnico creado.", "success")
                add_notification(usr, f"Técnico “{nu}” añadido.")
            return redirect(url_for("dashboard.dashboard"))

    # Render según rol
    if role == "cliente":
        my = list(tickets.find({"cliente": usr}))
        return render_template("dashboard_cliente.html",
                               first_name=fn, last_name=ln,
                               tickets=my, notif_count=notif_count)

    if role == "soporte":
        op = list(tickets.find({"status": "abierto"}))
        ass = list(tickets.find({"asignado_a": usr}))
        return render_template("dashboard_soporte.html",
                               first_name=fn, last_name=ln,
                               open_tickets=op, assigned=ass,
                               notif_count=notif_count)

    usrs = list(users.find())
    ags = [u["username"] for u in usrs if u["role"] == "soporte"]
    allt = list(tickets.find())
    return render_template("dashboard_admin.html",
                           first_name=fn, last_name=ln,
                           users=usrs, agents=ags, tickets=allt,
                           notif_count=notif_count)
