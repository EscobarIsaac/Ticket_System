from datetime import datetime
from services.db_service import notifications

def add_notification(username, message):
    notifications.insert_one({
        "user": username,
        "message": message,
        "read": False,
        "created_at": datetime.utcnow()
    })
