from flask import Blueprint, render_template, session, redirect, url_for
from bson.objectid import ObjectId
from services.db_service import tickets

ticket_bp = Blueprint("ticket", __name__)

@ticket_bp.route("/ticket/<tid>")
def ticket_detail(tid):
    if "user" not in session:
        return redirect(url_for("auth.login"))
    t = tickets.find_one({"_id": ObjectId(tid)})
    if not t:
        return "Ticket no existe", 404
    return render_template(
        "ticket_detail.html",
        ticket=t,
        first_name=session["first_name"],
        last_name=session["last_name"]
    )
