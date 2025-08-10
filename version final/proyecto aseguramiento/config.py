import os
from dotenv import load_dotenv
import certifi

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET', 'clave_segura_por_defecto')
    MONGO_URI = os.environ.get(
        "MONGO_URI",
        "mongodb+srv://isaac:isaac1@cluster0.uu8wq4u.mongodb.net/ticketdb?retryWrites=true&w=majority"
    )
    TLS_CA_FILE = certifi.where()
