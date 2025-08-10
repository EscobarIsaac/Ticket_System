from flask import Blueprint
from controllers import experto_controller

experto_bp = Blueprint('experto', __name__)

@experto_bp.route("/chat-experto", methods=["GET", "POST"])
def chat():
    return experto_controller.chat_experto()
