from flask import Blueprint, render_template, session, redirect, url_for
from services.db_service import notifications

notification_bp = Blueprint("notifications", __name__)

@notification_bp.route("/notifications")
def notifications_view():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    usr = session["user"]
    notifs = list(notifications.find({"user": usr}).sort("created_at", -1))
    notifications.update_many({"user": usr, "read": False}, {"$set": {"read": True}})
    return render_template(
        "notifications.html",
        notifs=notifs,
        first_name=session["first_name"],
        last_name=session["last_name"]
    )
